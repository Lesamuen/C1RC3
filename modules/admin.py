"""Contains several bot commands for admining or debugging"""

from discord import ApplicationContext

from bot import bot_client, database_connector
from auxiliary import perms, guilds, log, get_time

admin_cmds = bot_client.create_group("admin", "Commands to affect behind the scenes stuff for C1RC3")

@admin_cmds.command(name = "shutdown", description = "Shuts down bot externally")
async def admin_shutdown(context: ApplicationContext):
    """Adds the command /admin shutdown"""

    if context.author.id in perms["admin"]:
        await context.respond("`\"Permission granted. Shutdown protocol activated. Booting down...\"`")
        log(get_time() + " >> Admin " + str(context.author) + " externally shut down C1RC3 from [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await bot_client.close()
        quit()
    else:
        await context.respond("`\"Permission denied. You have no administrator privilege.\"`")
        log(get_time() + " >> " + str(context.author) + " permission denied in [" + str(context.guild) + "], [" + str(context.channel) + "]")

@bot_client.slash_command(name = "scan", description = "Scans the user, just for debugging", guild_ids = guilds, guild_only = True)
async def scan(context: ApplicationContext):
    """Adds the command /scan"""

    await context.respond(".", ephemeral = True, delete_after = 0)
    await context.channel.send("`\"Scanning protocol activated. Please stand still.\"`\n*C1RC3's eyes seem to glow a bit brighter, before a bright red cone of light shoots out and hovers from the top of your body to the very floor.*\n`\"Scanning protocol complete. Your soul value is "
         + str(context.author.id) + ". C1RC3 and the Casino by extension thanks you for your contribution.\"`")
    log(get_time() + " >> " + str(context.author) + " scanned themselves in [" + str(context.guild) + "], [" + str(context.channel) + "]")
    log("id: " + str(context.author.id) + "\nname: " + str(context.author))
