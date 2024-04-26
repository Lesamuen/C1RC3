"""Contains all SQLAlchemy ORM models"""

print("Loading module 'dbmodels'...")

from json import dumps, loads
from random import sample

from discord import User
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from bot import SQLBase, bot_client
from auxiliary import InvalidArgumentError, clamp


class ChipAccount(SQLBase):
    """Represents a chips account belonging to a single character.

    ### Attributes
    [PRIMARY] name: str
        Unique name that the account is under
    owner_id: int
        ID of User who owns this account
    chips: str
        Jsonified array of chips of each type within the account
        
    ### Methods
    [STATIC] create_account(session: sqlalchemy.orm.Session, name: str) -> bool
        Attempt to open a chip account under the given name
    [STATIC] find_account(session: sqlalchemy.orm.Session, username: str) -> ChipAccount | None
        Returns the ChipAccount if it exists
    get_bal() -> list[int]
        Returns the balance unjsonified
    deposit(session: sqlalchemy.orm.Session, amount: list[int]) -> None
        Deposit an amount of chips into the account
    withdraw(session: sqlalchemy.orm.Session, amount: list[int]) -> bool
        Withdraw an amount of chips from the account
    change_name(session: sqlalchemy.orm.Session, new: str) -> None
        Change the name of the account
    """

    __tablename__ = "account"

    name: Mapped[str] = mapped_column(primary_key = True)
    """Unique name that the account is under"""

    owner_id: Mapped[int]
    """ID of User who owns this account"""
    
    chips: Mapped[str] = mapped_column(default = "[0, 0, 0, 0, 0, 0]")
    """Jsonified array of chips of each type within the account"""

    @staticmethod
    def create_account(session: Session, id: int, name: str) -> bool:
        """Attempt to open a chip account under the given name

        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        id: int
            ID of Discord user
        name: str
            In-character name that the account is going under

        ### Returns
        True
            Successfully created account
        False
            Account already existed
        """

        found_account = session.get(ChipAccount, name)
        
        if found_account is None:
            # Create new account
            new_account = ChipAccount(owner_id = id, name = name)
            session.add(new_account)
            session.commit()
            return True
        else:
            return False
        
    @staticmethod
    def find_account(session: Session, name: str) -> "ChipAccount | None":
        """Returns the ChipAccount if it exists
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        name: str
            Name of account to search for

        ### Returns
        ChipAccount with matching username or None if not found.
        """

        return session.get(ChipAccount, name)
    
    def get_bal(self) -> list[int]:
        """Returns the balance unjsonified
        
        ### Returns
        A list of integers containing each type of chip in the account
        """

        return loads(self.chips)

    def deposit(self, session: Session, amount: list[int]) -> None:
        """Deposit an amount of chips into the account

        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        amount: list[int]
            Amount of each type of chips to add to the balance

        ### Raises
        InvalidArgumentError
            Amount given is negative or not enough chip arguments
        """

        for chips in amount:
            if chips < 0:
                raise InvalidArgumentError
        
        current_chips: list[int] = loads(self.chips)
        if len(amount) != len(current_chips):
            raise InvalidArgumentError
        
        for i in range(len(amount)):
            current_chips[i] += amount[i]

        self.chips = dumps(current_chips)
        session.commit()
    
    def withdraw(self, session: Session, amount: list[int]) -> bool:
        """Withdraw an amount of chips from the account

        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        amount: list[int]
            Amount of each type of chips to remove from the balance

        ### Returns
        True
            Successful withdraw
        False
            Any amount of chips was more than balance

        ### Raises
        InvalidArgumentError
            Amount given is negative or not enough chip arguments
        """

        for chips in amount:
            if chips < 0:
                raise InvalidArgumentError
        
        current_chips: list[int] = loads(self.chips)
        if len(amount) != len(current_chips):
            raise InvalidArgumentError
        
        for i in range(len(amount)):
            if amount[i] > current_chips[i]:
                return False
            current_chips[i] -= amount[i]

        self.chips = dumps(current_chips)
        session.commit()

        return True

    def change_name(self, session: Session, new: str) -> None:
        """Change the name of the account

        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        new: str
            The new name to attach the account to

        ### Raises
        InvalidArgumentError
            New name is empty string
        """

        if new == "":
            raise InvalidArgumentError

        self.name = new
        session.commit()


class Player(SQLBase):
    """Represents a User's participation within a Game.
    
    ### Attributes
    [PRIMARY] user_id: int
        User ID of the player
    [PRIMARY, FOREIGN] game_id: int
        ID of the Game the Player is playing in
    [BACKREF] game: Game
        Direct reference to corresponding Game
    [POLYMORPHIC] type: str
        The type of game this Player belongs to
    name: str
        What name the Player shall be referred to as
    chips: str
        Jsonified array of chips of each type the Player holds
    used: str
        Jsonified array of chips of each type the Player has used this game
    bet: str
        How many chips the Player is currently willing to bet

    ### Methods
    leave(session: sqlalchemy.orm.Session) -> None
        Remove Player from Game, i.e. delete Player from database
    user() -> discord.User
        Get associated Discord user
    mention() -> str
        Get Discord mention string of associated Discord user
    get_index() -> int
        Get index of player in corresponding game's player list
    rename(session: sqlalchemy.orm.Session, new_name: str) -> None
        Change the name of the player
    set_bet(session: sqlalchemy.orm.Session, bet: list[int]) -> None
        Set the Player's bet
    get_chips() -> list[int]
        Return the Player's current amount of chips unjsonified
    set_chips(session: sqlalchemy.orm.Session, amount: list[int]) -> None
        Set the Player's chips directly
    get_used() -> list[int]
        Return the Player's used amount of chips unjsonified
    set_used(session: sqlalchemy.orm.Session, amount: list[int]) -> None
        Set the Player's used chips directly
    pay_chips(session: sqlalchemy.orm.Session, amount: list[int]) -> None
        Add an amount of chips to the Player's current amount of chips
    use_chips(session: sqlalchemy.orm.Session, amount: list[int], track: bool = True) -> bool
        Removes a player's chips, if able, and tracks used chips
    """

    __tablename__ = "player"
    __mapper_args__ = {
        "polymorphic_identity": "base",
        "polymorphic_on": "type"
        }

    user_id: Mapped[int] = mapped_column(primary_key = True)
    """User ID of the player"""

    game_id: Mapped[int] = mapped_column(ForeignKey("game.id", ondelete = "CASCADE"), primary_key = True)
    """ID of the Game the Player is playing in"""

    game: Mapped["Game"] = relationship(back_populates = "players")
    """Direct reference to corresponding Game"""

    type: Mapped[str]
    """The type of game this Player belongs to"""

    name: Mapped[str]
    """What name the Player shall be referred to as"""

    chips: Mapped[str] = mapped_column(default = "[0, 0, 0, 0, 0, 0]")
    """Jsonified array of chips of each type the Player holds"""

    used: Mapped[str] = mapped_column(default = "[0, 0, 0, 0, 0, 0]")
    """Jsonified array of chips of each type the Player has used this game"""

    bet: Mapped[str] = mapped_column(default = "[0, 0, 0, 0, 0, 0]")
    """How many chips the Player is currently willing to bet"""
    
    def leave(self, session: Session) -> None:
        """Remove Player from Game, i.e. delete Player from database

        Also handle bet turn updates as a result of leaving
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        """

        if self.get_index() < self.game.bet_turn:
            self.game.bet_turn -= 1
        if len(self.game.players) > 1:
            self.game.bet_turn %= (len(self.game.players) - 1)

        session.delete(self)
        session.commit()

    def user(self) -> User:
        """Get associated Discord user
        
        ### Returns
        discord.User
            Reference to the Discord user
        """

        return bot_client.get_user(self.user_id)
    
    def mention(self) -> str:
        """Get Discord mention string of associated Discord user
        
        ### Returns
        str
            The mention string for the Discord user
        """

        return bot_client.get_user(self.user_id).mention

    def get_index(self) -> int:
        """Get index of player in corresponding game's player list
        
        ### Returns
        int
            The index of the player
        """

        for i in range(len(self.game.players)):
            if self.game.players[i] == self:
                return i

    def rename(self, session: Session, new_name: str) -> None:
        """Change the name of the player
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        new_name: str
            The name to change the Player's name to
        """

        self.name = new_name
        session.commit()

    def set_bet(self, session: Session, bet: list[int]) -> None:
        """Set the Player's bet
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        bet: list[int]
            The bet to set the Player's bet to
        """

        self.bet = dumps(bet)
        session.commit()

    def get_chips(self) -> list[int]:
        """Return the Player's current amount of chips unjsonified
        
        ### Returns
        List of integers corresponding to types of chips
        """

        return loads(self.chips)
    
    def set_chips(self, session: Session, amount: list[int]) -> None:
        """Set the Player's chips directly
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        amount: list[int]
            The list of chips to set the Player's chips to
        """

        self.chips = dumps(amount)
        session.commit()

    def get_used(self) -> list[int]:
        """Return the Player's used amount of chips unjsonified
        
        ### Returns
        List of integers corresponding to types of chips
        """

        return loads(self.used)
    
    def set_used(self, session: Session, amount: list[int]) -> None:
        """Set the Player's used chips directly
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        amount: list[int]
            The list of chips to set the Player's used chips to
        """

        self.used = dumps(amount)
        session.commit()

    def pay_chips(self, session: Session, amount: list[int]) -> None:
        """Add an amount of chips to the Player's current amount of chips
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        amount: list[int]
            The list of chips to add to the Player's chips
        """

        bal = loads(self.chips)
        for i in range(len(bal)):
            bal[i] += amount[i]
        self.chips = dumps(bal)

        session.commit()

    def use_chips(self, session: Session, amount: list[int], track: bool = True) -> bool:
        """Removes a player's chips, if able, and tracks used chips
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        amount: list[int]
            The list of chips to try to remove from the Player's chips
        track: bool = True
            Whether to track the chips removed here or not

        ### Returns
        True
            Chips successfully removed
        False
            Less current chips than was requested to be removed
        """

        bal = loads(self.chips)
        # Check if enough chips
        for i in range(len(bal)):
            if bal[i] < amount[i]:
                return False

        for i in range(len(bal)):
            bal[i] -= amount[i]

        if track:
            used = loads(self.used)
            for i in range(len(bal)):
                used[i] += amount[i]
            self.used = dumps(used)

        self.chips = dumps(bal)
        session.commit()
        return True


class Game(SQLBase):
    """Represents a currently running game for a channel/thread.
    
    ### Attributes
    [PRIMARY] id: int
        Corresponds to the discord channel/thread ID
    [POLYMORPHIC] type: str
        The type of game
    [BACKREF] players: list[Player]
        Ref to list of players within this game
    [CLASS] player_class
        Player subclass that corresponds to this Game subclass
    [CLASS] max_players: int
        Max amount of players the game of this type can handle; 0 means infinite
    [CLASS] bet_cap: list[int]
        The maximum amount of chips that can be bet in a Game
    stake: int
        0 - low stakes, 1 - normal stakes, 2 - high stakes
    bet_turn: int
        Player index whose turn it is to bet
    current_bet: str
        The current bet for the round within the game
    started: bool
        Whether or not the game's first round has begun

    ### Methods
    [CLASS] create_game(session: sqlalchemy.orm.Session, channel_id: int) -> None
        Create a game if there isn't one in the channel already
    [CLASS] find_game(session: sqlalchemy.orm.Session, channel: int) -> Game | None
        Return object of Game subclass for a channel, if any
    join_game(session: sqlalchemy.orm.Session, user: int, name: str) -> Player | None
        Attempt to add a Player to this game; does not check max players, see Game.is_full()
    end(session: sqlalchemy.orm.Session) -> None
        Wipe the Game from the database
    set_stake(session: sqlalchemy.orm.Session, bet: list[int], stake: int = 1) -> None
        Set the current bet for the round
    get_bet_turn() -> Player
        Return the player who will initiate the bet for the round
    advance_bet_turn(session: sqlalchemy.orm.Session, target: int = -1) -> Player
        Advances the bet turn
    get_bet() -> list[int]
        Return the current bet for the round unjsonified
    set_bet(session: sqlalchemy.orm.Session, bet: list[int]) -> None
        Set the current bet for the round
    is_midround() -> bool
        Test if the game is currently in the middle of a round; i.e. bets have been set
    is_full() -> bool
        Test if the max amount of players have joined
    is_playing(session: sqlalchemy.orm.Session, user_id: int) -> Player | None
        Return Player of current game if it actually exists
    bets_aligned() -> bool:
        Test if all players' bets are aligned and set
    end_round(session: sqlalchemy.orm.Session):
        Do general round end logic
    """

    __tablename__ = "game"
    __mapper_args__ = {
        "polymorphic_identity": "base",
        "polymorphic_on": "type"
        }

    id: Mapped[int] = mapped_column(primary_key = True)
    """Corresponds to the discord channel/thread ID"""

    type: Mapped[str]
    """The type of game"""

    players: Mapped[list["Player"]] = relationship(back_populates = "game", cascade = "all, delete-orphan")
    """Ref to list of players within this game"""

    player_class = Player
    """Player subclass that corresponds to this Game subclass"""

    max_players: int = 0
    """Max amount of players the game of this type can handle; 0 means infinite
    
    Overwritten per child class
    """

    bet_cap: list[int] = [100, 20, 2, 20, 3, 25]
    """The maximum amount of chips that can be bet in a Game"""

    bet_turn: Mapped[int] = mapped_column(default = 0)
    """Player index whose turn it is to bet"""

    stake: Mapped[int] = mapped_column(default = 1)
    """0 - low stakes, 1 - normal stakes, 2 - high stakes"""

    current_bet: Mapped[str] = mapped_column(default = "[0, 0, 0, 0, 0, 0]")
    """The current bet for the round within the game

    If bet is all zeroes, then round hasn't started yet.
    """

    started: Mapped[bool] = mapped_column(default = False)
    """Whether or not the game's first round has begun"""

    @classmethod
    def create_game(cls, session: Session, channel_id: int, stake: int = 1) -> None:
        """Create a game if there isn't one in the channel already
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        channel_id: int
            ID of the Discord channel to make the game in
        stake: int = 1
            Code for stake level of created game
        """

        if session.get(Game, channel_id) is not None:
            return
        
        new_game = cls(id = channel_id, stake = stake)
        session.add(new_game)

        session.commit()

    @classmethod
    def find_game(cls, session: Session, channel: int) -> "Game | None":
        """Return object of Game subclass for a channel, if any
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        channel: int
            ID of the Discord channel

        ### Returns
        The Game object of the channel if it exists, None otherwise
        """

        return session.get(cls, channel)
    
    def join_game(self, session: Session, user: int, name: str) -> Player | None:
        """Attempt to add a Player to this game; does not check max players, see is_full()
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        user: int
            ID of the Discord user
        name: str
            Name of the Player to be created

        ### Returns:
        Subclass of Player
            The player instance created
        None
            The Player already existed
        """

        player = session.get(Player, (user, self.id))
        if player is not None:
            return None
        
        player = self.player_class(user_id = user, game_id = self.id, name = name)
        session.add(player)
        
        session.commit()
        return player

    def end(self, session: Session) -> None:
        """Wipe the Game from the database
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        """

        session.delete(self)
        session.commit()

    def set_stake(self, session: Session, stake: int) -> None:
        """Set the game's stake
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        stake: int
            What to set the stake to

        ### Raises
        InvalidArgumentError
            Stake is not one of the valid states
        """

        if stake < 0 or stake > 2:
            raise InvalidArgumentError
        
        self.stake = stake

        session.commit()

    def get_bet_turn(self) -> Player:
        """Return the player who will initiate the bet for the round
        
        ### Returns
        Player
            The player that corresponds to the bet_turn index
        """
        return self.players[self.bet_turn]

    def advance_bet_turn(self, session: Session, target: int = -1) -> Player:
        """Advances the bet turn
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        target: int = -1
            If any non-negative number, will just try to set bet_turn to that

        ### Returns
        Player
            The player whose turn it is now to bet

        ### Raises
        InvalidArgumentError
            Target is outside of player list bounds
        """

        if target < 0:
            self.bet_turn = (self.bet_turn + 1) % len(self.players)
        elif target >= len(self.players):
            raise InvalidArgumentError
        else:
            self.bet_turn = target

        session.commit()
        return self.get_bet_turn()

    def get_bet(self) -> list[int]:
        """Return the current bet for the round unjsonified
        
        ### Returns
        List of ints corresponding to chip amounts
        """
        return loads(self.current_bet)

    def set_bet(self, session: Session, bet: list[int]) -> None:
        """Set the current bet for the round
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        bet: list[int]
            List of chip amounts to bet for each chip type
        """

        self.current_bet = dumps(bet)

        # Setting bet equivalent to starting round
        if not self.started:
            self.started = True

        session.commit()

    def is_midround(self) -> bool:
        """Test if the game is currently in the middle of a round; i.e. bets have been set
        
        ### Returns
        True
            Game in the middle of round (nonzero bet)
        False
            Game not in round (no bet)
        """

        return self.current_bet != "[0, 0, 0, 0, 0, 0]"
    
    def is_full(self) -> bool:
        """Test if the max amount of players have joined

        ### Returns
        True
            Players in game equals max amount or max is unlimited
        False
            Less players in game than max"""

        return ((self.max_players != 0) and (len(self.players) >= self.max_players))
    
    def is_playing(self, session: Session, user_id: int) -> "Player | None":
        """Return Player of current game if it actually exists

        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        user_id: int
            ID of the Discord user to search for a corresponding Player object

        ### Returns
        A Player object corresponding to channel and user on Discord, or None if it doesn't exist
        """

        return session.get(Player, (user_id, self.id))
    
    def bets_aligned(self) -> bool:
        """Test if all players' bets are aligned and set
        
        ### Returns
        True
            All players's bets are the same and nonzero
        False
            Otherwise
        """

        # No point in checking if only 1 player
        if len(self.players) < 2:
            return False

        # Make sure bets are nonzero, i.e. bets have actually been placed
        for player in self.players:
            if player.bet == "[0, 0, 0, 0, 0, 0]":
                return False

        # Associative property; only need to check consecutive pairs
        for i in range(len(self.players) - 1):
            if self.players[i].bet != self.players[i + 1].bet:
                return False

        return True

    def end_round(self, session: Session):
        """Do general round end logic
        
        To be called at end of subclassed functions

        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        """

        self.current_bet = "[0, 0, 0, 0, 0, 0]"
        for player in self.players:
            player.bet = "[0, 0, 0, 0, 0, 0]"
        self.advance_bet_turn(session)


class MiscPlayer(Player):
    """Represents a player of a Misc game. Inherits most attributes of Player.
    
    ### Attributes
    [PRIMARY, FOREIGN] user_id: int
        User ID of the player
    [PRIMARY, FOREIGN] game_id: int
        ID of the game the Player is playing in

    ### Methods
    """

    __tablename__ = "misc_player"
    __table_args__ = (
        ForeignKeyConstraint(["user_id", "game_id"], ["player.user_id", "player.game_id"]),
        )
    __mapper_args__ = {
        "polymorphic_identity": "misc"
        }

    user_id: Mapped[int] = mapped_column(primary_key = True)
    """User ID of the player"""

    game_id: Mapped[int] = mapped_column(primary_key = True)
    """ID of the game the Player is playing in"""


class Misc(Game):
    """Represents a Misc game with no rules. Inherits most attributes of Game.
    
    ### Attributes
    [PRIMARY, FOREIGN] id: int
        Corresponds to the discord channel/thread ID
    [CLASS] max_players
        Max amount of players the game of this type can handle
    [CLASS] player_class
        Player subclass that corresponds to this Game subclass
    deck: str
        The current deck to be pulled from; jsonified array of ints where each int corresponds to default deck index

    ### Methods
    shuffle(session: sqlalchemy.orm.Session) -> None
        Shuffle all cards back into the deck
    get_deck() -> list[int]
        Get the current deck unjsonified
    draw(session: sqlalchemy.orm.Session, amount: int) -> list[int]
        Draw a single or multiple cards
    end_round(session: sqlalchemy.orm.Session) -> tuple[str, list[tuple[int, str]]]:
        Give the winner the winnings, returning index/name of winner(s); more than 1 means tie
    """

    __tablename__ = "misc"
    __mapper_args__ = {
        "polymorphic_identity": "misc"
        }

    id: Mapped[int] = mapped_column(ForeignKey("game.id"), primary_key = True)
    """Corresponds to the discord channel/thread ID"""

    player_class = MiscPlayer
    """Player subclass that corresponds to this Game subclass"""

    max_players: int = 0
    """Max amount of players the game of this type can handle"""

    deck: Mapped[str] = mapped_column(default = "[]")
    """The current deck to be pulled from; jsonified array of ints where each int corresponds to default deck index"""

    def shuffle(self, session: Session) -> None:
        """Shuffle all cards back into the deck
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        """

        self.deck = dumps(sample(range(52), 52))
        session.commit()

    def get_deck(self) -> list[int]:
        """Get the current deck unjsonified
        
        ### Returns
        list[int]
            List of card indices in the deck
        """
        
        return loads(self.deck)

    def draw(self, session: Session, amount: int = 1) -> list[int]:
        """Draw a single or multiple cards
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        amount: int = 1
            Amount of cards to draw

        ### Raises
        InvalidArgumentError
            More cards to be drawn than there are in the deck
        
        ### Returns
        list[int]
            Cards indices drawn
        """

        current_deck: list[int] = loads(self.deck)

        if len(current_deck) < amount:
            raise InvalidArgumentError

        cards: list[int] = current_deck[:-(amount + 1):-1]
        del current_deck[-amount:]
        self.deck = dumps(current_deck)

        session.commit()
        return cards

    def end_round(self, session: Session, winner: int) -> None:
        """Give the winner the winnings and reset bets (ending round)
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        winner: int
            Discord ID of the Player who is to win
        """

        for player in self.players:
            if player.user_id == winner:
                player.pay_chips(session, loads(self.current_bet))
                break

        super().end_round(session)


class BlackjackPlayer(Player):
    """Represents a player of Blackjack. Inherits most attributes of Player.
    
    ### Attributes
    [PRIMARY, FOREIGN] user_id: int
        User ID of the player
    [PRIMARY, FOREIGN] game_id: int
        ID of the game the Player is playing in
    hand: str
        Jsonified list of cards within player's hand
    state: str
        Either 'hit', 'stand', or 'bust'; represents state of player's hand

    ### Methods
    get_hand(hidden: bool = False) -> list[int]
        Parses hand to list of ints
    stand(session: sqlalchemy.orm.Session) -> None
        Set state to standing
    add_card(session: sqlalchemy.orm.Session, card: int) -> bool
        Add card to hand; return whether still un-busted
    hand_value() -> int
        Calculate the value of the hand for direct comparison
    busted() -> bool
        Returns whether the player has busted
    """

    __tablename__ = "blackjack_player"
    __table_args__ = (
        ForeignKeyConstraint(["user_id", "game_id"], ["player.user_id", "player.game_id"]),
        )
    __mapper_args__ = {
        "polymorphic_identity": "blackjack"
        }

    user_id: Mapped[int] = mapped_column(primary_key = True)
    """User ID of the player"""

    game_id: Mapped[int] = mapped_column(primary_key = True)
    """ID of the game the Player is playing in"""

    hand: Mapped[str] = mapped_column(default = "[]")
    """Jsonified list of cards within player's hand"""

    state: Mapped[str] = mapped_column(default = "hit")
    """Either 'hit', 'stand', or 'bust'; represents state of player's hand"""

    def get_hand(self, hidden: bool = False) -> list[int]:
        """Parses hand to list of ints
        
        ### Parameters
        hidden: bool = False
            Whether the second card in the hand is hidden

        ### Returns
        list[int]
            Each int corresponds to index in deck
        """

        hand = loads(self.hand)
        if hidden and len(hand) >= 2:
            hand[1] = 52

        return hand
    
    def stand(self, session: Session) -> None:
        """Set state to standing
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        """

        self.state = "stand"
        session.commit()
    
    def add_card(self, session: Session, card: int) -> bool:
        """Add card to hand; return whether still un-busted
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        card: int
            Index of card in deck to add
        
        ### Returns
        True
            If hand has not busted from adding the card
        False
            If hand busted from adding the card
        """

        hand = self.get_hand()
        hand.append(card)
        self.hand = dumps(hand)

        # Calculate hand value
        hand_value = self.hand_value()
        if hand_value == 0:
            self.state = "bust"

        session.commit()
        return bool(hand_value)

    def hand_value(self, hidden: bool = False, raw: bool = False) -> int:
        """Calculate the value of the hand for direct comparison
        
        ### Parameters
        hidden: bool = False
            Whether the second card in the hand is hidden
        raw: bool = False
            Whether to give raw hand value without 5-card charlies or busting

        ### Returns
        22
            5-Card Charlie
        0
            Hand value over 21 (bust)
        1-21
            Total value of the hand
        """

        hand = self.get_hand(hidden)
        val = 0

        # Remove suits and convert to direct value
        for i in range(len(hand)):
            if hand[i] == 52:
                hand[i] = 1
                continue
            hand[i] = hand[i] % 13 + 2
            if hand[i] >= 11 and hand[i] <= 13:
                hand[i] = 10
            elif hand[i] == 14:
                hand[i] = 11
        for i in hand:
            val += i
        
        # Try to reduce aces if busting
        while val > 21 and 11 in hand:
            hand[hand.index(11)] = 1
            val -= 10

        if raw:
            return val
        elif val > 21:
            return 0
        elif len(hand) >= 5:
            return 22
        else:
            return val
        
    def busted(self) -> bool:
        """Returns whether the player has busted"""

        return self.state == "bust"


class Blackjack(Game):
    """Represents a game of Blackjack. Inherits most attributes of Game.
    
    ### Attributes
    [PRIMARY, FOREIGN] id: int
        Corresponds to the discord channel/thread ID
    [CLASS] max_players
        Max amount of players the game of this type can handle
    [CLASS] player_class
        Player subclass that corresponds to this Game subclass
    round_turn: int
        The first turn of the round; determines ordering of the hands in first post
    curr_turn: int
        The current turn of the round; corresponds to index of player list
    deck: str
        The current deck to be pulled from; jsonified array of ints where each int corresponds to default deck index

    ### Methods
    shuffle(session: sqlalchemy.orm.Session) -> None
        Shuffle all cards back into the deck
    draw(session: sqlalchemy.orm.Session, amount: int = 1) -> list[int] | int
        Draw a single or multiple cards
    start_round(session: sqlalchemy.orm.Session, players: list[int] = None) -> bool
        Deal the initial two cards to each player given and rotate turn order
    get_turn() -> BlackjackPlayer
        Get player whose turn it is
    is_all_done() -> bool:
        Test whether every player has stood/busted
    next_turn(session: sqlalchemy.orm.Session) -> None
        Advance the turn counter
    end_round(session: sqlalchemy.orm.Session) -> tuple[str, list[tuple[int, str]]]:
        Give the winner the winnings, returning index/name of winner(s); more than 1 means tie
    get_deck() -> list[int]
        Get the current deck unjsonified
    """

    __tablename__ = "blackjack"
    __mapper_args__ = {
        "polymorphic_identity": "blackjack"
        }

    id: Mapped[int] = mapped_column(ForeignKey("game.id"), primary_key = True)
    """Corresponds to the discord channel/thread ID"""

    player_class = BlackjackPlayer
    """Player subclass that corresponds to this Game subclass"""

    max_players: int = 4
    """Max amount of players the game of this type can handle"""

    round_turn: Mapped[int] = mapped_column(default = -1)
    """The first turn of the round; determines ordering of the hands in first post"""

    curr_turn: Mapped[int] = mapped_column(default = 0)
    """The current turn of the round; corresponds to index of player list"""

    deck: Mapped[str] = mapped_column(default = "[]")
    """The current deck to be pulled from; jsonified array of ints where each int corresponds to default deck index"""

    def shuffle(self, session: Session) -> None:
        """Shuffle all cards back into the deck
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        """

        self.deck = dumps(sample(range(52), 52))
        session.commit()

    def draw(self, session: Session, amount: int = 1) -> list[int]:
        """Draw a single or multiple cards
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        amount: int = 1
            Amount of cards to draw
        
        ### Returns
        list[int]
            Cards indices drawn
        """

        current_deck: list[int] = loads(self.deck)

        cards: list[int] = current_deck[:-(amount + 1):-1]
        del current_deck[-amount:]
        self.deck = dumps(current_deck)

        session.commit()
        return cards

    def start_round(self, session: Session, players: list[int] = None) -> bool:
        """Deal the initial two cards to each player given and rotate turn order
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        players: list[int]
            List of users to give cards to, by index in Player list; if omitted, then all players are dealt hands

        ### Returns
        True
            Deck was shuffled
        False
            Deck was not shuffled
        """

        if shuffled := (len(loads(self.deck)) <= 26):
            self.shuffle(session)

        if players is None:
            players = range(len(self.players))

        drawn: list[int] = self.draw(session, 2 * len(players))
        for i in range(len(self.players)):
            if i in players:
                self.players[i].state = "hit"
                self.players[i].hand = dumps(drawn[-2:])
                del drawn[-2:]
            else:
                self.players[i].state = "bust"
                self.players[i].hand = "[]"

        self.round_turn = (self.round_turn + 1) % len(self.players)
        self.curr_turn = self.round_turn

        if self.players[self.curr_turn].state == "bust":
            self.next_turn(session)

        session.commit()

        return shuffled

    def get_turn(self) -> "BlackjackPlayer":
        """Get player whose turn it is
        
        ### Returns
        The BlackjackPlayer whose turn it is
        """

        return self.players[self.curr_turn]
    
    def is_all_done(self) -> bool:
        """Test whether every player has stood/busted
        
        ### Returns
        True
            Every player except one has busted, or every player is standing/busted
        False
            At least one player is still Hitting
        """

        states = [0, 0, 0]
        for player in self.players:
            if player.state == "hit":
                states[0] += 1
            elif player.state == "stand":
                states[1] += 1
            elif player.state == "bust":
                states[2] += 1

        # If all but one player have busted, that player auto wins
        if states[2] == len(self.players) - 1:
            return True
        # Otherwise, more than 1 player is still hitting/standing; end play when all are standing/busting
        if states[0] == 0:
            return True
        
        return False
    
    def next_turn(self, session: Session) -> None:
        """Advance the turn counter
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        """

        self.curr_turn = (self.curr_turn + 1) % len(self.players)
        while self.players[self.curr_turn].state != "hit":
            self.curr_turn = (self.curr_turn + 1) % len(self.players)

        session.commit()

    def end_round(self, session: Session) -> tuple[str, list[tuple[int, str]]]:
        """Give the winner the winnings, returning index/name of winner(s); more than 1 means tie
        
        If tie, instead multiply bet by 3, or 9 on 21 tie; apply bet limits
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope

        ### Returns
        Index 0
            Win condition string for special dialogue; n = norm, b = blackjack, f = five card charlie
        Index 1
            List of winners by user id--name pairs
        """

        # Compare final hands
        end_vals: list[int] = []
        for player in self.players:
            end_vals.append(player.hand_value())

        winner_val = max(end_vals)
        winners = []
        for i in range(len(end_vals)):
            if end_vals[i] == winner_val:
                winners.append((i, self.players[i].name))

        if winner_val == 22:
            win_con = "f"
        elif winner_val == 21:
            win_con = "b"
        else:
            win_con = "n"

        # If more than 1 winner, then tie occurred
        if len(winners) == 1:
            # Give winner the bet value, then reset bets
            winner: BlackjackPlayer = self.players[winners[0][0]]
            winner.pay_chips(session, loads(self.current_bet))
            super().end_round(session)
        else:
            # Multiply bet
            bet = loads(self.current_bet)
            if winner_val == 21:
                for i in range(len(bet)):
                    bet[i] *= 9
            else:
                for i in range(len(bet)):
                    bet[i] *= 3

            # Conform to bet cap
            clamp(bet, self.bet_cap)

            self.current_bet = dumps(bet)
            session.commit()
        
        return (win_con, winners)

    def get_deck(self) -> list[int]:
        """Get the current deck unjsonified
        
        ### Returns
        list[int]
            List of card indices in the deck
        """
        
        return loads(self.deck)


class TourneyPlayer(Player):
    """Represents a player of Tourney. Inherits most attributes of Player.
    
    ### Attributes
    [PRIMARY, FOREIGN] user_id: int
        User ID of the player
    [PRIMARY, FOREIGN] game_id: int
        ID of the game the Player is playing in
    hand: str
        Jsonified list of cards within player's hand and whether they have been played
    played: int
        The index of the hand that will be played in this turn
    points: int
        How many points the player has in the current round

    ### Methods
    get_hand() -> list[list[int | bool]]
        Parses hand to list of pairs of cards and whether they've been played or not
    play_card(session: sqlalchemy.orm.Session, index: int) -> bool
        Present a card to be evaluated against other players' cards
    tiebreaker() -> int
        Get card that hasn't been played yet
    """

    __tablename__ = "tourney_player"
    __table_args__ = (
        ForeignKeyConstraint(["user_id", "game_id"], ["player.user_id", "player.game_id"]),
        )
    __mapper_args__ = {
        "polymorphic_identity": "tourney"
        }

    user_id: Mapped[int] = mapped_column(primary_key = True)
    """User ID of the player"""

    game_id: Mapped[int] = mapped_column(primary_key = True)
    """ID of the game the Player is playing in"""

    hand: Mapped[str] = mapped_column(default = "[]")
    """Jsonified list of cards within player's hand and whether they have been played"""

    played: Mapped[int] = mapped_column(default = -1)
    """The index of the hand that will be played in this turn"""

    points: Mapped[int] = mapped_column(default = 0)
    """How many points the player has in the current round"""

    def get_hand(self) -> list[list[int | bool]]:
        """Parses hand to list of ints

        ### Returns
        list[list[int | bool]]
            Each pair has an int corresponds to index in deck and whether card has already been played
        """

        return loads(self.hand)
    
    def play_card(self, session: Session, index: int) -> bool:
        """Present a card to be evaluated against other players' cards
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        index: int
            Index of the card to present in the hand

        ### Returns
        bool
            Whether operation successful or card already played

        ### Raises
        InvalidArgumentError
            The index given is out of bounds
        """

        hand: list[list[int | bool]] = loads(self.hand)

        if index >= len(hand):
            raise InvalidArgumentError
        
        if hand[index][1]:
            return False
        
        self.played = index

        session.commit()
        return True

    def tiebreaker(self) -> int:
        """Get card that hasn't been played yet

        ### Returns
        int
            First card that is unplayed
        """

        for card in loads(self.hand):
            if not card[1]:
                return card[0]
        
        return 0

class Tourney(Game):
    """Represents a game of Tourney. Inherits most attributes of Game.
    
    ### Attributes
    [PRIMARY, FOREIGN] id: int
        Corresponds to the discord channel/thread ID
    [CLASS] max_players
        Max amount of players the game of this type can handle
    [CLASS] player_class
        Player subclass that corresponds to this Game subclass
    turn: int
        The current turn of the round

    ### Methods
    start_round(session: sqlalchemy.orm.Session)
        Deal the initial two cards to each player given and rotate turn order
    all_played() -> bool
        Test whether every player has played a card
    evaluate_turn(session: sqlalchemy.orm.Session) -> TourneyPlayer
        Compare cards and reward point to winner
    end_round(session: sqlalchemy.orm.Session) -> list[TourneyPlayer]
        Evaluate winner of round and reward them
    """

    __tablename__ = "tourney"
    __mapper_args__ = {
        "polymorphic_identity": "tourney"
        }

    id: Mapped[int] = mapped_column(ForeignKey("game.id"), primary_key = True)
    """Corresponds to the discord channel/thread ID"""

    player_class = TourneyPlayer
    """Player subclass that corresponds to this Game subclass"""

    max_players: int = 6
    """Max amount of players the game of this type can handle"""

    turn: Mapped[int] = mapped_column(default = 1)
    """The current turn of the round"""

    def start_round(self, session: Session):
        """Deal initial cards, reset states
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        """

        draw = sample(range(52), len(self.players) * (len(self.players) + 2))

        player: TourneyPlayer
        for player in self.players:
            player.played = -1
            player.points = 0
            # Cards added to hand equal to number of players plus 2
            player.hand = dumps([[card, False] for card in draw[:-(len(self.players) + 3):-1]])
            del draw[-(len(self.players) + 2):]

        # Reset turn counter
        self.turn = 1

        session.commit()

    def all_played(self) -> bool:
        """Test whether every player has played a card

        ### Returns
        bool
            Whether every played has played a card
        """

        player: TourneyPlayer
        for player in self.players:
            if player.played == -1:
                return False

        return True

    def evaluate_turn(self, session: Session) -> TourneyPlayer:
        """Compare cards and reward point to winner
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope

        ### Returns
        TourneyPlayer
            Player that won the turn

        ### Raises
        InvalidArgumentError
            At least one player has not played a card
        """

        # Load played cards, set played flag to True for each card, and reset played for next turn
        played = []
        player: TourneyPlayer
        for player in self.players:
            if player.played == -1:
                session.rollback()
                raise InvalidArgumentError
            hand = loads(player.hand)
            card = hand[player.played][0]
            played.append(card)
            hand[player.played] = [card, True]
            player.hand = dumps(hand)
            player.played = -1

        # Evaluate card values in terms of value before suit
        played = [((card % 13) * 4) + (card // 13) for card in played]

        # Compare cards
        max = -1
        winner = 0
        for i in range(len(played)):
            if played[i] > max:
                winner = i
                max = played[i]

        # Award point
        winner: TourneyPlayer = self.players[winner]
        winner.points += 1

        # Advance turn counter
        self.turn += 1

        session.commit()
        return winner

    def end_round(self, session: Session) -> list[TourneyPlayer]:
        """Evaluate winner of round and reward them
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope

        ### Returns
        list[TourneyPlayer]
            All players that tied for winner in ascending order by tiebreaker
        """

        # Evaluate winners, or ties
        # First get top points
        max = 0
        player: TourneyPlayer
        for player in self.players:
            if player.points > max:
                max = player.points
        # Then get all winners
        winners: list[TourneyPlayer] = []
        for player in self.players:
            if player.points == max:
                winners.append(player)

        # Break ties by looking at final card; all players should have 1 card unplayed at end of round
        winners.sort(reverse = True, key = lambda player: player.tiebreaker())

        # Reward winner; in general scenario, 1 player wins minimum 2 pts, so bet multiplied by pts - 1
        reward = self.get_bet()
        reward = [chip * (max - 1) for chip in reward]
        # Clamp reward
        clamp(reward, self.bet_cap)
        winners[0].pay_chips(session, reward)

        # General end round logic
        super().end_round(session)

        return winners
