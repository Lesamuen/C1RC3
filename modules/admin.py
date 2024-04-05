"""Contains several bot commands for admining or debugging"""

print("Loading module 'admin'...")

from random import randint

from discord import ApplicationContext, Option, User

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

# No clue why this is here in admin.py, it was the only place it could really go
headpats = [
    "https://tenor.com/view/anime-pat-gif-22001993",
    "https://tenor.com/view/ruby-ruby-hoshino-headpat-anime-oshi-no-ko-gif-18256603620411463351",
    "https://tenor.com/view/anime-head-pat-anime-head-rub-neko-anime-love-anime-gif-16121044",
    "https://tenor.com/view/qualidea-code-head-pat-anime-anime-girl-blush-anime-gif-24627864",
    "https://tenor.com/view/kaede-azusagawa-kaede-gif-head-headpat-gif-13284057",
    "https://tenor.com/view/pat-gif-20637970",
    "https://tenor.com/view/head-pat-anime-kawaii-neko-nyaruko-gif-15735895",
    "https://tenor.com/view/anime-head-pat-gif-23472603",
    "https://tenor.com/view/anime-pat-gif-22001979",
    "https://tenor.com/view/headpats-anime-cat-girl-beeg-pats-shake-pats-gif-7464612627661142514",
    "https://tenor.com/view/senpai-ga-uzai-kouhai-no-hanashi-futaba-futaba-igarashi-my-senpai-is-annoying-headpats-anime-gif-23547171",
    "https://tenor.com/view/head-pat-love-live-anime-gif-11053869",
    "https://tenor.com/view/pat-gif-19836590",
    "https://tenor.com/view/anime-cry-blush-cute-petting-gif-22149967",
    "https://tenor.com/view/anime-neko-para-neko-anime-head-rub-anime-head-pat-gif-16085519",
    "https://tenor.com/view/kanna-kanna-kamui-dragon-maid-miss-kobayashis-dragon-maid-anime-gif-16567663",
    "https://tenor.com/view/pet-head-cute-rem-re-zero-anime-gif-16038325",
    "https://tenor.com/view/dakooters-anime-headpats-pats-headpatting-gif-19110358",
    "https://tenor.com/view/hinako-note-pat-pat-head-pat-anime-kawaii-gif-14816799",
    "https://tenor.com/view/pat-gif-19836598",
    ]

@bot_client.slash_command(name = "good_girl", description = "Reward <3", guild_ids = guilds, guild_only = True)
async def good_girl(
    context: ApplicationContext,
    user: Option(User, description = "User to target with love", required = False)
    ):
    """Add the command /good_girl"""

    await context.respond("https://canary.discordapp.com/__development/link/", ephemeral = True, delete_after = 0)
    if user is not None:
        await context.channel.send(user.mention)
    await context.channel.send(headpats[randint(0, 19)])
    log(get_time() + " >> " + str(context.author) + " headpatted " + (str(user) + " " if user is not None else "") + "in [" + str(context.guild) + "], [" + str(context.channel) + "]")


