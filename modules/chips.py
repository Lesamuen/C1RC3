"""This module helps keeps track of user's global out-of-game chips."""

from discord import ApplicationContext, Option
from discord import User as DiscordUser

from bot import bot_client, database_connector
from auxiliary import perms, guilds, log, get_time
from dbmodels import User, ChipAccount

def validate_account_name(name: str) -> bool:
    """Tests for a valid account name. Alphanumeric with hyphens or underscores; first char alphabetical"""
    if not name[0].isalpha():
        return False
    for char in name:
        if not char.isalnum() and char != "-" and char != "_":
            return False

    return True

@bot_client.slash_command(name = "open_account", description = "Open an account for you to hold your chips.", guild_ids = guilds, guild_only = True)
async def open_account(
    context: ApplicationContext,
    account_name: Option(str, description = "The username of the new account (alphanumeric with hyphens or underscores, first char alphabetical)", required = True, min_length = 1),
    holder_name: Option(str, description = "The current name of the soul who will own the account", required = True, min_length = 1)
):
    """Adds the command /open_account"""

    if not validate_account_name(account_name):
        log(get_time() + " >> " + str(context.author) + " tried to open an invalid account in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond("*C1RC3 shakes her head.* \"Request denied. The account name '" + account_name + "' does not meet specifications.\"")
        return

    session = database_connector()

    user: User = User.find_user(session, context.author.id)

    log(get_time() + " >> " + str(context.author) + " opened the account \"" + account_name + "\" under the name \"" + holder_name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")

    success: bool = user.create_account(session, account_name, holder_name)

    if success:
        await context.respond("*C1RC3 nods.* \"Request accepted and processed. The account '" + account_name + "' has been opened under the name '" + holder_name + "'.\"")
    else:
        await context.respond("*C1RC3 shakes her head.* \"Request denied. The account '" + account_name + "' has already been registered.\"")
        log("             [ERROR] >> Account already exists.")

    session.close()

@bot_client.slash_command(name = "update_name", description = "Update the holder's name on an account.", guild_ids = guilds, guild_only = True)
async def update_name(
    context: ApplicationContext,
    account_name: Option(str, description = "The username of the casino account", required = True, min_length = 1),
    holder_name: Option(str, description = "The new name of the soul owns the account", required = True, min_length = 1)
):
    """Adds the command /update_name"""

    session = database_connector()

    # Attempt to retrieve account
    account = ChipAccount.find_account(session, account_name)
    if account is None:
        log(get_time() + " >> " + str(context.author) + " failed to find account \"" + account_name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond("*C1RC3 pauses for a brief moment as she scans her records.* \"Request failed. That account does not exist.\"")
        session.close()
        return

    # Check if name is the same
    if account.name == holder_name:
        log(get_time() + " >> " + str(context.author) + " didn't change name of account \"" + account_name + "\" at all in ["
             + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond("*C1RC3 freezes as she tries to process the request.* \"Request...failed...\" *She seems uncertain.* \"That is already the name your account is under.\"")
        session.close()
        return

    # Check if account belongs to the person sending the command
    if account.owner_id == context.author.id:
        log(get_time() + " >> " + str(context.author) + " changed name of account \"" + account_name + "\" from \"" + account.name
             + "\" to \"" + holder_name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        account.changename(session, holder_name)
        await context.respond("*C1RC3 nods as she edits her internal records.* \"Request approved. The account '" + account_name + "' is now under the name '" + holder_name + "'.\"")
    else:
        log(get_time() + " >> " + str(context.author) + " tried to change name of other's account \"" + account_name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond("*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes red for a moment.* \"Request denied. This account does not belong to you.\"")

    session.close()

@bot_client.slash_command(name = "check_account", description = "Check how many chips you have in an account.", guild_ids = guilds, guild_only = True)
async def check(
    context: ApplicationContext,
    account_name: Option(str, description = "The username of the casino account", required = True, min_length = 1)
):
    """Adds the command /check_account"""

    session = database_connector()

    # Attempt to retrieve account
    account = ChipAccount.find_account(session, account_name)
    if account is None:
        log(get_time() + " >> " + str(context.author) + " failed to find account \"" + account_name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond("*C1RC3 pauses for a brief moment as she scans her records.* \"Request failed. That account does not exist.\"")
        session.close()
        return

    # Check if account belongs to the person sending the command
    if account.owner_id == context.author.id:
        log(get_time() + " >> " + str(context.author) + " checked their account \"" + account_name
             + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond("*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes green for a moment.* \"Request approved. The account '"
             + account_name + "' under '" + account.name + "' currently contains " + str(account.chips) + " <:chip1:1216075094947004617>.\"")
    else:
        log(get_time() + " >> " + str(context.author) + " tried to access other's account \"" + account_name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond("*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes red for a moment.* \"Request denied. This account does not belong to you.\"")

    session.close()

@bot_client.slash_command(name = "deposit", description = "Deposit an amount of chips into an account.", guild_ids = guilds, guild_only = True)
async def deposit(
    context: ApplicationContext,
    account_name: Option(str, description = "The username of the casino account", required = True, min_length = 1),
    amount: Option(int, description = "The amount of chips to deposit", required = True, min_value = 1)
):
    """Adds the command /deposit"""

    session = database_connector()

    # Attempt to retrieve account
    account = ChipAccount.find_account(session, account_name)
    if account is None:
        log(get_time() + " >> " + str(context.author) + " failed to find account \"" + account_name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond("*C1RC3 pauses for a brief moment as she scans her records.* \"Request failed. That account does not exist.\"")
        session.close()
        return

    # Check if account belongs to the person sending the command
    if account.owner_id == context.author.id:
        log(get_time() + " >> " + str(context.author) + " added " + str(amount) + " chips to account \"" + account_name
             + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        account.deposit(session, amount)
        await context.respond("\"Request approved.\" *The chips you are holding gently glow before evaporating into golden light that shoots over to C1RC3, infusing into her. Her body quivers with pleasure, but she shows no emotion in her automated state.* \"The account '"
             + account_name + "' under '" + account.name + "' now contains " + str(account.chips) + " <:chip1:1216075094947004617>.\"")
    else:
        log(get_time() + " >> " + str(context.author) + " tried to access other's account \"" + account_name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond("*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes red for a moment.* \"Request denied. This account does not belong to you.\"")

    session.close()

@bot_client.slash_command(name = "withdraw", description = "Withdraw an amount of chips from an account.", guild_ids = guilds, guild_only = True)
async def withdraw(
    context: ApplicationContext,
    account_name: Option(str, description = "The username of the casino account", required = True, min_length = 1),
    amount: Option(int, description = "The amount of chips to withdraw", required = True, min_value = 1)
):
    """Adds the command /withdraw"""

    session = database_connector()

    # Attempt to retrieve account
    account = ChipAccount.find_account(session, account_name)
    if account is None:
        log(get_time() + " >> " + str(context.author) + " failed to find account \"" + account_name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond("*C1RC3 pauses for a brief moment as she scans her records.* \"Request failed. That account does not exist.\"")
        session.close()
        return

    # Check if account belongs to the person sending the command
    if account.owner_id == context.author.id:
        log(get_time() + " >> " + str(context.author) + " added " + str(amount) + " chips to account \"" + account_name
             + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        success: bool = account.withdraw(session, amount)
        if success:
            await context.respond("\"Request approved.\" *C1RC3 suddenly begins to glow with golden light as the magical energy within her condenses. A hidden compartment within her midriff suddenly slides open, revealing a pile of fresh <:chip1:1216075094947004617> for you to take.* \"The account '"
                + account_name + "' under '" + account.name + "' now contains " + str(account.chips) + " <:chip1:1216075094947004617>.\"")
        else:
            await context.respond("*C1RC3 pauses for a brief moment as she checks her records.* \"Request denied. The account '" + account_name + "' does not have enough <:chip1:1216075094947004617> to withdraw.\"")
    else:
        log(get_time() + " >> " + str(context.author) + " tried to access other's account \"" + account_name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond("*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes red for a moment.* \"Request denied. This account does not belong to you.\"")

    session.close()