"""Contains several bot commands for admining or debugging"""

from discord import ApplicationContext

from bot import bot_client, database_connector
from auxiliary import perms, guilds, log, get_time
from dbmodels import Game

admin_cmds = bot_client.create_group("admin", "Commands that only an admin can use", guild_ids = guilds, guild_only = True)

async def check_admin(context: ApplicationContext) -> bool:
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
    """Adds the command /admin force_end_game"""

    session = database_connector()

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to force-end a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("`\"Administrator-level Access detected. Request failed. There is already no game at this table.\"`")
    else:
        log(get_time() + " >> Admin " + str(context.author) + " force-ended a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        game.end(session)
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("`\"Administrator-level Access detected. The game running for this table has been forcibly ended.\"`")

    session.close()

@admin_cmds.command(name = "bad_girl", description = "Shuts down bot externally", )
async def bad_girl(context: ApplicationContext):
    """Adds the command /bad_girl"""

    await context.respond("https://tenor.com/view/anime-dan-machi-sad-sad-face-sorrow-gif-13886240")
    log(get_time() + " >> Admin " + str(context.author) + " externally shut down C1RC3 from [" + str(context.guild) + "], [" + str(context.channel) + "]")
    await bot_client.close()
    quit()

@bot_client.slash_command(name = "good_girl", description = "Reward C1RC3 <3", guild_ids = guilds, guild_only = True)
async def good_girl(context: ApplicationContext):
    """Adds the command /good_girl"""

    await context.respond("https://tenor.com/view/catgirl-gif-19605722")
    log(get_time() + " >> " + str(context.author) + " headpatted C1RC3 [" + str(context.guild) + "], [" + str(context.channel) + "]")


