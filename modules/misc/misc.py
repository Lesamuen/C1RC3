"""Contains several bot commands for fun outside of games"""

print("Loading module 'misc'...")

from random import randint

from discord import ApplicationContext, User, option, SlashCommand

from ..base.bot import bot_client
from ..base.auxiliary import guilds, log, get_time
from ..games.miscgame import mg_roll

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
    "https://tenor.com/view/anime-head-pat-gif-23472600",
    "https://tenor.com/view/kanna-kanna-kamui-dragon-maid-miss-kobayashis-dragon-maid-anime-gif-16567663",
    "https://tenor.com/view/pet-head-cute-rem-re-zero-anime-gif-16038325",
    "https://tenor.com/view/dakooters-anime-headpats-pats-headpatting-gif-19110358",
    "https://tenor.com/view/hinako-note-pat-pat-head-pat-anime-kawaii-gif-14816799",
    "https://tenor.com/view/pat-gif-19836598",
    ]

double_headpats = [
    "https://tenor.com/view/anime-cat-girls-pet-head-cute-girls-gif-17829980",
    "https://tenor.com/view/senko-cute-smiling-gif-14951592",
    "https://tenor.com/view/anime-neko-anime-head-pat-anime-head-rub-neko-para-gif-16085488",
]

@bot_client.slash_command(name = "good_girl", description = "Reward <3", guild_ids = guilds, guild_only = True)
@option("user", User, description = "User to target with love")
@option("user2", User, description = "Other user to target with love", required = False)
async def headpat(context: ApplicationContext, user: User, user2: User):
    """Add the command /good_girl
    
    Throw a headpat at someone
    """

    if user is not None and user2 is not None:
        await context.respond(double_headpats[randint(0, len(double_headpats) - 1)])
    else:
        await context.respond(headpats[randint(0, len(headpats) - 1)])
    if user is not None:
        if user2 is not None:
            await context.channel.send(user.mention + " " + user2.mention)
        else:
            await context.channel.send(user.mention)
    log(get_time() + " >> " + str(context.author) + " headpatted " + (str(user) + " " + ("and " + str(user2) + " " if user2 is not None else "") if user is not None else "")\
        + "in [" + str(context.guild) + "], [" + str(context.channel) + "]")

roll_alias = SlashCommand(mg_roll.callback, name = "roll", description = "Roll some dice (does not require a game)", guild_ids = guilds, guild_only = True)
"""Add the command /roll

Alias for /mg roll
"""
bot_client.add_application_command(roll_alias)
