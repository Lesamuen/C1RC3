"""Module containing methods that are applicable to every game"""

print("Loading module 'game'...")

from typing import List, Tuple

from discord import ApplicationContext
from sqlalchemy.orm import Session

from auxiliary import log, get_time, all_zero, ghost_reply
from dbmodels import Game, Player
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

async def create(context: ApplicationContext, session: Session, expected_type: type[Game]) -> None:
    """Handle functionality for creating any game
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    session: sqlalchemy.orm.Session
        Current database scope
    expected_type: type[dbmodels.Game]
        Game subclass this command was sent for
    """

    game = Game.find_game(session, context.channel_id)
    if game is not None:
        log(get_time() + " >> " + str(context.author) + " tried to create another game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is already a game running at this table.\"`")
    else:
        expected_type.create_game(session, context.channel_id)
        
        print("goth eher")
        log(get_time() + " >> " + str(context.author) + " started a " + str(expected_type) + " game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "*C1RC3 approaches you when you call for a dealer, and takes her place at the dealer's stand.*\n"\
            "`\"Your request has been processed. I will be acting as your table's arbitrator. Please state your name for the record, in order for your participation to be counted.\"`")

async def join(context: ApplicationContext, session: Session, name: str, expected_type: type[Game]) -> None:
    """Handle functionality for joining any game
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    session: sqlalchemy.orm.Session
        Current database scope
    name: str
        Name to refer to new Player as
    expected_type: type[dbmodels.Game]
        Game subclass this command was sent for
    """

    game: expected_type = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to join no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`")
    else:
        if game.is_full():
            log(get_time() + " >> " + str(context.author) + " tried to join a full game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"This table is already full.\"`")
        elif game.is_midround():
            # Can't join game in the middle of a round
            log(get_time() + " >> " + str(context.author) + " tried to join a game mid-round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"This table is in the middle of a round; please wait until the round is over before joining.\"`")
        else:
            if (player := game.join_game(session, context.author.id, name)) is not None:
                log(get_time() + " >> " + str(context.author) + " joined a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "*C1RC3 nods.* `\"Request accepted. " + player.name + " has joined this table.\"`")
            else:
                log(get_time() + " >> " + str(context.author) + " tried to rejoin a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "*C1RC3 stays silent for a couple of seconds as she tries to process your request.*\n`\"...You are already part of this table.\"`")

async def concede(context: ApplicationContext, session: Session, expected_type: type[Game]) -> None:
    """Handle functionality for conceding in any game
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    session: sqlalchemy.orm.Session
        Current database scope
    expected_type: type[dbmodels.Game]
        Game subclass this command was sent for
    """
    
    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to concede from no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`")
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to concede from the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "*C1RC3 stares at you for a few seconds.* `\"You cannot concede a game you are not a part of.\"`")
        elif game.is_midround():
            log(get_time() + " >> " + str(context.author) + " tried to concede mid-game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + ", you cannot concede right now, in the middle of a round.\"`")
        else:
            log(get_time() + " >> " + str(context.author) + " conceded from a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")

            name = player.name
            player.leave(session)
            if game.started:
                # Game in progress, so check if only one remaining = overall winner
                message = "`\"Understood. Player " + name + " has officially conceded.\"`\n*C1RC3 snaps her fingers as the magic of the casino flows into "\
                     + name + ", solidifying their new form. Their pile of chips disintegrates into golden light, reabsorbed into C1RC3 as her frame shivers.*\n"
                if len(game.players) == 1:
                    winner: Player = game.players[0]
                    log("                     >> Game ended with winner " + winner.name + ".")
                    message += "\n*C1RC3 turns to the last player.* `\"Congratulations, " + winner.name + ", you have won against everyone at the table.\n"\
                        "You may choose to transform back to your original form at the beginning of the game, or keep your current one if it is complete.\n"\
                        "You may also keep your chips, if this table was at normal stakes or higher:\"`\n# "\
                         + format_chips(winner.get_chips()) + "\n*With that, C1RC3 walks off to attend to other tables.*"
                    game.end(session)
                await ghost_reply(context, message)
            else:
                # Game has not started, so safely left the game; if all left, delete game
                await ghost_reply(context, "`\"Understood. Player " + name + " has changed their mind.\"`")
                if len(game.players) == 0:
                    log("                     >> Game deleted as all players left.")
                    await context.channel.send("*With no one left sitting at the table, C1RC3 walks off to attend to other tables.*")
                    game.end(session)

async def chips(context: ApplicationContext, session: Session, expected_type: type[Game]) -> None:
    """Handle functionality for viewing chips in any game
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    session: sqlalchemy.orm.Session
        Current database scope
    expected_type: type[dbmodels.Game]
        Game subclass this command was sent for
    """
    
    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to view chips with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`")
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to view chips in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "*C1RC3 stares at you for a few seconds.* `\"You do not have any chips for game you are not a part of.\"`")
        else:
            log(get_time() + " >> " + str(context.author) + " viewed chips (" + str(player.get_chips()) + ") in a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + ", you currently have:\"`\n# " + format_chips(player.get_chips()))

async def bet(context: ApplicationContext, session: Session, chips: List[int], expected_type: type[Game]) -> Tuple[bool, Game]:
    """Handle functionality for placing a bet in any game
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    session: sqlalchemy.orm.Session
        Current database scope
    chips: list[int]
        Values of chips to bet in order of type
    expected_type: type[dbmodels.Game]
        Game subclass this command was sent for

    ### Returns
    bool
        True
            The bet was successfully placed
        False
            The bet failed to be placed
    dbmodels.Game
        The game of the channel if bet placed; None if not
    """

    if all_zero(chips):
        log(get_time() + " >> " + str(context.author) + " tried to bet nothing in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "*C1RC3 pauses as she tries to process your inane request.*\n`\"...You cannot bet nothing. Please restate your bet.\"`")
        return (False, None)

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to bet with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`")
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to bet in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "*C1RC3 stares at you for a few seconds.* `\"You cannot bet in a game you are not a part of.\"`")
        elif game.is_midround():
            log(get_time() + " >> " + str(context.author) + " tried to bet mid-game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + ", you cannot bet right now, in the middle of a round.\"`")
        else:
            log(get_time() + " >> " + str(context.author) + " placed bet of " + str(chips) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            player.set_bet(session, chips)
            await ghost_reply(context, "*C1RC3 nods to your request, as she reiterates,* `\"" + player.name + " has placed a bet of:\"`\n## " + format_chips(chips))
            return (True, game)

    return (False, None)

async def use(context: ApplicationContext, session: Session, chips: List[int], expected_type: type[Game]) -> None:
    """Handle functionality for using chips in any game
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    session: sqlalchemy.orm.Session
        Current database scope
    chips: list[int]
        Values of chips to use in order of type
    expected_type: type[dbmodels.Game]
        Game subclass this command was sent for
    """

    if all_zero(chips):
        log(get_time() + " >> " + str(context.author) + " tried to use no chips in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "*C1RC3 pauses as she tries to process your inane request.*\n`\"...You cannot use nothing. Please restate how many chips you want to use.\"`")

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to use chips with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`")
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to use chips in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "*C1RC3 stares at you for a few seconds.* `\"You cannot use chips in a game you are not a part of.\"`")
        elif game.is_midround():
            log(get_time() + " >> " + str(context.author) + " tried to use chips mid-game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + ", you cannot use chips right now, in the middle of a round.\"`")
        else:
            success = player.use_chips(session, chips)
            if success:
                log(get_time() + " >> " + str(context.author) + " used " + str(chips) + " chips in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "`\"" + player.name + " has used:\"`\n## " + format_chips(chips))
            else:
                log(get_time() + " >> " + str(context.author) + " tried to use " + str(chips) + " chips in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "`\"You do not possess enough chips to use that many, " + player.name + ".\"`")

async def convert(context: ApplicationContext, session: Session, option: int, amount: int, expected_type: type[Game]) -> None:
    """Handle functionality for converting chips in any game
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    session: sqlalchemy.orm.Session
        Current database scope
    option: int
        Index for conversion type of chip_conversions
    amount: int
        Amount to multiply conversion by
    expected_type: type[dbmodels.Game]
        Game subclass this command was sent for
    """

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to convert chips with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`")
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to convert chips in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "*C1RC3 stares at you for a few seconds.* `\"You cannot convert chips in a game you are not a part of.\"`")
        elif game.is_midround():
            log(get_time() + " >> " + str(context.author) + " tried to convert chips mid-game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + ", you cannot convert chips right now, in the middle of a round.\"`")
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
                log(get_time() + " >> " + str(context.author) + " converted illegal amount of chips (" + str(consumed) + " to " + str(produced) + ") in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "*C1RC3 shakes her head.* `\"That conversion would result in a fractional chip; please pay attention to the conversion ratios, " + player.name + ".\"`")
            else:
                # convert to int
                consumed = [int(x) for x in consumed]
                produced = [int(x) for x in produced]
                if player.use_chips(session, consumed):
                    player.pay_chips(session, produced)
                    log(get_time() + " >> " + str(context.author) + " converted " + str(consumed) + " to " + str(produced) + " chips in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await ghost_reply(context, "`\"" + player.name + " has converted:\"`\n## " + format_chips(consumed) + " to " + format_chips(produced))
                else:
                    log(get_time() + " >> " + str(context.author) + " converted more chips than they had (" + str(consumed) + ") in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await ghost_reply(context, "`\"You do not possess enough chips to convert that many, " + player.name + ".\"`")
           
async def rename(context: ApplicationContext, session: Session, new_name: str, expected_type: type[Game]) -> None:
    """Handle functionality for renaming a player in any game
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    session: sqlalchemy.orm.Session
        Current database scope
    new_name: str
        The new name to set the player to
    expected_type: type[dbmodels.Game]
        Game subclass this command was sent for
    """

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to rename with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`")
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to rename in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "*C1RC3 stares at you for a few seconds.* `\"You cannot rename yourself in a game you are not a part of.\"`")
        else:
            player.rename(session, new_name)
            log(get_time() + " >> " + str(context.author) + " renamed to " + new_name + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "*C1RC3 nods.* `\"Very well. I will refer to you as " + new_name + " from now on.\"`")
