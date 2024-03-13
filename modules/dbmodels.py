"""Contains all SQLAlchemy ORM models"""

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

    [BACKREF] accounts: List[ChipAccount]
        List of chip accounts under this User
        
    ### Methods
    [STATIC] find_user(session: Session, id: str) -> User
        Returns the User object corresponding to the given Discord ID

    create_account(session: Session, name: str) -> bool
        Tries to open a chip account under the given name
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key = True)
    """Corresponds to Discord user ID"""

    accounts: Mapped[List["ChipAccount"]] = relationship(back_populates = "owner", cascade = "all, delete-orphan")
    """List of chip accounts under this User"""

    @staticmethod
    def find_user(session: Session, id: int) -> "User":
        """Returns the User object corresponding to the given Discord ID

        ### Parameters
        session: Session
            Database session scope

        id: int
            Discord user ID

        ### Returns
        User object with matching id. Creates new user object if no match found.
        """

        found_user = session.execute(
            select(User)
            .where(User.id == id)
            ).scalar()
        
        if found_user is None:
            # Create new default user data if no matching user data found
            new_user = User(id = id)
            session.add(new_user)
            session.commit()
            return new_user
        else:
            return found_user
        
    def create_account(self, session: Session, name: str) -> bool:
        """Tries to open a chip account under the given name

        ### Parameters
        session: Session
            Database session scope

        name: str
            In-character name that the account is going under

        ### Returns
        True on success, False if account already existed.
        """

        found_account = session.execute(
            select(ChipAccount)
            .where(ChipAccount.name == name)
            ).scalar()
        
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
    [PRIMARY] str: name
        Unique name that the account is under

    [FOREIGN] owner_id: int
        ID of User who owns this account

    [BACKREF] owner: User
        Direct reference to User who owns this account

    chips: str
        Jsonified array of chips of each type within the account
        
    ### Methods
    [STATIC] find_account(session: Session, username: str) -> ChipAccount | None
        Returns the ChipAccount if it exists

    get_bal() -> List[int]
        Returns the balance unjsonified
    
    deposit(session: Session, amount: List[int]) -> None
        Deposit an amount of chips into the account

    withdraw(session: Session, amount: List[int]) -> bool
        Withdraw an amount of chips from the account
    
    change_name(session: Session, new: str) -> None
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
        session: Session
            Database session scope

        name: str
            Name of account to search for

        ### Returns
        ChipAccount with matching username or None if not found.
        """

        return session.execute(
            select(ChipAccount)
            .where(ChipAccount.name == name)
            ).scalar()
    
    def get_bal(self) -> List[int]:
        """Returns the balance unjsonified
        
        ### Returns
        A list of integers containing each type of chip in the account
        """

        return loads(self.chips)

    def deposit(self, session: Session, amount: List[int]) -> None:
        """Deposit an amount of chips into the account

        ### Parameters
        session: Session
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
        session: Session
            Database session scope

        amount: List[int]
            Amount of each type of chips to remove from the balance

        ### Returns
            True if successful, false if any amount of chips was more than balance

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
        session: Session
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

    ### Methods
    """ #TODO

    __tablename__ = "game"

    id: Mapped[int] = mapped_column(primary_key = True)
    """Corresponds to the discord channel/thread ID"""

    type: Mapped[str]
    """The type of game"""

    players: Mapped[List["Player"]] = relationship(back_populates = "game", cascade = "all, delete-orphan")
    """Ref to list of players within this game"""

    max_players: int = 0

    current_bet: Mapped[str] = mapped_column(default = "[0, 0, 0, 0, 0, 0]")
    """The current bet for the round within the game

    If bet is all zeroes, then round hasn't started yet.
    """

    started: Mapped[bool] = mapped_column(default = False)
    """Whether or not the game's first round has begun"""

    __mapper_args__ = {
        "polymorphic_identity": "base",
        "polymorphic_on": "type"
    }

    @staticmethod
    def find_game(session: Session, channel: int) -> "Game | None":
        return session.get(Game, channel)
    
    def end(self, session: Session):
        session.delete(self)
        session.commit()

    def set_bet(self, session: Session, bet: List[int]) -> None:
        """Sets current_bet"""

        self.current_bet = dumps(bet)

        session.commit()

    def is_midround(self) -> bool:
        """Tests if the round is currently in the middle of a round; i.e. bets have been set"""

        return self.current_bet != "[0, 0, 0, 0, 0, 0]"
    
    def is_full(self) -> bool:
        """Tests if the max amount of players have joined"""

        return len(self.players) >= self.max_players
    
    def is_playing(self, session: Session, user_id: int) -> "Player | None":
        """Tests if a user is already part of the game"""

        return session.get(Player, (user_id, self.id))
    
    def bets_aligned(self) -> bool:
        """Tests if all players' bets are aligned and nonzero"""

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

    ### Methods
    """ #TODO

    __tablename__ = "player"

    user_id: Mapped[int] = mapped_column(primary_key = True)
    """User ID of the player"""

    game_id: Mapped[int] = mapped_column(ForeignKey("game.id", ondelete = "CASCADE"), primary_key = True)
    """ID of the game the Player is playing in"""

    game: Mapped[Game] = relationship(back_populates = "players")
    """Ref to related game"""

    type: Mapped[str]
    """The type of game"""

    name: Mapped[str]
    """What name the player shall be referred to as"""

    chips: Mapped[str] = mapped_column(default = "[0, 0, 0, 0, 0, 0]")
    """Jsonified array of chips of each type the player holds"""

    bet: Mapped[str] = mapped_column(default = "[0, 0, 0, 0, 0, 0]")
    """What the player is currently willing to bet"""

    __mapper_args__ = {
        "polymorphic_identity": "base",
        "polymorphic_on": "type"
    }
    
    def leave(self, session: Session):
        session.delete(self)
        session.commit()

    def set_bet(self, session: Session, bet: List[int]) -> None:
        """Sets bet"""

        self.bet = dumps(bet)

        session.commit()

    def get_chips(self) -> List[int]:
        """Get chips unjsonified"""

        return loads(self.chips)

    def pay_chips(self, session: Session, bet: List[int]) -> None:
        """Gives a player chips"""

        bal = loads(self.chips)
        for i in range(len(bal)):
            bal[i] += bet[i]
        self.chips = dumps(bal)

        session.commit()

    def use_chips(self, session: Session, bet: List[int]) -> bool:
        # TODO
        return

class Blackjack(Game):
    """Represents a game of Blackjack.
    
    ### Attributes

    ### Methods
    """ #TODO

    __tablename__ = "blackjack"

    id: Mapped[int] = mapped_column(ForeignKey("game.id"), primary_key = True)
    """Corresponds to the discord channel/thread ID"""

    max_players: int = 4

    round_turn: Mapped[int] = mapped_column(default = 0)
    """The first turn of the round; determines ordering of the hands in first post"""

    curr_turn: Mapped[int] = mapped_column(default = 0)
    """The current turn of the round; corresponds to index of player list"""

    deck: Mapped[str] = mapped_column(default = "[]")
    """The current deck to be pulled from; jsonified array of ints where each int corresponds to default deck index"""

    __mapper_args__ = {
        "polymorphic_identity": "blackjack"
    }

    @staticmethod
    def create_game(session: Session, channel_id: int) -> "Blackjack | None":
        if session.get(Game, channel_id) is not None:
            return None
        
        new_game = Blackjack(id = channel_id)
        session.add(new_game)

        session.commit()
        return new_game

    def shuffle(self, session: Session) -> None:
        """Shuffle the discard back into the deck"""

        self.deck = dumps(sample(range(52), 52))

        session.commit()

    def draw(self, session: Session, amount: int) -> List[int] | int:
        """Draw a single or multiple cards"""

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
        
        returns whether shuffled
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
        """Tries to have a user join the game"""

        player = session.get(BlackjackPlayer, (user, self.id))
        if player is not None:
            return None
        
        player = BlackjackPlayer(user_id = user, game_id = self.id, name = name)
        session.add(player)
        
        session.commit()
        return player
    
    def get_names(self) -> List[str]:
        """Gets names of players in round turn order"""

        names: List[str] = []
        for i in range(len(self.players)):
            names.append(self.players[(i + self.round_turn) % len(self.players)].name)
        
        return names
    
    def get_turn_name(self) -> str:
        """Get name of player whose turn it is"""

        return self.players[self.curr_turn].name
    
    def get_turn(self) -> int:
        """Get user id of player whose turn it is"""

        return self.players[self.curr_turn].user_id
    
    def is_all_done(self) -> bool:
        """Test whether every player has stood/busted"""

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
        """Advance the turn counter"""

        self.curr_turn = (self.curr_turn + 1) % len(self.players)
        while self.players[self.curr_turn].state != "hit":
            self.curr_turn = (self.curr_turn + 1) % len(self.players)

        session.commit()

    def end_round(self, session: Session) -> Tuple[str, List[Tuple[int, str]]]:
        """Gives the winner the winnings, returns index/name of winner(s); more than 1 means tie
        
        If tie, instead multiply bet by 3, or 9 on 21 tie

        Return win condition string for special dialogue; n = norm, b = blackjack, f = five card charlie
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
    """Represents a player of Blackjack.
    
    ### Attributes

    ### Methods
    """ #TODO

    __tablename__ = "blackjack_player"
    __table_args__ = (
        ForeignKeyConstraint(["user_id", "game_id"], ["player.user_id", "player.game_id"]),
        )
    

    user_id: Mapped[int] = mapped_column(primary_key = True)
    """User ID of the player"""

    game_id: Mapped[int] = mapped_column(primary_key = True)
    """ID of the game the Player is playing in"""

    hand: Mapped[str] = mapped_column(default = "[]")
    """Jsonified list of cards within player's hand"""

    state: Mapped[str] = mapped_column(default = "hit")
    """Either 'hit', 'stand', or 'bust'; represents state of player's hand"""

    __mapper_args__ = {
        "polymorphic_identity": "blackjack"
    }

    def get_hand(self) -> List[int]:
        """Parses hand to list of ints"""

        return loads(self.hand)
    
    def stand(self, session: Session) -> None:
        """Blackjack player stands"""

        self.state = "stand"
        session.commit()
    
    def add_card(self, session: Session, card: int) -> bool:
        """Adds card to hand; returns whether still un-busted"""

        hand: List[int] = loads(self.hand)
        hand.append(card)
        self.hand = dumps(hand)

        # Calculate hand value
        hand_value = self.hand_value()
        if hand_value == 0:
            self.state == "bust"

        session.commit()
        return bool(hand_value)

    def hand_value(self) -> int:
        """Calculates the value of the hand for direct comparison
        
        0 is bust
        22 is 5-card charlie
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