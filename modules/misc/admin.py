"""Contains several bot commands for admining or debugging"""

print("Loading module 'admin'...")

from discord import ApplicationContext

from ..base.bot import bot_client
from ..base.auxiliary import perms, guilds, log, get_time, ghost_reply, loc

admin_cmds = bot_client.create_group("admin", "Commands that only an admin can use", guild_ids = guilds)

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
        log(loc("admin.deny.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("admin.deny"), True)
        return False
    
admin_cmds.checks = [check_admin]

@admin_cmds.command(name = "bad_girl", description = "Admin command to shut C1RC3 down")
async def shutdown(context: ApplicationContext):
    """Add the command /admin bad_girl
    
    Shut C1RC3 down externally
    """

    log(loc("admin.shutdown.log", get_time(), context.guild, context.channel, context.author))
    await context.respond(loc("admin.shutdown"))
    await bot_client.close()
    quit()
