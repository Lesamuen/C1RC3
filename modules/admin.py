"""Contains several bot commands for admining or debugging"""

print("Loading module 'admin'...")

from discord import ApplicationContext

from bot import bot_client
from auxiliary import perms, guilds, log, get_time, ghost_reply

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
        await ghost_reply(context, "`\"Request denied. Administrator-level Access required.\"`", True)
        log(get_time() + " >> " + str(context.author) + " permission denied in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        return False
    
admin_cmds.checks = [check_admin]

@admin_cmds.command(name = "bad_girl", description = "Admin command to shut C1RC3 down")
async def bad_girl(context: ApplicationContext):
    """Add the command /bad_girl"""

    await context.respond("https://tenor.com/view/anime-dan-machi-sad-sad-face-sorrow-gif-13886240")
    log(get_time() + " >> Admin " + str(context.author) + " externally shut down C1RC3 from [" + str(context.guild) + "], [" + str(context.channel) + "]")
    await bot_client.close()
    quit()

@bot_client.slash_command(name = "good_girl", description = "Reward C1RC3 <3")
async def good_girl(context: ApplicationContext):
    """Add the command /good_girl"""

    await context.respond("https://tenor.com/view/catgirl-gif-19605722")
    log(get_time() + " >> " + str(context.author) + " headpatted C1RC3 [" + str(context.guild) + "], [" + str(context.channel) + "]")


