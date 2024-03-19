"""Contains miscellaneous functions used in most cases"""

from datetime import datetime
from json import load
from typing import Dict, List, Any

from discord import ApplicationContext

class InvalidArgumentError(Exception):
    pass

with open("settings/perms.json", "r") as file:
    perms: Dict[str, List[int]] = load(file)
    """Contains all permission groups used by several commands"""

with open("settings/guilds.json", "r") as file:
    guilds: List[int] = load(file)
    """Contains all guild ids that the bot is to be used in"""

def get_time() -> str:
    """Return the current system time in extended ISO8601 format; 20 chars long"""

    return datetime.now().strftime("%Y-%m-%d, %H:%M:%S")

def log(out: str) -> None:
    """Both prints the input string to the console and writes the input string to a dated log.

    This log is found in the logs/ folder (the logs folder has to be created first).

    ### Parameters
    out: str
        String to print to file and console
    """

    print(out)

    with open("logs/" + datetime.now().strftime("%Y-%m-%d") + ".txt", "a") as log_file:
        log_file.write(out + "\n")

async def ghost_reply(context: ApplicationContext, message: str) -> None:
    """Reply to a message without the command reply actually showing up
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    message: str
        The message to send
    """

    await context.respond("https://canary.discordapp.com/__development/link/", ephemeral = True, delete_after = 0)
    await context.channel.send(message)

def all_zero(arr: List[int]) -> bool:
    """Check if a list of integers contains nothing but 0's.
    
    ### Parameters
    arr: list[int]
        The list of integers to be tested

    ### Returns
    True
        Every value is 0
    False
        At least one value is nonzero
    """

    for num in arr:
        if num != 0:
            return False

    return True