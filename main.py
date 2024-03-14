"""Main bot application file to run directly with Python"""

# Allows for other .py files to be found in /modules folder
from sys import path as syspath
syspath.append(syspath[0] + "\\modules")

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
    print("Database not found!\nPlease run bot.db_init() in a separate script.")
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
from bot import bot_client
from auxiliary import log, get_time
import dbmodels
import admin
import chips
import game
import blackjack

print("\nAll bot modules successfully loaded!\nNow initiating connection to Discord servers...")

# Initialize bot loop
@bot_client.listen()
async def on_ready():
    log("\n" + get_time() + " >> Successfully logged in as " + str(bot_client.user) + "\n")
@bot_client.listen()
async def on_disconnect():
    log("\n" + get_time() + " >> Lost connection to Discord!\n")
@bot_client.listen()
async def on_connect():
    log("\n" + get_time() + " >> Connected to Discord!\n")
@bot_client.listen()
async def on_application_command_error(ctx, exc):
    # Suppress admin fail checks
    return

bot_client.run(bot_token)