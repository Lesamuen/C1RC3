"""Contains all SQLAlchemy ORM models"""

from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta

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

    add_chips(session: Session, chip: int) -> None
        Adds a number of chips to user's currency
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
        
    def create_account(self, session: Session, username: str, name: str) -> bool:
        """Tries to open a chip account under the given username

        ### Parameters
        session: Session
            Database session scope

        username: str
            Username of the new account

        name: str
            In-character name that the account is going under

        ### Returns
        True on success, False if account already existed.
        """

        found_account = session.execute(
            select(ChipAccount)
            .where(ChipAccount.username == username)
            ).scalar()
        
        if found_account is None:
            # Create new account
            new_account = ChipAccount(owner_id = self.id, username = username, name = name)
            session.add(new_account)
            session.commit()
            return True
        else:
            return False

class ChipAccount(SQLBase):
    # TODO
    """Represents a chips account belonging to a single character.

    ### Attributes
        
    ### Methods
    
    """

    __tablename__ = "account"

    username: Mapped[str] = mapped_column(primary_key = True)
    """Unique username of the account; no two characters can have the same account, even under different users"""

    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete = "CASCADE"))
    """ID of User who owns this account"""

    owner: Mapped["User"] = relationship(back_populates = "accounts")
    """Direct reference to User who owns this account"""

    name: Mapped[str]
    """Given name of character that owns this account"""
    
    chips: Mapped[int] = mapped_column(default = 0)
    """How many chips the account contains"""

    @staticmethod
    def find_account(session: Session, username: str) -> "ChipAccount | None":
        """Returns the ChipAccount if it exists
        
        ### Parameters
        session: Session
            Database session scope

        username: str
            Username to search for

        ### Returns
        ChipAccount with matching username or None if not found.
        """

        return session.execute(
            select(ChipAccount)
            .where(ChipAccount.username == username)
            ).scalar()
    
    def deposit(self, session: Session, amount: int) -> None:
        """Deposit an amount of chips into the account

        ### Parameters
        session: Session
            Database session scope

        amount: int
            Amount of chips to add to the balance

        ### Throws
        InvalidArgumentError
            Amount given is negative
        """

        if amount < 0:
            raise InvalidArgumentError
        
        self.chips += amount
        session.commit()
    
    def withdraw(self, session: Session, amount: int) -> bool:
        """Withdraw an amount of chips from the account

        ### Parameters
        session: Session
            Database session scope

        amount: int
            Amount of chips to take from the balance

        ### Returns
        True if successful, False if there were not enough chips in the account

        ### Throws
        InvalidArgumentError
            Amount given is negative
        """

        if amount < 0:
            raise InvalidArgumentError

        if amount > self.chips:
            return False
        
        self.chips -= amount
        session.commit()

        return True

    def changename(self, session: Session, new: str) -> None:
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