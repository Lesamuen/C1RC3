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
    [PRIMARY] id: str
        Corresponds to Discord user ID

    chips: int
        Currency for the casino, per user
        
    ### Methods
    [STATIC] find_user(session: Session, id: str) -> User
        Returns the User object corresponding to the given Discord ID

    add_chips(session: Session, chip: int) -> None
        Adds a number of chips to user's currency
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key = True)
    """Corresponds to Discord user ID"""
    chips: Mapped[int] = mapped_column(default = 0)
    """Currency for this bot, per user"""

    @staticmethod
    def find_user(session: Session, id: int) -> 'User':
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

    def add_chips(self, session: Session, chips: int) -> None:
        """Adds a number of chips to user's currency

        ### Parameters
        session: Session
            Database session scope

        chips: int
            Amount of chips to add or remove (if negative) from account

        ### Throws
        InvalidArgumentError
            Chips to remove is larger than amount of chips available
        """

        if -chips > self.chips:
            raise InvalidArgumentError
        
        self.chips += chips
        session.commit()
