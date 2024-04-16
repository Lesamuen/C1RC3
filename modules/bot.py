"""Contains global bot object & Database connection manager"""

print("Loading module 'bot'...")

import discord
import discord.ext.commands as discomm
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from auxiliary import log, get_time

# Global bot object
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot_client = discomm.Bot(intents = intents)
"""Main bot object"""

@bot_client.listen()
async def on_ready():
    log(get_time() + " >> Successfully logged in as " + str(bot_client.user))
@bot_client.listen()
async def on_disconnect():
    log(get_time() + " >> Lost connection to Discord!")
@bot_client.listen()
async def on_connect():
    log(get_time() + " >> Connected to Discord!")
@bot_client.listen()
async def on_application_command_error(ctx, exc):
    # Suppress admin fail checks
    return


# Database stuff (SQLite and SQLAlchemy)
database_engine = create_engine("sqlite:///database/db.sqlite")
database_connector = sessionmaker(database_engine, autocommit = False, autoflush = False)
"""To use, call database_connector to create session."""

class SQLBase(DeclarativeBase):
    """Used for all SQLAlchemy ORM classes"""
    pass

def db_reset() -> None:
    """Reset the database. Call this only once per structure change."""

    SQLBase.metadata.drop_all(database_engine)
    SQLBase.metadata.create_all(database_engine)

def db_update() -> None:
    """Adds tables not already present in database"""

    SQLBase.metadata.create_all(database_engine)