"""Contains several bot commands for fun outside of games"""

print("Loading module 'misc'...")

from random import randint

from discord import ApplicationContext, User, option, SlashCommand

from ..base.bot import bot_client
from ..base.auxiliary import guilds, log, loc, loc_arr, get_time
try:
    from ..games.miscgame import mg_roll
    misc_exists = True
except ImportError:
    misc_exists = False

@bot_client.slash_command(name = "good_girl", description = "Reward <3", guild_ids = guilds)
@option("user", User, description = "User to target with love")
@option("user2", User, description = "Other user to target with love", required = False)
async def headpat(context: ApplicationContext, user: User, user2: User):
    """Add the command /good_girl
    
    Throw a headpat at someone
    """
        
    if user2 is None:
        log(loc("pat.log.single", get_time(), context.guild, context.channel, context.author, user))
        await context.respond(loc_arr("pat.single", randint(0, 19)))
        await context.channel.send(user.mention)
    else:
        log(loc("pat.log.double", get_time(), context.guild, context.channel, context.author, user, user2))
        await context.respond(loc_arr("pat.double", randint(0, 2)))
        await context.channel.send(" ".join([user.mention, user2.mention]))

# Only make the alias if the miscgame module even exists
if misc_exists:
    roll_alias = SlashCommand(mg_roll.callback, name = "roll", description = "Roll some dice (does not require a game)", guild_ids = guilds)
    """Add the command /roll

    Alias for /mg roll
    """
    bot_client.add_application_command(roll_alias)
