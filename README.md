## General Info
This is the code for a discord bot in Python3.11 using Pycord.

The bot's main functionality is to automate games for a public casino RP server. Some parts of the bot may not make sense without the context of the server, but I will not disclose which server the bot is for.

## Current Python Dependencies
py-cord
SQLAlchemy

## Pre-Use Steps
- Bot has been tested on Windows and Linux, but not on MacOS.
- Run db_update() or db_reset() from modules/bot.py in db.py to initialize the database
- Put bot token in settings/bottoken.txt
- Fill out Discord user IDs in settings/perms.json for admin privileges
- Fill out Discord server ID(s) in settings/guilds.json