"""Main bot application file to run directly with Python"""

from traceback import format_exception
from time import sleep

# Load environment
import discord

print("\nRunning PyCord version " + discord.__version__)
try:
    with open("settings/bottoken.txt") as file:
        bot_token = file.read()
except OSError:
    print("\nBot token not found!\nTerminating program...")
    quit()
else:
    print("\nBot token found!")

# Creates certain empty folders if necessary
from os.path import exists
from os import mkdir
if exists("database"):
    print("Database folder found!")
else:
    print("Database folder not found!\nCreating new folder...")
    mkdir("database")

if exists("database/db.sqlite"):
    print("Database found!")
else:
    print("Database not found!\nPlease run modules.bot.db_init() in a separate script.")
    quit()

if exists("logs"):
    print("Logs folder found!")
else:
    print("Logs folder not found!\nCreating new folder...")
    mkdir("logs")

if exists("settings/perms.json"):
    print("Permissions settings found!")
else:
    print("Permissions file not found!\nTerminating...")
    quit()

# Import all modules, setting up event listeners
from modules.base.bot import bot_client
from modules.base.auxiliary import log, get_time
import modules.misc.chips
import modules.games.miscgame
import modules.games.blackjack
import modules.games.tourney

print("All bot modules successfully loaded!\n")

# Initialize bot loop

while True:
    try:
        log(get_time() + " >> Initializing connection to Discord...")
        bot_client.run(bot_token)
    except Exception as err:
        log(get_time() + " >> UNEXPECTED ERROR occurred during bot loop; bot has closed!")
        log("".join(format_exception(err)))
        log("                     >> Relaunching bot in 5 minutes...")
        sleep(300)