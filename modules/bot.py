"""Contains global bot object & Database connection manager"""

print("Loading module 'bot'...")

import discord
import discord.ext.commands as discomm
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Global bot object
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot_client = discomm.Bot(intents = intents)
"""Main bot object"""


# Database stuff (SQLite and SQLAlchemy)
database_engine = create_engine("sqlite:///database/db.sqlite")
database_connector = sessionmaker(database_engine, autocommit = False, autoflush = False)
"""To use, do \"with database_connector() as session:\""""

class SQLBase(DeclarativeBase):
    """Used for all SQLAlchemy ORM classes"""
    pass

def db_init() -> None:
    """Reset the database. Call this only once per structure change."""

    SQLBase.metadata.drop_all(database_engine)
    SQLBase.metadata.create_all(database_engine)