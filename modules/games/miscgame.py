"""This module relates to the game type 'Misc'."""

print("Loading module 'miscgame'...")

from random import randint

from discord import ApplicationContext, option

from ..base.bot import bot_client, database_connector
from ..base.auxiliary import log, loc, get_time, ghost_reply, InvalidArgumentError
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
        log(loc("mg.shuffle.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("mg.none"), True)
    else:
        log(loc("mg.shuffle.log", get_time(), context.guild, context.channel, context.author))
        game.shuffle(session)
        await ghost_reply(context, loc("mg.shuffle"))

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
        log(loc("mg.deck.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("mg.none"), True)
    else:
        log(loc("mg.deck.log", get_time(), context.guild, context.channel, context.author))
        deck = game.get_deck()
        message = [loc("mg.deck", len(deck))]
        player = game.is_playing(session, context.author.id)
        if peek:
            deck = deck[::-1]
            if player is None or private:
                if (len(deck) > 26):
                    message.append(loc("mg.deck.big", format_cards(standard_deck, deck[:26]), len(deck) - 26))
                else:
                    message.append(loc("mg.deck.small", format_cards(standard_deck, deck)))
                await ghost_reply(context, "".join(message), True)
                if private and player is not None:
                    # Player is playing, so other players should be let known
                    await context.channel.send(loc("mg.deck.peek", player.name))
            else:
                for i in range(len(deck) // 13):
                    # 13 cards per row
                    message.append(loc("mg.deck.small", format_cards(standard_deck, deck[i * 13 : (i + 1) * 13])))
                if len(deck) % 13 > 0:
                    # Last cards, not full 13
                    message.append(loc("mg.deck.small", format_cards(standard_deck, deck[(len(deck) // 13) * 13:])))
                await ghost_reply(context, "".join(message))
        else:
            # Just counting cards left
            await ghost_reply(context, "".join(message), (private or (player is None)))

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
        log(loc("mg.draw.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("mg.none"), True)
    else:
        player: MiscPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("mg.draw.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("mg.draw.spec"), True)
        else:
            try:
                drawn = game.draw(session, amount)
            except InvalidArgumentError:
                log(loc("mg.draw.fail.log", get_time(), context.guild, context.channel, context.author, amount))
                await ghost_reply(context, loc("mg.draw.fail", len(game.get_deck())))
            else:
                log(loc("mg.draw.log", get_time(), context.guild, context.channel, context.author, drawn))
                if private:
                    await context.respond(loc("mg.draw", player.name, format_cards(standard_deck, drawn)), ephemeral = True)
                    await context.channel.send(loc("mg.draw.hide", player.name, amount))
                else:
                    await ghost_reply(context, loc("mg.draw", player.name, format_cards(standard_deck, drawn)))

    session.close()

@mg_cmds.command(name = "roll", description = "Roll some dice (does not require a game)")
@option("amount", int, description = "The number of dice to roll", min_value = 1, max_value = 100)
@option("sides", int, description = "The amount of sides each dice has", min_value = 1, max_value = 9999999999)
@option("private", bool, description = "Whether the dice can only be seen by you or not")
async def mg_roll(context: ApplicationContext, amount: int, sides: int, private: bool):
    """Add the command /mg roll
    
    Roll an amount of dice
    """
    dice = [randint(1, sides) for i in range(amount)]
    total = sum(dice)

    log(loc("mg.roll.log", get_time(), context.guild, context.channel, context.author, amount, sides, total))
    
    await ghost_reply(context, loc("mg.roll", amount, sides, dice[0], "".join(["".join([", ", str(die)]) for die in dice[1:]]), total), private)

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
        log(loc("mg.win.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("mg.none"), True)
    else:
        player: MiscPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("mg.win.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("mg.win.spec"), True)
        elif not game.is_midround():
            log(loc("mg.win.out.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("mg.win.out"), True)
        else:
            log(loc("mg.win.log", get_time(), context.guild, context.channel, context.author))
            game.end_round(session, player.user_id)
            await ghost_reply(context, loc("mg.win", player.name, player.name, format_chips(player.get_chips()), game.get_bet_turn().name))

    session.close()

async def mg_start_round(context: ApplicationContext):
    """Test for round start"""

    session = database_connector()

    game: Misc = Misc.find_game(session, context.channel_id)

    # Game must exist, and bets must be placed outside of round
    if game is not None and not game.is_midround() and game.bets_aligned():
        log(loc("mg.start.log", get_time(), context.guild, context.channel))
        bet_placed = game.players[0].get_bet()
        game.set_bet(session, bet_placed)
        
        await context.channel.send(loc("mg.start"))
        
        # Ping everyone for beginning of round
        await context.channel.send(" ".join([player.mention() for player in game.players]), delete_after = 0)

    session.close()

# Register round start logic to invoke after betting
for cmd in mg_cmds.walk_commands():
    if cmd.name == "bet":
        cmd.after_invoke(mg_start_round)
        break