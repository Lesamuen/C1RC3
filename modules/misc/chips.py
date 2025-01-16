"""This module helps keeps track of user's global out-of-game chips."""

print("Loading module 'chips'...")

from discord import ApplicationContext, option

from ..base.bot import bot_client, database_connector
from ..base.auxiliary import guilds, log, loc, get_time, all_zero, ghost_reply
from ..base.dbmodels import ChipAccount
from ..base.emojis import format_chips

chip_cmds = bot_client.create_group("chip", "Commands related to chip-holding accounts out of game", guild_ids = guilds)

@chip_cmds.command(name = "open_account", description = "Open an account for you to keep track of the chips you've won from tables.")
@option("name", str, description = "The name of the character holding the account", min_length = 1, max_length = 50)
@option("private", bool, description = "Whether to keep the response only visible to you")
async def open_account(context: ApplicationContext, name: str, private: bool):
    """Add the command /chip open_account
    
    Create a chips holding account
    """

    session = database_connector()

    success: bool = ChipAccount.create_account(session, context.author.id, name)

    if success:
        log(loc("chips.open.log", get_time(), context.guild, context.channel, context.author, name))
        await ghost_reply(context, loc("chips.open", name), private)
    else:
        log(loc("chips.open.dupe.log", get_time(), context.guild, context.channel, context.author, name))
        await ghost_reply(context, loc("chips.open.dupe", name), True)

    session.close()

@chip_cmds.command(name = "change_name", description = "Update the holder's name on an account.")
@option("name", str, description = "The original name of the casino account", min_length = 1, max_length = 50)
@option("new_name", str, description = "The new name of the account", min_length = 1, max_length = 50)
@option("private", bool, description = "Whether to keep the response only visible to you")
async def change_name(context: ApplicationContext, name: str, new_name: str, private: bool):
    """Add the command /chip change_name
    
    Change name of chip account
    """

    session = database_connector()

    # Attempt to retrieve account
    account = ChipAccount.find_account(session, name)
    if account is None:
        log(loc("chips.none.log", get_time(), context.guild, context.channel, context.author, name))
        await ghost_reply(context, loc("chips.none"), True)
        session.close()
        return
    
    # Check if name isn't changing
    if name == new_name:
        log(loc("chips.name.same.log", get_time(), context.guild, context.channel, context.author, name))
        await ghost_reply(context, loc("chips.name.same"), True)
        session.close()
        return

    # Check if account with new name already exists
    if ChipAccount.find_account(session, new_name):
        log(loc("chips.name.dupe.log", get_time(), context.guild, context.channel, context.author, name, new_name))
        await ghost_reply(context, loc("chips.dupe", new_name), True)
        session.close()
        return

    # Check if account doesn't belong to the person sending the command
    if account.owner_id != context.author.id:
        log(loc("chips.name.other.log", get_time(), context.guild, context.channel, context.author, name))
        await ghost_reply(context, loc("chips.other"), True)
        session.close()
        return

    log(loc("chips.name.log", get_time(), context.guild, context.channel, context.author, name, new_name))
    account.change_name(session, new_name)
    await ghost_reply(context, loc("chips.name", name, new_name), private)
    session.close()

@chip_cmds.command(name = "balance", description = "Check how many chips you have in an account.")
@option("name", str, description = "The name the account is under", min_length = 1, max_length = 50)
@option("private", bool, description = "Whether to keep the response only visible to you")
async def balance(context: ApplicationContext, name: str, private: bool):
    """Add the command /chip balance
    
    Check balance of chip account
    """

    session = database_connector()

    # Attempt to retrieve account
    account = ChipAccount.find_account(session, name)
    if account is None:
        log(loc("chips.none.log", get_time(), context.guild, context.channel, context.author, name))
        await ghost_reply(context, loc("chips.none"), True)
        session.close()
        return

    # Check if account belongs to the person sending the command
    if account.owner_id != context.author.id:
        log(loc("chips.bal.other.log", get_time(), context.guild, context.channel, context.author, name))
        await ghost_reply(context, loc("chips.other"), True)
        session.close()
        return

    log(loc("chips.bal.log", get_time(), context.guild, context.channel, context.author, name))
    await ghost_reply(context, loc("chips.bal", name, format_chips(account.get_bal())), private)

    session.close()

@chip_cmds.command(name = "deposit", description = "Deposit an amount of chips into an account.")
@option("name", str, description = "The name the account is under", min_length = 1, max_length = 50)
@option("private", bool, description = "Whether to keep the response only visible to you")
@option("physical", int, description = "The amount of physical chips to deposit", min_value = 0, default = 0)
@option("mental", int, description = "The amount of mental chips to deposit", min_value = 0, default = 0)
@option("artificial", int, description = "The amount of artificial chips to deposit", min_value = 0, default = 0)
@option("supernatural", int, description = "The amount of supernatural chips to deposit", min_value = 0, default = 0)
@option("merge", int, description = "The amount of merge chips to deposit", min_value = 0, default = 0)
@option("swap", int, description = "The amount of swap chips to deposit", min_value = 0, default = 0)
async def deposit(context: ApplicationContext, name: str, private: bool, physical: int, mental: int, artificial: int, supernatural: int, merge: int, swap: int):
    """Add the command /chip deposit
    
    Add chips to chip account
    """

    # Grab chip params
    chips: list[int] = list(locals().values())[3:9]

    # If every single parameter is 0
    if all_zero(chips):
        log(loc("chips.depo.zero.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("chips.depo.zero"), True)
        return

    session = database_connector()

    # Attempt to retrieve account
    account = ChipAccount.find_account(session, name)
    if account is None:
        log(loc("chips.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("chips.none"), True)

    # Check if account belongs to the person sending the command
    if account.owner_id != context.author.id:
        log(loc("chips.depo.other.log", get_time(), context.guild, context.channel, context.author, name))
        await ghost_reply(context, loc("chips.other"), True)
        session.close()
        return
    
    log(loc("chips.depo.log", get_time(), context.guild, context.channel, context.author, chips, name))
    
    account.deposit(session, chips)

    await ghost_reply(context, loc("chips.depo", name, format_chips(account.get_bal())), private)

    session.close()

@chip_cmds.command(name = "withdraw", description = "Withdraw an amount of chips from an account.")
@option("name", str, description = "The name the account is under", min_length = 1, max_length = 50)
@option("private", bool, description = "Whether to keep the response only visible to you")
@option("physical", int, description = "The amount of physical chips to withdraw", min_value = 0, default = 0)
@option("mental", int, description = "The amount of mental chips to withdraw", min_value = 0, default = 0)
@option("artificial", int, description = "The amount of artificial chips to withdraw", min_value = 0, default = 0)
@option("supernatural", int, description = "The amount of supernatural chips to withdraw", min_value = 0, default = 0)
@option("merge", int, description = "The amount of merge chips to withdraw", min_value = 0, default = 0)
@option("swap", int, description = "The amount of swap chips to withdraw", min_value = 0, default = 0)
async def withdraw(
    context: ApplicationContext, name: str, private: bool, physical: int, mental: int, artificial: int, supernatural: int, merge: int, swap: int):
    """Add the command /chip withdraw
    
    Remove chips from chip account
    """

    # Grab chip params
    chips: list[int] = list(locals().values())[3:9]

    # If every single parameter is 0
    if all_zero(chips):
        log(loc("chips.with.zero.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("chips.with.zero"), True)
        return

    session = database_connector()

    # Attempt to retrieve account
    account = ChipAccount.find_account(session, name)
    if account is None:
        log(loc("chips.none.log", get_time(), context.guild, context.channel, context.author, name))
        await ghost_reply(context, loc("chips.none"), True)
        session.close()
        return

    # Check if account belongs to the person sending the command
    if account.owner_id != context.author.id:
        log(loc("chips.with.other.log", get_time(), context.guild, context.channel, context.author, name))
        await ghost_reply(context, loc("chips.other"), True)
        session.close()
        return

    success: bool = account.withdraw(session, chips)

    if not success:
        log(loc("chips.with.fail.log", get_time(), context.guild, context.channel, context.author, name))
        await ghost_reply(context, loc("chips.with.fail"), True)
    else:
        log(loc("chips.with.log", get_time(), context.guild, context.channel, context.author, chips, name))

        await ghost_reply(context, loc("chips.with", name, format_chips(account.get_bal())), private)

    session.close()