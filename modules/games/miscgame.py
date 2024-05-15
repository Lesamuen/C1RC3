"""This module relates to the game type 'Misc'."""

print("Loading module 'miscgame'...")

from random import randint

from discord import ApplicationContext, SlashCommand, option

from ..base.bot import bot_client, database_connector
from ..base.auxiliary import guilds, log, get_time, ghost_reply, InvalidArgumentError
from ..base.dbmodels import Misc, MiscPlayer
from ..base.emojis import standard_deck, format_cards, format_chips
from .game import base_game_cmds

# Inherit and register command group to Discord
mg_cmds = base_game_cmds.copy()
mg_cmds.name = "mg"
mg_cmds.description = "Commands to run a Miscellaneous game"
for i, cmd in enumerate(mg_cmds.subcommands):
    cmd = cmd.copy()
    cmd.game_type = Misc
    mg_cmds.subcommands[i] = cmd
bot_client.add_application_command(mg_cmds)


@mg_cmds.command(name = "shuffle", description = "Shuffle the standard deck in this game")
async def mg_shuffle(
    context: ApplicationContext
):
    """Add the command /mg shuffle
    
    Shuffle the deck
    """

    session = database_connector()
    
    game: Misc = Misc.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to shuffle for no Misc game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no Misc game running at this table at the moment.\"`", True)
    else:
        game.shuffle(session)
        log(get_time() + " >> " + str(context.author) + " shuffled a deck in a Misc game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "*C1RC3 places all of the cards into a compartment that slides open in her arm, and shuts it. A moment of whirring later, she opens it again and pulls out a newly shuffled deck, setting it down on the table.*")

    session.close()

@mg_cmds.command(name = "deck", description = "Check the cards left in the deck (you don't have to be playing)")
@option("peek", bool, description = "Whether to see the cards themselves")
@option("private", bool, description = "Whether the cards can only be seen by you or not (only if not peeking). Always True if not playing.")
async def mg_deck(context: ApplicationContext, peek: bool, private: bool):
    """Add the command /mg deck
    
    View the deck
    """

    session = database_connector()
    
    game: Misc = Misc.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " drew for a Misc game with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no Misc game running at this table at the moment.\"`", True)
    else:
        log(get_time() + " >> " + str(context.author) + " checked Misc deck in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        deck = game.get_deck()
        message = "`\"There are " + str(len(deck)) + " cards remaining.\"`"
        player = game.is_playing(session, context.author.id)
        if peek:
            deck = deck[::-1]
            if player is None or private:
                if (len(deck) > 26):
                    message += "\n## " + format_cards(standard_deck, deck[:26]) + "...\n*" + str(len(deck) - 26) + " cards have been omitted.*"
                else:
                    message += "\n## " + format_cards(standard_deck, deck)
                await ghost_reply(context, message, True)
                if private and player is not None:
                    await context.channel.send("`\"" + player.name + " has peeked at the deck.\"`")
            else:
                await ghost_reply(context, message)
                for i in range(len(deck) // 13):
                    await context.channel.send("## " + format_cards(standard_deck, deck[i * 13 : (i + 1) * 13]))
                if len(deck) % 13 > 0:
                    await context.channel.send("## " + format_cards(standard_deck, deck[(len(deck) // 13) * 13:]))
        else:
            await ghost_reply(context, message, (private or (player is None)))

    session.close()

@mg_cmds.command(name = "draw", description = "Draw an amount of cards from the deck")
@option("amount", int, description = "The amount of cards to draw", min_value = 1, max_value = 26)
@option("private", bool, description = "Whether the cards drawn can only be seen by you or not")
async def mg_draw(context: ApplicationContext, amount: int, private: bool):
    """Add the command /mg draw
    
    Draw from the deck
    """

    session = database_connector()
    
    game: Misc = Misc.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " drew for a Misc game with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no Misc game running at this table at the moment.\"`", True)
    else:
        player: MiscPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " drew cards in a game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot be dealt cards in a game you are not a part of.\"`", True)
        else:
            try:
                drawn = game.draw(session, amount)
            except InvalidArgumentError:
                log(get_time() + " >> " + str(context.author) + " failed to draw " + str(amount) + " cards in a Misc game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "`\"There are only " + str(len(game.get_deck())) + " cards left in the deck right now.\"`")
            else:
                log(get_time() + " >> " + str(context.author) + " drew " + str(drawn) + " in a Misc game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                if private:
                    await context.respond("`\"" + player.name + " has drawn:\"`\n# " + format_cards(standard_deck, drawn), ephemeral = True)
                    await context.channel.send("`\"" + player.name + " has drawn " + str(amount) + " cards.\"`")
                else:
                    await ghost_reply(context, "`\"" + player.name + " has drawn:\"`\n# " + format_cards(standard_deck, drawn))

    session.close()

@mg_cmds.command(name = "roll", description = "Roll some dice (does not require a game)")
@option("amount", int, description = "The number of dice to roll", min_value = 1, max_value = 100)
@option("sides", int, description = "The amount of sides each dice has", min_value = 1, max_value = 9999999999)
@option("private", bool, description = "Whether the dice can only be seen by you or not")
async def mg_roll(context: ApplicationContext, amount: int, sides: int, private: bool):
    """Add the command /mg roll
    
    Roll an amount of dice
    """

    message = "*You have rolled " + str(amount) + "d" + str(sides) + ":*\n"
    sum = randint(1, sides)
    message += "## " + str(sum)
    if amount > 1:
        for i in range(amount - 1):
            roll = randint(1, sides)
            sum += roll
            message += ", " + str(roll)
        message += " = " + str(sum)
    log(get_time() + " >> " + str(context.author) + " rolled " + str(amount) + "d" + str(sides) + " for " + str(sum) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
    
    await ghost_reply(context, message, private)

roll_alias = SlashCommand(mg_roll.callback, name = "roll", description = "Roll some dice (does not require a game)", guild_ids = guilds, guild_only = True)
"""Add the command /roll

Alias for /mg roll
"""
bot_client.add_application_command(roll_alias)

@mg_cmds.command(name = "win_bet", description = "Declare yourself as the winner of the round, according to whatever rules you agreed on")
async def mg_win_bet(
    context: ApplicationContext
):
    """Add the command /mg win_bet
    
    Win a round
    """

    session = database_connector()
    
    game: Misc = Misc.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to win with no Misc game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no Misc game running at this table at the moment.\"`", True)
    else:
        player: MiscPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to win in a Misc game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot win in a Misc game you are not a part of.\"`", True)
        elif not game.is_midround():
            log(get_time() + " >> " + str(context.author) + " tried to win in a Misc game outside of a round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot win in a round that hasn't started yet.\"`", True)
        else:
            game.end_round(session, player.user_id)
            message = "`\"The Casino congratulates " + player.name + " for winning this round.\"`"\
                "\n*C1RC3 opens a compartment in her abdomen where a pile of fresh chips lays, and pushes it over to " + player.name + ", making a sizeable pile of:*\n"\
                + "# " + format_chips(player.get_chips())
            message += "\n`\"" + game.get_bet_turn().name + " shall decide the next initial bet.\"`"
            await ghost_reply(context, message)

    session.close()

async def mg_start_round(context: ApplicationContext):
    """Test for round start"""

    session = database_connector()

    game: Misc = Misc.find_game(session, context.channel_id)

    if game is not None and not game.is_midround() and game.bets_aligned():
        log(get_time() + " >> The Misc game round has started in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        bet_placed = game.players[0].get_bet()
        game.set_bet(session, bet_placed)
        
        await context.channel.send("`\"The players have agreed on a bet. The round has begun.\"`\n")
        
        # Ping everyone for beginning of round
        mention = ""
        for player in game.players:
            mention += player.mention() + " "
        await context.channel.send(mention, delete_after = 0)

    session.close()

# Register round start logic to invoke after betting
for cmd in mg_cmds.walk_commands():
    if cmd.name == "bet":
        cmd.after_invoke(mg_start_round)
        break