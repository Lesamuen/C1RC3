"""This module relates to the game type 'Misc'."""

print("Loading module 'miscgame'...")

from typing import List
from random import randint

from discord import ApplicationContext, Option, OptionChoice

from bot import bot_client, database_connector
from auxiliary import guilds, log, get_time, ghost_reply, InvalidArgumentError
from dbmodels import Misc, MiscPlayer
from emojis import standard_deck, format_cards, format_chips
from game import create, join, concede, identify, rename, chips, bet, use, convert

mg_cmds = bot_client.create_group("mg", "Commands to run a Misc game", guild_ids = guilds, guild_only = True)

@mg_cmds.command(name = "create", description = "Start a Misc game in this channel")
async def mg_create(
    context: ApplicationContext,
    stake: Option(int, description = "What stake to set the game to", required = True, choices = [
        OptionChoice("Low Stakes", 0),
        OptionChoice("Normal Stakes", 1),
        OptionChoice("High Stakes", 2),
    ])
):
    """Add the command /mg create"""

    session = database_connector()

    await create(context, session, stake, Misc)

    session.close()

@mg_cmds.command(name = "join", description = "Join a Misc game in this channel")
async def mg_join(
    context: ApplicationContext,
    name: Option(str, description = "The name that C1RC3 will refer to you as", required = True, min_length = 1)
):
    """Add the command /mg join"""

    session = database_connector()

    await join(context, session, name, Misc)

    session.close()

@mg_cmds.command(name = "concede", description = "Tell C1RC3 you lost (use when fully TFed or at the end of a mental round)")
async def mg_concede(
    context: ApplicationContext
):
    """Add the command /mg concede"""

    session = database_connector()

    await concede(context, session, Misc)

    session.close()

@mg_cmds.command(name = "identify", description = "Be reminded of the other players' identities and chips")
async def mg_identify(
    context: ApplicationContext
):
    """Add the command /mg identify"""

    session = database_connector()

    await identify(context, session, Misc)

    session.close()

@mg_cmds.command(name = "rename", description = "Ask C1RC3 to call you something else, in case your name has been changed")
async def mg_rename(
    context: ApplicationContext,
    name: Option(str, description = "Name that C1RC3 will refer to you as", required = True, min_length = 1),
    private: Option(bool, description = "Whether to keep the response only visible to you", required = False)
):
    """Add the command /mg rename"""

    session = database_connector()

    await rename(context, session, name, private, Misc)

    session.close()

@mg_cmds.command(name = "chips", description = "Recount how many chips you have in your current pile")
async def mg_chips(
    context: ApplicationContext,
    private: Option(bool, description = "Whether to keep the response only visible to you", required = True)
):
    """Add the command /mg chips"""

    session = database_connector()

    await chips(context, session, private, Misc)

    session.close()

@mg_cmds.command(name = "bet", description = "Bet an amount of chips")
async def mg_bet(
    context: ApplicationContext,
    physical: Option(int, description = "The amount of physical chips to bet", min_value = 0, max_value = 100, default = 0),
    mental: Option(int, description = "The amount of mental chips to bet", min_value = 0, max_value = 20, default = 0),
    artificial: Option(int, description = "The amount of artificial chips to bet", min_value = 0, max_value = 2, default = 0),
    supernatural: Option(int, description = "The amount of supernatural chips to bet", min_value = 0, max_value = 20, default = 0),
    merge: Option(int, description = "The amount of merge chips to bet", min_value = 0, max_value = 3, default = 0),
    swap: Option(int, description = "The amount of swap chips to bet", min_value = 0, max_value = 25, default = 0)
):
    """Add the command /mg bet"""

    # Extract chip args
    chips: List[int] = list(locals().values())[1:7]

    session = database_connector()

    game: Misc
    bet_placed, game = await bet(context, session, chips, Misc)

    if bet_placed:
        if game.bets_aligned():
            log(get_time() + " >> The Blackjack round has started in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            game.set_bet(session, chips)
            
            await context.channel.send("`\"The players have agreed on a bet. The round has begun.\"`\n")

    session.close()

@mg_cmds.command(name = "use", description = "Use an amount of chips from your current pile")
async def mg_use(
    context: ApplicationContext,
    physical: Option(int, description = "The amount of physical chips to use", min_value = 0, default = 0),
    mental: Option(int, description = "The amount of mental chips to use", min_value = 0, default = 0),
    artificial: Option(int, description = "The amount of artificial chips to use", min_value = 0, default = 0),
    supernatural: Option(int, description = "The amount of supernatural chips to use", min_value = 0, default = 0),
    merge: Option(int, description = "The amount of merge chips to use", min_value = 0, default = 0),
    swap: Option(int, description = "The amount of swap chips to use", min_value = 0, default = 0)
):
    """Add the command /mg use"""

    # Extract chip args
    chips: List[int] = list(locals().values())[1:7]

    session = database_connector()

    await use(context, session, chips, Misc)

    session.close()

@mg_cmds.command(name = "convert", description = "Convert one type of chips to another")
async def mg_convert(
    context: ApplicationContext,
    type: Option(int, description = "What chips to convert", required = True, choices = [
        OptionChoice("Mental -> x10 Physical", 0),
        OptionChoice("Artificial -> x40 Physical, x3 Mental", 1),
        OptionChoice("x40 Physical, x3 Mental -> Artificial", 2),
        OptionChoice("Supernatural -> x5 Physical", 3),
        OptionChoice("Supernatural -> x1/2 Mental", 4),
        OptionChoice("x5 Physical -> Supernatural", 5),
        OptionChoice("x1/2 Mental -> Supernatural", 6),
        OptionChoice("Merge -> x30 Physical", 7),
        OptionChoice("Merge -> x3 Mental", 8),
        OptionChoice("Swap -> x5 Physical", 9),
        OptionChoice("Swap -> x1/2 Mental", 10),
    ]),
    amount: Option(int, description = "The amount of chips to convert", min_value = 1)
):
    """Add the command /mg convert"""

    session = database_connector()

    await convert(context, session, type, amount, Misc)

    session.close()

@mg_cmds.command(name = "shuffle", description = "Shuffle the standard deck in this game")
async def mg_shuffle(
    context: ApplicationContext
):
    """Add the command /mg shuffle"""

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
async def mg_deck(
    context: ApplicationContext,
    peek: Option(bool, description = "Whether to see the cards themselves", required = True),
    private: Option(bool, description = "Whether the cards can only be seen by you or not (only if not peeking). Always True if not playing.", required = True)
):
    """Add the command /mg deck"""

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
async def mg_draw(
    context: ApplicationContext,
    amount: Option(int, description = "The amount of cards to draw", min_value = 1, max_value = 26),
    private: Option(bool, description = "Whether the cards drawn can only be seen by you or not", required = True)
):
    """Add the command /mg draw"""

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
async def mg_roll(
    context: ApplicationContext,
    amount: Option(int, description = "The number of dice to roll", min_value = 1, max_value = 100),
    sides: Option(int, description = "The amount of sides each dice has", min_value = 1, max_value = 9999999999),
    private: Option(bool, description = "Whether the dice can only be seen by you or not", required = True)
):
    """Add the command /mg roll"""

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

@mg_cmds.command(name = "win_bet", description = "Declare yourself as the winner of the round, according to whatever rules you agreed on")
async def mg_win_bet(
    context: ApplicationContext
):
    """Add the command /mg win_bet"""

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
            await ghost_reply(context, message)

    session.close()
