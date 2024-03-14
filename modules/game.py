"""Module containing methods that are applicable to every game"""

from typing import List, Tuple

from discord import ApplicationContext, Option, OptionChoice
from sqlalchemy.orm import Session

from bot import bot_client, database_connector
from auxiliary import perms, guilds, log, get_time, all_zero
from dbmodels import User, Game, Player
from emojis import format_chips

chip_conversions = (
    ((0, 1, 0, 0, 0, 0), (10, 0, 0, 0, 0, 0)),
    ((0, 0, 1, 0, 0, 0), (40, 3, 0, 0, 0, 0)),
    ((40, 3, 0, 0, 0, 0), (0, 0, 1, 0, 0, 0)),
    ((0, 0, 0, 1, 0, 0), (5, 0, 0, 0, 0, 0)),
    ((0, 0, 0, 1, 0, 0), (0, 0.5, 0, 0, 0, 0)),
    ((5, 0, 0, 0, 0, 0), (0, 0, 0, 1, 0, 0)),
    ((0, 0.5, 0, 0, 0, 0), (0, 0, 0, 1, 0, 0)),
    ((0, 0, 0, 0, 1, 0), (30, 0, 0, 0, 0, 0)),
    ((0, 0, 0, 0, 1, 0), (0, 3, 0, 0, 0, 0)),
    ((0, 0, 0, 0, 0, 1), (5, 0, 0, 0, 0, 0)),
    ((0, 0, 0, 0, 0, 1), (0, 0.5, 0, 0, 0, 0)),
)

@bot_client.slash_command(name = "force_end_game", description = "Admin command to end a game in this channel", guild_ids = guilds, guild_only = True)
async def force_end_game(
    context: ApplicationContext
):
    """Adds the command /force_end_game"""

    session = database_connector()

    if context.author.id in perms["admin"]:
        game = Game.find_game(session, context.channel_id)
        if game is None:
            log(get_time() + " >> Admin " + str(context.author) + " tried to force-end a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("`\"Request failed. There is already no game in this channel.\"`")
        else:
            log(get_time() + " >> Admin " + str(context.author) + " force-ended a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            game.end(session)
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("`\"Permission granted. The game running for this table has been forcibly ended.\"`")
    else:
        await context.respond("`\"Permission denied. You have no administrator privilege.\"`")
        log(get_time() + " >> " + str(context.author) + " permission denied in [" + str(context.guild) + "], [" + str(context.channel) + "]")

    session.close()

async def bet(context: ApplicationContext, session: Session, chips: List[int], expected_type: str) -> Tuple[bool, Game]:
    """default bet behavior, return whether bet placed"""

    if all_zero(chips):
        log(get_time() + " >> " + str(context.author) + " tried to bet nothing in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: ...nothin'?")
        return (False, None)

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to bet with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: no game here")
    elif game.type != expected_type:
        log(get_time() + " >> " + str(context.author) + " tried to bet in the wrong type of game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: wrong game to bet")
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to bet in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: not part of this game")
        elif game.is_midround():
            log(get_time() + " >> " + str(context.author) + " tried to bet mid-game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: can't change bet midround")
        else:
            log(get_time() + " >> " + str(context.author) + " placed a bet of " + str(chips) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            player.set_bet(session, chips)
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: " + player.name + " placed bet of " + str(chips))
            return (True, game)

    return (False, None)

async def concede(context: ApplicationContext, session: Session, expected_type: str) -> None:
    """default concede behavior"""
    
    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to concede from no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: no game here")
    elif game.type != expected_type:
        log(get_time() + " >> " + str(context.author) + " tried to bet from the wrong type of game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: wrong game to concede")
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to concede from the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: not part of this game")
        elif game.is_midround():
            log(get_time() + " >> " + str(context.author) + " tried to concede mid-game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: can't concede midround")
        else:
            log(get_time() + " >> " + str(context.author) + " conceded from a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)

            player.leave(session)
            if game.started:
                # Game in progress, so check if only one remaining = overall winner
                await context.channel.send("PLACEHOLDER: " + player.name + " conceded")
                if len(game.players) == 1:
                    winner: Player = game.players[0]
                    await context.channel.send("PLACEHOLDER: " + winner.name + " won the entire game")
                    await context.channel.send("PLACEHOLDER: " + winner.name + " final winnings:\n" + format_chips(winner.get_chips()))
                    await context.channel.send("PLACEHOLDER: deleting game")
                    game.end(session)
            else:
                # Game has not started, so safely left the game; if all left, delete game
                await context.channel.send("PLACEHOLDER: " + player.name + " withdrew")
                if len(game.players) == 0:
                    await context.channel.send("PLACEHOLDER: all players left, deleting game")
                    game.end(session)

async def chips(context: ApplicationContext, session: Session, expected_type: str) -> None:
    """default chip view behavior"""
    
    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to view chips with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: no game here")
    elif game.type != expected_type:
        log(get_time() + " >> " + str(context.author) + " tried to view chips of the wrong type of game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: wrong game to concede")
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to view chips in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: not part of this game")
        else:
            log(get_time() + " >> " + str(context.author) + " viewed chips in a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: current chips of " + player.name + " are\n" + format_chips(player.get_chips()))

async def use(context: ApplicationContext, session: Session, chips: List[int], expected_type: str) -> None:
    """default chip use behavior"""

    if all_zero(chips):
        log(get_time() + " >> " + str(context.author) + " tried to use no chips in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: ...nothin'?")
        return (False, None, None)

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to use chips with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: no game here")
    elif game.type != expected_type:
        log(get_time() + " >> " + str(context.author) + " tried to use chips in the wrong type of game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: wrong game to use chips")
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to use chips in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: not part of this game")
        elif game.is_midround():
            log(get_time() + " >> " + str(context.author) + " tried to use chips mid-game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: can't use chips midround")
        else:
            success = player.use_chips(session, chips)
            if success:
                log(get_time() + " >> " + str(context.author) + " used " + str(chips) + " chips in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await context.respond(".", ephemeral = True, delete_after = 0)
                await context.channel.send("PLACEHOLDER: " + str(chips) + " chips used by " + player.name)
            else:
                log(get_time() + " >> " + str(context.author) + " tried to use " + str(chips) + " chips in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await context.respond(".", ephemeral = True, delete_after = 0)
                await context.channel.send("PLACEHOLDER: not enough chips")

async def convert(context: ApplicationContext, session: Session, option: int, amount: int, expected_type: str) -> None:
    """default chip conversion behavior"""

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to convert chips with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: no game here")
    elif game.type != expected_type:
        log(get_time() + " >> " + str(context.author) + " tried to convert chips in the wrong type of game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: wrong game to convert chips")
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to convert chips in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: not part of this game")
        elif game.is_midround():
            log(get_time() + " >> " + str(context.author) + " tried to convert chips mid-game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: can't convert chips midround")
        else:
            # test to see if conversion results in whole numbers
            consumed, produced = chip_conversions[option]
            consumed = [x * amount for x in consumed]
            produced = [x * amount for x in produced]

            whole = True
            for i in range(len(consumed)):
                if consumed[i] % 1 != 0 or produced[i] % 1 != 0:
                    whole = False

            if not whole:
                log(get_time() + " >> " + str(context.author) + " converted illegal amount of chips in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await context.respond(".", ephemeral = True, delete_after = 0)
                await context.channel.send("PLACEHOLDER: please convert whole numbers of chips")
            else:
                # convert to int
                consumed = [int(x) for x in consumed]
                produced = [int(x) for x in produced]
                if player.use_chips(session, consumed):
                    player.pay_chips(session, produced)
                    log(get_time() + " >> " + str(context.author) + " converted " + str(consumed) + " to " + str(produced) + " chips in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await context.respond(".", ephemeral = True, delete_after = 0)
                    await context.channel.send("PLACEHOLDER: " + player.name + " converted " + str(consumed) + " to " + str(produced) + " chips")
                else:
                    log(get_time() + " >> " + str(context.author) + " converted more chips than they had in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await context.respond(".", ephemeral = True, delete_after = 0)
                    await context.channel.send("PLACEHOLDER: you don't have enough chips for that conversion")