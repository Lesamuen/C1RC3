"""Directly runs database-related commands; use for structure changes and data migration"""

import sqlite3
from traceback import format_exception
from sys import path as syspath
syspath.append(syspath[0] + "\\modules")

import bot
import dbmodels

#bot.db_update()

db = sqlite3.connect("database/dbedit.sqlite")
c = db.cursor()

stmts = [
    #"SELECT * FROM game",
    #"ALTER TABLE game ADD COLUMN bet_turn INTEGER NOT NULL DEFAULT 0",
]

for stmt in stmts:
    try:
        print(c.execute(stmt).fetchall())
    except Exception as err:
        print("".join(format_exception(err)))
