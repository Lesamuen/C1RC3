"""Contains global bot object & Database connection manager"""

print("Loading module 'bot'...")

from traceback import format_exception

import discord
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .auxiliary import log, get_time, loc

# Global bot object
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot_client = discord.Bot(intents = intents)
"""Main bot object"""

@bot_client.listen()
async def on_ready():
    log(loc("bot.login", get_time(), bot_client.user))
# @bot_client.listen()
# async def on_disconnect():
#     log(loc("bot.disconnect", get_time()))
@bot_client.listen()
async def on_connect():
    log(loc("bot.reconnect", get_time()))
@bot_client.listen()
async def on_application_command_error(context: discord.ApplicationContext, exception: discord.DiscordException):
    log(loc("error.log", get_time(), context.guild, context.channel, context.author, "".join(format_exception(exception))))
    await context.respond(loc("error"))


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