"""Contains all SQLAlchemy ORM models"""

print("Loading module 'dbmodels'...")

from typing import List, Optional, Tuple, Dict
from json import dumps, loads
from random import sample

from sqlalchemy import ForeignKey, ForeignKeyConstraint, select, insert, update, delete
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from bot import SQLBase
from auxiliary import InvalidArgumentError, all_zero


class User(SQLBase):
    """Represents the saved data corresponding to a single discord user.

    ### Attributes
    [PRIMARY] id: int
        Corresponds to Discord user ID
    [BACKREF] accounts: list[ChipAccount]
        List of chip accounts under this User
        
    ### Methods
    [STATIC] find_user(session: sqlalchemy.orm.Session, id: str) -> User
        Returns the User object corresponding to the given Discord ID
    create_account(session: sqlalchemy.orm.Session, name: str) -> bool
        Tries to open a chip account under the given name
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key = True)
    """Corresponds to Discord user ID"""

    accounts: Mapped[List["ChipAccount"]] = relationship(back_populates = "owner", cascade = "all, delete-orphan")
    """List of chip accounts under this User"""

    @staticmethod
    def find_user(session: Session, id: int) -> "User":
        """Return the User object corresponding to the given Discord ID

        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        id: int
            Discord user ID

        ### Returns
        User object with matching id. Creates new user object if no match found.
        """

        found_user = session.get(User, id)
        
        if found_user is None:
            # Create new default user data if no matching user data found
            new_user = User(id = id)
            session.add(new_user)
            session.commit()
            return new_user
        else:
            return found_user
        
    def create_account(self, session: Session, name: str) -> bool:
        """Attempt to open a chip account under the given name

        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
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
            new_account = ChipAccount(owner_id = self.id, name = name)
            session.add(new_account)
            session.commit()
            return True
        else:
            return False


class ChipAccount(SQLBase):
    """Represents a chips account belonging to a single character.

    ### Attributes
    [PRIMARY] name: str
        Unique name that the account is under
    [FOREIGN] owner_id: int
        ID of User who owns this account
    [BACKREF] owner: User
        Direct reference to User who owns this account
    chips: str
        Jsonified array of chips of each type within the account
        
    ### Methods
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

    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete = "CASCADE"))
    """ID of User who owns this account"""

    owner: Mapped["User"] = relationship(back_populates = "accounts")
    """Direct reference to User who owns this account"""
    
    chips: Mapped[str] = mapped_column(default = "[0, 0, 0, 0, 0, 0]")
    """Jsonified array of chips of each type within the account"""

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
    
    def get_bal(self) -> List[int]:
        """Returns the balance unjsonified
        
        ### Returns
        A list of integers containing each type of chip in the account
        """

        return loads(self.chips)

    def deposit(self, session: Session, amount: List[int]) -> None:
        """Deposit an amount of chips into the account

        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        amount: List[int]
            Amount of each type of chips to add to the balance

        ### Throws
        InvalidArgumentError
            Amount given is negative or not enough chip arguments
        """

        for chips in amount:
            if chips < 0:
                raise InvalidArgumentError
        
        current_chips: List[int] = loads(self.chips)
        if len(amount) != len(current_chips):
            raise InvalidArgumentError
        
        for i in range(len(amount)):
            current_chips[i] += amount[i]

        self.chips = dumps(current_chips)
        session.commit()
    
    def withdraw(self, session: Session, amount: List[int]) -> bool:
        """Withdraw an amount of chips from the account

        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        amount: List[int]
            Amount of each type of chips to remove from the balance

        ### Returns
        True
            Successful withdraw
        False
            Any amount of chips was more than balance

        ### Throws
        InvalidArgumentError
            Amount given is negative or not enough chip arguments
        """

        for chips in amount:
            if chips < 0:
                raise InvalidArgumentError
        
        current_chips: List[int] = loads(self.chips)
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

        ### Throws
        InvalidArgumentError
            New name is empty string
        """

        if new == "":
            raise InvalidArgumentError

        self.name = new
        session.commit()


class Game(SQLBase):
    """Represents a currently running game for a channel/thread.
    
    ### Attributes
    [PRIMARY] id: int
        Corresponds to the discord channel/thread ID
    [POLYMORPHIC] type: str
        The type of game
    [BACKREF] players: list[Player]
        Ref to list of players within this game
    [CLASS] max_players: int
        Max amount of players the game of this type can handle; 0 means infinite
    current_bet: str
        The current bet for the round within the game
    started: bool
        Whether or not the game's first round has begun

    ### Methods
    [STATIC] find_game(session: sqlalchemy.orm.Session, channel: int) -> Game | None
        Return Game object for a channel, if any
    end(session: sqlalchemy.orm.Session) -> None
        Wipe the Game from the database
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

    players: Mapped[List["Player"]] = relationship(back_populates = "game", cascade = "all, delete-orphan")
    """Ref to list of players within this game"""

    max_players: int = 0
    """Max amount of players the game of this type can handle; 0 means infinite
    
    Overwritten per child class
    """

    current_bet: Mapped[str] = mapped_column(default = "[0, 0, 0, 0, 0, 0]")
    """The current bet for the round within the game

    If bet is all zeroes, then round hasn't started yet.
    """

    started: Mapped[bool] = mapped_column(default = False)
    """Whether or not the game's first round has begun"""

    @staticmethod
    def find_game(session: Session, channel: int) -> "Game | None":
        """Return Game object for a channel, if any
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        channel: int
            ID of the Discord channel

        ### Returns
        The Game object of the channel if it exists, None otherwise
        """

        return session.get(Game, channel)
    
    def end(self, session: Session) -> None:
        """Wipe the Game from the database
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        """

        session.delete(self)
        session.commit()

    def get_bet(self) -> List[int]:
        """Return the current bet for the round unjsonified
        
        ### Returns
        List of ints corresponding to chip amounts
        """
        return loads(self.current_bet)

    def set_bet(self, session: Session, bet: List[int]) -> None:
        """Set the current bet for the round
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        bet: list[int]
            List of chip amounts to bet for each chip type
        """

        self.current_bet = dumps(bet)

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

        return self.max_players == 0 or len(self.players) >= self.max_players
    
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
    bet: str
        How many chips the Player is currently willing to bet

    ### Methods
    leave(session: sqlalchemy.orm.Session) -> None
        Remove Player from Game, i.e. delete Player from database
    rename(session: sqlalchemy.orm.Session, new_name: str) -> None
        Change the name of the player
    set_bet(session: sqlalchemy.orm.Session, bet: list[int]) -> None
        Set the Player's bet
    get_chips() -> list[int]
        Return the Player's current amount of chips unjsonified
    set_chips(session: sqlalchemy.orm.Session, amount: list[int]) -> None
        Set the Player's chips directly
    pay_chips(session: sqlalchemy.orm.Session, amount: list[int]) -> None
        Add an amount of chips to the Player's current amount of chips
    use_chips(session: sqlalchemy.orm.Session, amount: list[int]) -> bool
        Removes a player's chips, if able
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

    game: Mapped[Game] = relationship(back_populates = "players")
    """Direct reference to corresponding Game"""

    type: Mapped[str]
    """The type of game this Player belongs to"""

    name: Mapped[str]
    """What name the Player shall be referred to as"""

    chips: Mapped[str] = mapped_column(default = "[0, 0, 0, 0, 0, 0]")
    """Jsonified array of chips of each type the Player holds"""

    bet: Mapped[str] = mapped_column(default = "[0, 0, 0, 0, 0, 0]")
    """How many chips the Player is currently willing to bet"""
    
    def leave(self, session: Session) -> None:
        """Remove Player from Game, i.e. delete Player from database
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        """

        session.delete(self)
        session.commit()

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

    def set_bet(self, session: Session, bet: List[int]) -> None:
        """Set the Player's bet
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        bet: list[int]
            The bet to set the Player's bet to
        """

        self.bet = dumps(bet)
        session.commit()

    def get_chips(self) -> List[int]:
        """Return the Player's current amount of chips unjsonified
        
        ### Returns
        List of integers corresponding to types of chips
        """

        return loads(self.chips)
    
    def set_chips(self, session: Session, amount: List[int]) -> None:
        """Set the Player's chips directly
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        amount: list[int]
            The list of chips to set the Player's chips to
        """

        self.chips = dumps(amount)
        session.commit()

    def pay_chips(self, session: Session, amount: List[int]) -> None:
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

    def use_chips(self, session: Session, amount: List[int]) -> bool:
        """Removes a player's chips, if able
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        amount: list[int]
            The list of chips to try to remove from the Player's chips

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

        self.chips = dumps(bal)
        session.commit()
        return True


class Blackjack(Game):
    """Represents a game of Blackjack. Inherits most attributes of Game.
    
    ### Attributes
    [PRIMARY, FOREIGN] id: int
        Corresponds to the discord channel/thread ID
    [CLASS] max_players = 4
        Max amount of players the game of this type can handle
    round_turn: int
        The first turn of the round; determines ordering of the hands in first post
    curr_turn: int
        The current turn of the round; corresponds to index of player list
    deck: str
        The current deck to be pulled from; jsonified array of ints where each int corresponds to default deck index

    ### Methods
    [STATIC] create_game(session: sqlalchemy.orm.Session, channel_id: int) -> Blackjack | None
        Create a blackjack game if there isn't one in the channel already
    shuffle(session: sqlalchemy.orm.Session) -> None
        Shuffle all cards back into the deck
    draw(session: sqlalchemy.orm.Session, amount: int) -> list[int] | int
        Draw a single or multiple cards
    start_round(session: sqlalchemy.orm.Session, players: list[int] = None) -> bool
        Deal the initial two cards to each player given and rotate turn order
    join_game(session: sqlalchemy.orm.Session, user: int, name: str) -> BlackjackPlayer | None
        Attempt to add a Player to this game; does not check max players, see Game.is_full()
    get_turn() -> BlackjackPlayer
        Get player whose turn it is
    is_all_done() -> bool:
        Test whether every player has stood/busted
    next_turn(session: sqlalchemy.orm.Session) -> None
        Advance the turn counter
    end_round(session: sqlalchemy.orm.Session) -> tuple[str, list[tuple[int, str]]]:
        Give the winner the winnings, returning index/name of winner(s); more than 1 means tie
    """

    __tablename__ = "blackjack"
    __mapper_args__ = {
        "polymorphic_identity": "blackjack"
        }

    id: Mapped[int] = mapped_column(ForeignKey("game.id"), primary_key = True)
    """Corresponds to the discord channel/thread ID"""

    max_players: int = 4
    """Max amount of players the game of this type can handle"""

    round_turn: Mapped[int] = mapped_column(default = 0)
    """The first turn of the round; determines ordering of the hands in first post"""

    curr_turn: Mapped[int] = mapped_column(default = 0)
    """The current turn of the round; corresponds to index of player list"""

    deck: Mapped[str] = mapped_column(default = "[]")
    """The current deck to be pulled from; jsonified array of ints where each int corresponds to default deck index"""

    @staticmethod
    def create_game(session: Session, channel_id: int) -> "Blackjack | None":
        """Create a blackjack game if there isn't one in the channel already
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        channel_id: int
            ID of the Discord channel to make the game in

        ### Returns
        The created Blackjack game or None if not created
        """

        if session.get(Game, channel_id) is not None:
            return None
        
        new_game = Blackjack(id = channel_id)
        session.add(new_game)

        session.commit()
        return new_game

    def shuffle(self, session: Session) -> None:
        """Shuffle all cards back into the deck
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        """

        self.deck = dumps(sample(range(52), 52))
        session.commit()

    def draw(self, session: Session, amount: int) -> List[int] | int:
        """Draw a single or multiple cards
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        amount: int
            Amount of cards to draw
        
        ### Returns
        int
            Card index drawn, if only 1
        list[int]
            Cards indices drawn, if more than 1
        """

        current_deck: List[int] = loads(self.deck)

        if amount == 1:
            cards: int = current_deck.pop()
            self.deck = dumps(current_deck)
        elif amount > 1:
            cards: List[int] = current_deck[-amount:]
            del current_deck[-amount:]
            self.deck = dumps(current_deck)

        session.commit()
        return cards

    def start_round(self, session: Session, players: List[int] = None) -> bool:
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

        if not self.started:
            self.started = True

        if shuffled := (len(loads(self.deck)) <= 26):
            self.shuffle(session)

        if players is None:
            players = range(len(self.players))

        drawn: List[int] = self.draw(session, 2 * len(players))
        for i in range(len(self.players)):
            if i in players:
                self.players[i].state = "hit"
                self.players[i].hand = dumps(drawn[-2:])
                del drawn[-2:]
            else:
                self.players[i].state = "stand"
                self.players[i].hand = "[]"

        self.round_turn = (self.round_turn + 1) % len(self.players)
        self.curr_turn = self.round_turn

        if self.players[self.curr_turn].state == "stand":
            self.next_turn(session)

        session.commit()

        return shuffled

    def join_game(self, session: Session, user: int, name: str) -> "BlackjackPlayer | None":
        """Attempt to add a Player to this game; does not check max players, see is_full()
        
        ### Parameters
        session: sqlalchemy.orm.Session
            Database session scope
        user: int
            ID of the Discord user
        name: str
            Name of the Player to be created

        ### Returns:
        BlackjackPlayer
            The player instance created
        None
            The Player already existed
        """

        player = session.get(BlackjackPlayer, (user, self.id))
        if player is not None:
            return None
        
        player = BlackjackPlayer(user_id = user, game_id = self.id, name = name)
        session.add(player)
        
        session.commit()
        return player
    
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

    def end_round(self, session: Session) -> Tuple[str, List[Tuple[int, str]]]:
        """Give the winner the winnings, returning index/name of winner(s); more than 1 means tie
        
        If tie, instead multiply bet by 3, or 9 on 21 tie
        
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
        end_vals: List[int] = []
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
            self.current_bet = "[0, 0, 0, 0, 0, 0]"
            for player in self.players:
                player.set_bet(session, [0, 0, 0, 0, 0, 0])
        else:
            # Multiply bet
            bet = loads(self.current_bet)
            if winner_val == 21:
                for i in range(len(bet)):
                    bet[i] *= 9
            else:
                for i in range(len(bet)):
                    bet[i] *= 3
            self.current_bet = dumps(bet)
            session.commit()
        
        return (win_con, winners)


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
    get_hand() -> list[int]
        Parses hand to list of ints
    stand(session: sqlalchemy.orm.Session) -> None
        Set state to standing
    add_card(session: sqlalchemy.orm.Session, card: int) -> bool
        Add card to hand; return whether still un-busted
    hand_value() -> int:
        Calculate the value of the hand for direct comparison
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

    def get_hand(self) -> List[int]:
        """Parses hand to list of ints
        
        ### Returns
        list[int]
            Each int corresponds to index in deck
        """

        return loads(self.hand)
    
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

        hand: List[int] = loads(self.hand)
        hand.append(card)
        self.hand = dumps(hand)

        # Calculate hand value
        hand_value = self.hand_value()
        if hand_value == 0:
            self.state = "bust"

        session.commit()
        return bool(hand_value)

    def hand_value(self) -> int:
        """Calculate the value of the hand for direct comparison

        ### Returns
        22
            5-Card Charlie
        0
            Hand value over 21 (bust)
        1-21
            Total value of the hand
        """

        hand: List[int] = loads(self.hand)
        val = 0

        # Remove suits and convert to direct value
        for i in range(len(hand)):
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

        if val > 21:
            return 0
        elif len(hand) >= 5:
            return 22
        else:
            return val