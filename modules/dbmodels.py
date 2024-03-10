"""Contains all SQLAlchemy ORM models"""

from typing import List, Optional, Tuple, Dict
from json import dumps, loads

from sqlalchemy import ForeignKey, select, insert, update, delete
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from bot import SQLBase
from auxiliary import InvalidArgumentError


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

    accounts: Mapped[List["ChipAccount"]] = relationship(back_populates = "owner", cascade = "all, delete-orphan", passive_deletes = True)
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
