"""This module helps keeps track of user's global out-of-game chips."""

from typing import List

from discord import ApplicationContext, Option

from bot import bot_client, database_connector
from auxiliary import guilds, log, get_time
from dbmodels import User, ChipAccount

chip_emojis: List[str] = [
    "<:chip1:1216075094947004617>",
    "<:chip2:1216075127481962606>",
    "<:chip3:1216075181898993664>",
    "<:chip4:1216075196763734027>",
    "<:chip5:1216075227726086305>",
    "<:chip6:1216075286005813338>"
]

@bot_client.slash_command(name = "open_account", description = "Open an account for you to hold your chips.", guild_ids = guilds, guild_only = True)
async def open_account(
    context: ApplicationContext,
    name: Option(str, description = "The name of the person holding the account", required = True, min_length = 1)
):
    """Adds the command /open_account"""

    session = database_connector()

    user: User = User.find_user(session, context.author.id)

    success: bool = user.create_account(session, name)

    if success:
        log(get_time() + " >> " + str(context.author) + " opened an account under the name \"" + name
             + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*C1RC3 nods.* \"Request accepted and processed. An account has been opened under the name '" + name + "'.\"")
    else:
        log(get_time() + " >> " + str(context.author) + " tried to open a duplicate account under the name \"" + name + "\" in ["
             + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*C1RC3 shakes her head.* \"Request denied. An account already exists under the name '" + name + "'.\"")

    session.close()

@bot_client.slash_command(name = "change_name", description = "Update the holder's name on an account.", guild_ids = guilds, guild_only = True)
async def change_name(
    context: ApplicationContext,
    name: Option(str, description = "The original name of the casino account", required = True, min_length = 1),
    new_name: Option(str, description = "The new name of the account", required = True, min_length = 1)
):
    """Adds the command /change_name"""

    session = database_connector()

    # Attempt to retrieve account
    account = ChipAccount.find_account(session, name)
    if account is None:
        log(get_time() + " >> " + str(context.author) + " failed to find account \"" + name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*C1RC3 pauses for a brief moment as she scans her records.* \"Request failed. No account exists under that name.\"")
        session.close()
        return
    
    # Check if name isn't changing
    if name == new_name:
        log(get_time() + " >> " + str(context.author) + " didn't change name of account \"" + name + "\" at all in ["
             + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*C1RC3 freezes as she tries to process the request.* \"Request...failed...\" *She seems uncertain.* \"That is already the name your account is under.\"")
        session.close()
        return

    # Check if account with new name already exists
    if ChipAccount.find_account(session, new_name):
        log(get_time() + " >> " + str(context.author) + " failed to change name of account \"" + name + "\" in ["
             + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*C1RC3 pauses for a brief moment as she scans her records.* \"Request failed. An account already exists under the name '" + new_name + "'.\"")
        session.close()
        return

    # Check if account belongs to the person sending the command
    if account.owner_id == context.author.id:
        log(get_time() + " >> " + str(context.author) + " changed name of account \"" + name + "\" to \"" + new_name
             + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        account.change_name(session, new_name)
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes green for a moment.* \"Request approved. The account under '" + name + "' is now under the name '" + new_name + "'.\"")
    else:
        log(get_time() + " >> " + str(context.author) + " tried to change name of other's account \"" + name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes red for a moment.* \"Request denied. This account does not belong to you.\"")

    session.close()

@bot_client.slash_command(name = "balance", description = "Check how many chips you have in an account.", guild_ids = guilds, guild_only = True)
async def balance(
    context: ApplicationContext,
    name: Option(str, description = "The name the account is under", required = True, min_length = 1)
):
    """Adds the command /balance"""

    session = database_connector()

    # Attempt to retrieve account
    account = ChipAccount.find_account(session, name)
    if account is None:
        log(get_time() + " >> " + str(context.author) + " failed to find account \"" + name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*C1RC3 pauses for a brief moment as she scans her records.* \"Request failed. No account exists under that name.\"")
        session.close()
        return

    # Check if account belongs to the person sending the command
    if account.owner_id == context.author.id:
        log(get_time() + " >> " + str(context.author) + " checked their account \"" + name
             + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        
        await context.respond(".", ephemeral = True, delete_after = 0)
        response: str = "*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes green for a moment.* \"Request approved. The account under the name '" + account.name + "' currently contains:\"\n# "
        bal: List[int] = account.get_bal()

        # If no chips, say "no chips".
        no_chips = True
        for chips in bal:
            if chips != 0:
                no_chips = False
                break
        if no_chips:
            response += "no " + chip_emojis[0]
        else:
            # Chips exist, so go through every non-zero chip and list them
            for i in range(len(bal)):
                if bal[i] != 0:
                    response += str(bal[i]) + " " + chip_emojis[i] + ", "
            response = response.removesuffix(", ")

        await context.channel.send(response)
    else:
        log(get_time() + " >> " + str(context.author) + " tried to access other's account \"" + name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes red for a moment.* \"Request denied. This account does not belong to you.\"")

    session.close()

@bot_client.slash_command(name = "deposit", description = "Deposit an amount of chips into an account.", guild_ids = guilds, guild_only = True)
async def deposit(
    context: ApplicationContext,
    name: Option(str, description = "The name the account is under", required = True, min_length = 1),
    phys_chips: Option(int, description = "The amount of physical chips to deposit", required = True, min_value = 0, default = 0),
    ment_chips: Option(int, description = "The amount of mental chips to deposit", required = True, min_value = 0, default = 0),
    arti_chips: Option(int, description = "The amount of artificial chips to deposit", required = True, min_value = 0, default = 0),
    supe_chips: Option(int, description = "The amount of supernatural chips to deposit", required = True, min_value = 0, default = 0),
    merg_chips: Option(int, description = "The amount of merging chips to deposit", required = True, min_value = 0, default = 0),
    swap_chips: Option(int, description = "The amount of swap chips to deposit", required = True, min_value = 0, default = 0)
):
    """Adds the command /deposit"""

    # If every single parameter is 0
    if phys_chips == 0 and ment_chips == 0 and arti_chips == 0 and supe_chips == 0 and merg_chips == 0 and swap_chips == 0:
        log(get_time() + " >> " + str(context.author) + " tried to deposit nothing in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*C1RC3 freezes as she tries to process your inane request.* \"...Request accepted. You have achieved nothing.\"")
        return

    session = database_connector()

    # Attempt to retrieve account
    account = ChipAccount.find_account(session, name)
    if account is None:
        log(get_time() + " >> " + str(context.author) + " failed to find account \"" + name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*C1RC3 pauses for a brief moment as she scans her records.* \"Request failed. No account exists under that name.\"")
        session.close()
        return

    # Check if account belongs to the person sending the command
    if account.owner_id == context.author.id:
        log(get_time() + " >> " + str(context.author) + " deposited " + str(phys_chips) + "|" + str(ment_chips) + "|" + str(arti_chips) + "|" + str(supe_chips) + "|" + str(merg_chips) + "|" + str(swap_chips) 
             + " chips to their account \"" + name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        
        account.deposit(session, [phys_chips, ment_chips, arti_chips, supe_chips, merg_chips, swap_chips])

        await context.respond(".", ephemeral = True, delete_after = 0)
        response: str = "*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes green for a moment.* \"Request approved.\" *The chips you are holding gently glow before evaporating into golden light that shoots over to C1RC3, infusing into her. Her body quivers with pleasure, but she shows no emotion in her automated state.* \"Your account now contains:\"\n# "

        bal: List[int] = account.get_bal()

        # If no chips, say "no chips".
        no_chips = True
        for chips in bal:
            if chips != 0:
                no_chips = False
                break
        if no_chips:
            response += "no " + chip_emojis[0]
        else:
            # Chips exist, so go through every non-zero chip and list them
            for i in range(len(bal)):
                if bal[i] != 0:
                    response += str(bal[i]) + " " + chip_emojis[i] + ", "
            response = response.removesuffix(", ")

        await context.channel.send(response)
    else:
        log(get_time() + " >> " + str(context.author) + " tried to access other's account \"" + name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes red for a moment.* \"Request denied. This account does not belong to you.\"")

    session.close()

@bot_client.slash_command(name = "withdraw", description = "Withdraw an amount of chips from an account.", guild_ids = guilds, guild_only = True)
async def withdraw(
    context: ApplicationContext,
    name: Option(str, description = "The name the account is under", required = True, min_length = 1),
    phys_chips: Option(int, description = "The amount of physical chips to withdraw", required = True, min_value = 0, default = 0),
    ment_chips: Option(int, description = "The amount of mental chips to withdraw", required = True, min_value = 0, default = 0),
    arti_chips: Option(int, description = "The amount of artificial chips to withdraw", required = True, min_value = 0, default = 0),
    supe_chips: Option(int, description = "The amount of supernatural chips to withdraw", required = True, min_value = 0, default = 0),
    merg_chips: Option(int, description = "The amount of merging chips to withdraw", required = True, min_value = 0, default = 0),
    swap_chips: Option(int, description = "The amount of swap chips to withdraw", required = True, min_value = 0, default = 0)
):
    """Adds the command /withdraw"""

    # If every single parameter is 0
    if phys_chips == 0 and ment_chips == 0 and arti_chips == 0 and supe_chips == 0 and merg_chips == 0 and swap_chips == 0:
        log(get_time() + " >> " + str(context.author) + " tried to withdraw nothing in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*C1RC3 freezes as she tries to process your inane request.* \"...Request accepted. You have achieved nothing.\"")
        return

    session = database_connector()

    # Attempt to retrieve account
    account = ChipAccount.find_account(session, name)
    if account is None:
        log(get_time() + " >> " + str(context.author) + " failed to find account \"" + name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*C1RC3 pauses for a brief moment as she scans her records.* \"Request failed. No account exists under that name.\"")
        session.close()
        return

    # Check if account belongs to the person sending the command
    if account.owner_id == context.author.id:
        success: bool = account.withdraw(session, [phys_chips, ment_chips, arti_chips, supe_chips, merg_chips, swap_chips])

        if success:
            log(get_time() + " >> " + str(context.author) + " withdrew " + str(phys_chips) + "|" + str(ment_chips) + "|" + str(arti_chips) + "|" + str(supe_chips) + "|" + str(merg_chips) + "|" + str(swap_chips) 
                + " chips from their account \"" + name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")

            await context.respond(".", ephemeral = True, delete_after = 0)
            response: str = "*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes green for a moment.* \"Request approved.\" *Golden light begins to condense from nowhere into C1RC3's body as she visibly shivers. A hidden compartment in her midriff suddenly slides open, containing a pile of the chips you requested.* \"Your account now contains:\"\n# "

            bal: List[int] = account.get_bal()

            # If no chips, say "no chips".
            no_chips = True
            for chips in bal:
                if chips != 0:
                    no_chips = False
                    break
            if no_chips:
                response += "no " + chip_emojis[0]
            else:
                # Chips exist, so go through every non-zero chip and list them
                for i in range(len(bal)):
                    if bal[i] != 0:
                        response += str(bal[i]) + " " + chip_emojis[i] + ", "
                response = response.removesuffix(", ")

            await context.channel.send(response)
        else:
            log(get_time() + " >> " + str(context.author) + " withdrew too many chips from their account \"" + name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes green for a moment. However, she soon shakes her head.* \"Request denied. You do not have enough chips in your account for that withdrawal.\"")
    else:
        log(get_time() + " >> " + str(context.author) + " tried to access other's account \"" + name + "\" in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("*You feel a small tingle all over your body as C1RC3 scans your magical signature, and her face flashes red for a moment.* \"Request denied. This account does not belong to you.\"")

    session.close()