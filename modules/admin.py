"""Contains several bot commands for admining or debugging"""

from discord import ApplicationContext, Option
from discord import User as DiscordUser

from bot import bot_client, database_connector
from auxiliary import perms, log, get_time
from dbmodels import User

admin_cmds = bot_client.create_group("admin", "Commands to affect behind the scenes stuff for C1RC3")

@admin_cmds.command(name = "shutdown", description = "Shuts down bot externally")
async def admin_shutdown(context: ApplicationContext):
    """Adds the command /admin shutdown"""

    if context.author.id in perms["admin"]:
        await context.respond("\"Permission granted. Shutdown protocol activated. Booting down...\"")
        log(get_time() + " >> Admin " + str(context.author) + " externally shut down C1RC3 from GUILD[" + str(context.guild) + "], CHANNEL[" + str(context.channel) + "]")
        await bot_client.close()
        quit()
    else:
        await context.respond("\"Permission denied.\"")
        log(get_time() + " >> " + str(context.author) + " permission denied in GUILD[" + str(context.guild) + "], CHANNEL[" + str(context.channel) + "]")
