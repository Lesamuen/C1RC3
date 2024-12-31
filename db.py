"""Directly runs database-related commands; use for structure changes and data migration"""

import sqlite3
from traceback import format_exception

import modules.base.bot as bot
import modules.base.dbmodels as dbmodels

#bot.db_update()

db = sqlite3.connect("database/dbedit.sqlite")
c = db.cursor()

stmts = [
    #"SELECT * FROM col",
    #"ALTER TABLE table ADD COLUMN col VARCHAR NOT NULL DEFAULT 'something'",
    #"SELECT * FROM col",
]

for stmt in stmts:
    try:
        print(c.execute(stmt).fetchall())
    except Exception as err:
        print("".join(format_exception(err)))
