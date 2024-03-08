"""Directly runs database-related commands; use for structure changes and data migration"""

from sys import path as syspath
syspath.append(syspath[0] + "\\modules")

import bot
import dbmodels

bot.db_init()