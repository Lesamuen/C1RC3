"""Contains several bot commands for admining or debugging"""

from typing import List

from discord import ApplicationContext, Option, Member

from bot import bot_client, database_connector
from auxiliary import perms, guilds, log, get_time, ghost_reply
from dbmodels import Game
from emojis import format_chips

admin_cmds = bot_client.create_group("admin", "Commands that only an admin can use", guild_ids = guilds, guild_only = True)

async def check_admin(context: ApplicationContext) -> bool:
    """Pre-check whether a user has the 'admin' permission
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context

    ### Returns
    True
        Author in admin perms list
    False
        Author not in admin perms list
    """

    if context.author.id in perms["admin"]:
        return True
    else:
        await context.respond("`\"Request denied. Administrator-level Access required.\"`")
        log(get_time() + " >> " + str(context.author) + " permission denied in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        return False
    
admin_cmds.checks = [check_admin]

@admin_cmds.command(name = "force_end_game", description = "Admin command to end a game in this channel", guild_ids = guilds, guild_only = True)
async def force_end_game(
    context: ApplicationContext
):
    """Add the command /admin force_end_game"""

    session = database_connector()

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to force-end a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. There is already no game at this table.\"`")
    else:
        log(get_time() + " >> Admin " + str(context.author) + " force-ended a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        game.end(session)
        await ghost_reply(context, "`\"Administrator-level Access detected. The game running for this table has been forcibly ended.\"`")

    session.close()

@admin_cmds.command(name = "set_chips", description = "Admin command to manually set chips in a game", guild_ids = guilds, guild_only = True)
async def force_end_game(
    context: ApplicationContext,
    user: Option(Member, description = "User whose chips you are editting", required = True),
    phys_chips: Option(int, description = "The amount of physical chips to set", min_value = 0, default = 0),
    ment_chips: Option(int, description = "The amount of mental chips to set", min_value = 0, default = 0),
    arti_chips: Option(int, description = "The amount of artificial chips to set", min_value = 0, default = 0),
    supe_chips: Option(int, description = "The amount of supernatural chips to set", min_value = 0, default = 0),
    merg_chips: Option(int, description = "The amount of merging chips to set", min_value = 0, default = 0),
    swap_chips: Option(int, description = "The amount of swap chips to set", min_value = 0, default = 0)
):
    """Add the command /admin set_chips"""

    session = database_connector()

    # Extract chip args
    chips: List[int] = list(locals().values())[2:8]

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to set chips with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. There is no game at this table.\"`")
    else:
        player = game.is_playing(session, user.id)
        if player is None:
            log(get_time() + " >> Admin " + str(context.author) + " tried to set chips for a non-player in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. This person is not playing at this table.\"`")
        else:
            player.set_chips(session, chips)
            log(get_time() + " >> Admin " + str(context.author) + " set chips of " + str(user) + " to " + str(chips) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. " + player.name + " has been granted the following chips:\"`\n## " + format_chips(chips))

    session.close()

@admin_cmds.command(name = "bad_girl", description = "Admin command to shut C1RC3 down", )
async def bad_girl(context: ApplicationContext):
    """Add the command /bad_girl"""

    await context.respond("https://tenor.com/view/anime-dan-machi-sad-sad-face-sorrow-gif-13886240")
    log(get_time() + " >> Admin " + str(context.author) + " externally shut down C1RC3 from [" + str(context.guild) + "], [" + str(context.channel) + "]")
    await bot_client.close()
    quit()

@bot_client.slash_command(name = "good_girl", description = "Reward C1RC3 <3", guild_ids = guilds, guild_only = True)
async def good_girl(context: ApplicationContext):
    """Add the command /good_girl"""

    await context.respond("https://tenor.com/view/catgirl-gif-19605722")
    log(get_time() + " >> " + str(context.author) + " headpatted C1RC3 [" + str(context.guild) + "], [" + str(context.channel) + "]")


