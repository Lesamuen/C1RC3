"""Module containing methods that are applicable to every game"""

print("Loading module 'game'...")

from typing import List, Tuple

from discord import ApplicationContext, Option, Member, OptionChoice
from sqlalchemy.orm import Session

from auxiliary import log, get_time, all_zero, ghost_reply, guilds
from dbmodels import Game, Player
from emojis import format_chips
from admin import admin_cmds
from bot import database_connector

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

async def create(context: ApplicationContext, session: Session, stake: int, expected_type: type[Game]) -> None:
    """Handle functionality for creating any game
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    session: sqlalchemy.orm.Session
        Current database scope
    stake: int
        Code for the stake level of the created game
    expected_type: type[dbmodels.Game]
        Game subclass this command was sent for
    """

    game = Game.find_game(session, context.channel_id)
    if game is not None:
        log(get_time() + " >> " + str(context.author) + " tried to create another game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is already a game running at this table.\"`", True)
    else:
        expected_type.create_game(session, context.channel_id, stake)
        log(get_time() + " >> " + str(context.author) + " started a " + str(expected_type) + " game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        message = "*C1RC3 approaches you when you call for a dealer, and takes her place at the dealer's stand.*\n`\"Your request for a "
        if stake == 0:
            message += "low "
        elif stake == 1:
            message += "normal "
        elif stake == 2:
            message += "high "
        message += "stakes game has been processed. I will be acting as your table's arbitrator. Please state your name for the record, in order for your participation to be counted.\"`"
        await ghost_reply(context, message)

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
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`", True)
    else:
        if game.is_full():
            log(get_time() + " >> " + str(context.author) + " tried to join a full game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"This table is already full.\"`", True)
        elif game.is_midround():
            # Can't join game in the middle of a round
            log(get_time() + " >> " + str(context.author) + " tried to join a game mid-round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"This table is in the middle of a round; please wait until the round is over before joining.\"`", True)
        else:
            if game.join_game(session, context.author.id, name) is not None:
                log(get_time() + " >> " + str(context.author) + " joined a game as " + name + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "*C1RC3 nods.* `\"Request accepted. " + name + " is now participating in this game.\"`")
            else:
                log(get_time() + " >> " + str(context.author) + " tried to rejoin a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "`\"...You are already part of this table.\"`", True)

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
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`", True)
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to concede from the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot concede a game you are not a part of.\"`", True)
        elif game.is_midround():
            log(get_time() + " >> " + str(context.author) + " tried to concede mid-game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot concede right now, in the middle of a round.\"`", True)
        else:
            log(get_time() + " >> " + str(context.author) + " conceded from a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")

            name = player.name
            player.leave(session)
            if game.started:
                # Game in progress, so check if only one remaining = overall winner
                message = "`\"Understood. Player " + name + " has officially conceded.\"`\n*C1RC3 snaps her fingers as the magic of the casino flows into "\
                     + name + ", solidifying their new form. Any of their remaining chips fade as multicolored light shoots out of them, reabsorbed into C1RC3 as her frame shivers."\
                    " She then pulls them into an open compartment in her abdomen, where it closes shut seamlessly.*\n"
                if len(game.players) == 1:
                    winner: Player = game.players[0]
                    log("                     >> Game ended with winner " + winner.name + ".")
                    message += "\n*C1RC3 turns to the last player.* `\"Congratulations, " + winner.name + ", you have won against everyone at the table.\n"\
                        "You may choose to transform back to your original form at the beginning of the game, or keep your current one if it is complete.\n"
                    if game.stake == 0:
                        message += "Because this table was playing at low stakes, you unfortunately do not keep these.\"`"\
                            " *She reaches over and shovels your remaining chips into herself, absorbing their magic as well.*\n"\
                            "*She then turns to the other players.* `\"The rest of you, please enjoy your temporary forms while they last.\"`"
                    elif game.stake == 1:
                        message += "Because this table was playing at normal stakes, you shall receive half of the chips you have used thus far.\"`\n"
                        roi = winner.get_used()
                        roi = [n // 2 for n in roi]
                        message += "*She places her hands on the table and leans forward, while the sound of clinking chips comes from her body. "\
                            "Eventually, the compartment in her midriff slides open, and out flows a great pile of dull, magicless chips, totalling:*\n# "
                        message += format_chips(roi)
                        message += "\n*While she pulls your unused chips back into herself, she explains with an even tone,* "\
                            "`\"You may come see me or any staff member later to have the magic reinfused into them so you may use them on yourself to change your own form to your liking."\
                            " Otherwise, you may store them with me.\"`"
                    elif game.stake == 2:
                        message += "Because this table was playing at high stakes, you shall receive all of the chips you have used on others thus far.\"`\n"
                        roi = winner.get_used()
                        message += "*She places her hands on the table and leans forward, while the sound of clinking chips comes from her body. "\
                            "Eventually, the compartment in her midriff slides open, and out flows a great pile of dull, magicless chips, totalling:*\n# "
                        message += format_chips(roi)
                        message += "\n*While she pulls your unused chips back into herself, she explains with an even tone,*"\
                            "`\"You may come see me or any staff member later to have the magic reinfused into them so you may use them on yourself to change your own form to your liking."\
                            " May fortune continue to find you.\"`"
                    message += "\n*With that, C1RC3 walks off to attend to other tables.*"
                    game.end(session)
                await ghost_reply(context, message)
            else:
                # Game has not started, so safely left the game; if all left, delete game
                await ghost_reply(context, "`\"Understood. Player " + name + " has changed their mind.\"`")
                if len(game.players) == 0:
                    log("                     >> Game deleted as all players left.")
                    await context.channel.send("*With no one left sitting at the table, C1RC3 simply walks off to attend to other tables.*")
                    game.end(session)

async def chips(context: ApplicationContext, session: Session, private: bool, expected_type: type[Game]) -> None:
    """Handle functionality for viewing chips in any game
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    session: sqlalchemy.orm.Session
        Current database scope
    private: bool
        Whether bot responds to user in private
    expected_type: type[dbmodels.Game]
        Game subclass this command was sent for
    """
    
    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to view chips with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`", True)
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to view chips in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You do not have any chips for game you are not a part of.\"`", True)
        else:
            log(get_time() + " >> " + str(context.author) + " viewed chips (" + str(player.get_chips()) + ") in a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + ", you currently have:\"`\n# " + format_chips(player.get_chips()), private)

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
        await ghost_reply(context, "`\"You cannot bet nothing.\"`", True)
        return (False, None)

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to bet with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`", True)
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to bet in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot bet in a game you are not a part of.\"`", True)
        elif game.is_midround():
            log(get_time() + " >> " + str(context.author) + " tried to bet mid-game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot bet right now, in the middle of a round.\"`", True)
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
        await ghost_reply(context, "You cannot use no chips.\"`", True)

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to use chips with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`", True)
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to use chips in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot use chips in a game you are not a part of.\"`", True)
        elif game.is_midround():
            log(get_time() + " >> " + str(context.author) + " tried to use chips mid-game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot use chips right now, in the middle of a round.\"`", True)
        else:
            success = player.use_chips(session, chips)
            if success:
                log(get_time() + " >> " + str(context.author) + " used " + str(chips) + " chips in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "`\"" + player.name + " has used:\"`\n## " + format_chips(chips))
            else:
                log(get_time() + " >> " + str(context.author) + " tried to use " + str(chips) + " chips in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "`\"You do not possess enough chips to use that many.\"`", True)

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
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`", True)
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to convert chips in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot convert chips in a game you are not a part of.\"`", True)
        elif game.is_midround():
            log(get_time() + " >> " + str(context.author) + " tried to convert chips mid-game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot convert chips right now, in the middle of a round.\"`", True)
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
                await ghost_reply(context, "`\"That conversion would result in a fractional chip; please pay attention to the conversion ratios.\"`", True)
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
                    await ghost_reply(context, "`\"You do not possess enough chips to convert that many.\"`", True)
           
async def rename(context: ApplicationContext, session: Session, new_name: str, private: bool, expected_type: type[Game]) -> None:
    """Handle functionality for renaming a player in any game
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    session: sqlalchemy.orm.Session
        Current database scope
    new_name: str
        The new name to set the player to
    private: bool
        Whether bot responds to user in private
    expected_type: type[dbmodels.Game]
        Game subclass this command was sent for
    """

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to rename with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`", True)
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " tried to rename in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot rename yourself in a game you are not a part of.\"`", True)
        else:
            player.rename(session, new_name)
            log(get_time() + " >> " + str(context.author) + " renamed to " + new_name + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "*C1RC3 nods.* `\"Very well. I will refer to you as " + new_name + " from now on.\"`", private)

game_admin_cmds = admin_cmds.create_subgroup("game", "Admin commands directly related to games in general")

@game_admin_cmds.command(name = "force_end_game", description = "Admin command to end a game in this channel")
async def force_end_game(
    context: ApplicationContext,
    private: Option(bool, description = "Whether to keep the response only visible to you", default = False)
):
    """Add the command /admin game force_end_game"""

    session = database_connector()

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to force-end a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. There is already no game at this table.\"`", True)
    else:
        log(get_time() + " >> Admin " + str(context.author) + " force-ended a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        game.end(session)
        await ghost_reply(context, "`\"Administrator-level Access detected. The game running for this table has been forcibly ended.\"`", private)

    session.close()

@game_admin_cmds.command(name = "set_chips", description = "Admin command to manually set chips in a game")
async def set_chips(
    context: ApplicationContext,
    user: Option(Member, description = "User whose chips you are editting", required = True),
    physical: Option(int, description = "The amount of physical chips to set", min_value = 0, default = 0),
    mental: Option(int, description = "The amount of mental chips to set", min_value = 0, default = 0),
    artificial: Option(int, description = "The amount of artificial chips to set", min_value = 0, default = 0),
    supernatural: Option(int, description = "The amount of supernatural chips to set", min_value = 0, default = 0),
    merge: Option(int, description = "The amount of merge chips to set", min_value = 0, default = 0),
    swap: Option(int, description = "The amount of swap chips to set", min_value = 0, default = 0),
    private: Option(bool, description = "Whether to keep the response only visible to you", default = False)
):
    """Add the command /admin game set_chips"""

    session = database_connector()

    # Extract chip args
    chips: List[int] = list(locals().values())[2:8]

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to set chips with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. There is no game at this table.\"`", True)
    else:
        player = game.is_playing(session, user.id)
        if player is None:
            log(get_time() + " >> Admin " + str(context.author) + " tried to set chips for a non-player in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. This person is not playing at this table.\"`", True)
        else:
            player.set_chips(session, chips)
            log(get_time() + " >> Admin " + str(context.author) + " set chips of " + str(user) + " to " + str(chips) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. " + player.name + " has been granted the following chips:\"`\n## " + format_chips(chips), private)

    session.close()

@game_admin_cmds.command(name = "set_used", description = "Admin command to manually set used chips in a game")
async def set_used(
    context: ApplicationContext,
    user: Option(Member, description = "User whose used chips you are editting", required = True),
    physical: Option(int, description = "The amount of physical chips to set", min_value = 0, default = 0),
    mental: Option(int, description = "The amount of mental chips to set", min_value = 0, default = 0),
    artificial: Option(int, description = "The amount of artificial chips to set", min_value = 0, default = 0),
    supernatural: Option(int, description = "The amount of supernatural chips to set", min_value = 0, default = 0),
    merge: Option(int, description = "The amount of merge chips to set", min_value = 0, default = 0),
    swap: Option(int, description = "The amount of swap chips to set", min_value = 0, default = 0),
    private: Option(bool, description = "Whether to keep the response only visible to you", default = False)
):
    """Add the command /admin game set_used"""

    session = database_connector()

    # Extract chip args
    chips: List[int] = list(locals().values())[2:8]

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to set used chips with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. There is no game at this table.\"`", True)
    else:
        player = game.is_playing(session, user.id)
        if player is None:
            log(get_time() + " >> Admin " + str(context.author) + " tried to set used chips for a non-player in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. This person is not playing at this table.\"`", True)
        else:
            player.set_used(session, chips)
            log(get_time() + " >> Admin " + str(context.author) + " set used chips of " + str(user) + " to " + str(chips) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. " + player.name + "'s used chips record has been has been updated to:\"`\n## " + format_chips(chips), private)

    session.close()

@game_admin_cmds.command(name = "set_stake", description = "Admin command to change the stake of a game in this channel")
async def set_stake(
    context: ApplicationContext,
    stake: Option(int, description = "What stake to set the game to", required = True, choices = [
        OptionChoice("Low Stakes", 0),
        OptionChoice("Normal Stakes", 1),
        OptionChoice("High Stakes", 2),
    ]),
    private: Option(bool, description = "Whether to keep the response only visible to you", default = False)
):
    """Add the command /admin game set_stake"""

    session = database_connector()

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to change stake for no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. There is no game at this table.\"`", True)
    else:
        log(get_time() + " >> Admin " + str(context.author) + " changed stake of game to " + str(stake) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        game.set_stake(session, stake)
        message = "`\"Administrator-level Access detected. The stake of this game has been set to "
        if stake == 0:
            message += "Low."
        elif stake == 1:
            message += "Normal."
        elif stake == 2:
            message += "High."
        message += "\"`"
        await ghost_reply(context, message, private)

    session.close()
