"""Contains miscellaneous functions/objects used in other modules"""

print("Loading module 'auxiliary'...")

from datetime import datetime
from json import load

from discord import ApplicationContext

class InvalidArgumentError(Exception):
    pass

with open("settings/perms.json", "r") as file:
    perms: dict[str, list[int]] = load(file)
    """Contains all permission groups used by several commands"""

with open("settings/guilds.json", "r") as file:
    guilds: list[int] = load(file)
    """Contains all guild ids that the bot is to be used in"""

with open("settings/localization_en.json", "r") as file:
    loc_en: dict[str, str] = load(file)
    """Contains log/response messages localization in English"""

def loc(id: str, *ins, loc_used: dict[str, str | list] = loc_en):
    """Retrieves a predefined localized string and inserts string values in like f-strings.

    Inside string, {} refers to extra arguments sequentially.

    Missing arguments are replaced with empty string.

    ### Parameters
    id: str
        The id of the localized string to retrieve
    ins: Tuple
        List of extra arguments to insert into localized string.
    loc_used: dict[str, str | list]
        The loaded localization file to use; defaults to English

    ### Returns
    Single string with arguments inserted if applicable.
    
    ### Raises
    InvalidArgumentError if invalid ID.
    """
    
    if (found_loc := loc_used.get(id)) is None:
        raise InvalidArgumentError
    
    out = found_loc.split("{}")
    for arg in enumerate(ins):
        # Test to see if too many extra arguments
        i = arg[0] * 2 + 1
        if i >= len(out):
            break
        out.insert(i, str(arg[1]))

    out = "".join(out)

    return out

def loc_arr(id: str, val: int, loc_used: dict[str, str | list] = loc_en):
    """Retrieves a predefined localized string from within an array.

    ### Parameters
    id: str
        The id of the localized array to retrieve
    val: int
        The id of the string within the array to retrieve
    loc_used: dict[str, str | list]
        The loaded localization file to use; defaults to English

    ### Returns
    Single string retrieved.
    
    ### Raises
    InvalidArgumentError if invalid ID or val.
    """
    
    if (found_loc := loc_used.get(id)) is None:
        raise InvalidArgumentError
    
    if type(found_loc) == str:
        raise InvalidArgumentError
    
    if val >= len(found_loc):
        raise InvalidArgumentError
    
    return found_loc[val]

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

    with open("logs/" + datetime.now().strftime("%Y-%m-%d") + ".txt", "a", encoding = "utf-8") as log_file:
        log_file.write(out + "\n")

async def ghost_reply(context: ApplicationContext, message: str, private: bool = False) -> None:
    """Reply to a message without the command reply being visible to everyone else
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    message: str
        The message to send
    private: bool = False
        Whether the reply should only be visible to the user
    """
    if private:
        await context.respond(message, ephemeral = True)
    else:
        await context.respond("https://canary.discordapp.com/__development/link/", ephemeral = True, delete_after = 0)
        await context.channel.send(message)

def clamp(arr: list[int | float], max: list[int | float]) -> None:
    """Clamp each value in a list to those in another list.
    
    ### Parameters
    arr: list[int | float]
        The list to clamp (MODIFIED IN-PLACE)
    max: list[int | float]
        The list of maximum values

    ### Raises
    InvalidArgumentError
        Lists are not the same length
    """

    if len(arr) != len(max):
        raise InvalidArgumentError
    
    for i in range(len(arr)):
        if arr[i] > max[i]:
            arr[i] = max[i]

def all_zero(arr: list[int]) -> bool:
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