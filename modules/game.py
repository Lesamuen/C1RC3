"""Module containing methods that are applicable to every game"""

print("Loading module 'game'...")

from random import randint

from discord import ApplicationContext, OptionChoice, User, SlashCommandGroup, option

from modules.auxiliary import log, get_time, all_zero, ghost_reply, guilds, InvalidArgumentError
from modules.dbmodels import Game, Player
from modules.emojis import format_chips
from modules.admin import admin_cmds
from modules.bot import database_connector

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

base_game_cmds = SlashCommandGroup("game_template", "If you can see this, something went wrong", guild_ids = guilds, guild_only = True)
"""Use .copy() to create another group, then change .name, .description, and then set .game_type for each cmd. Then use bot_client.add_application_command to register"""

@base_game_cmds.command(name = "create", description = "Start a game in this channel")
@option("stake", int, description = "What stake to set the game to", choices = [
        OptionChoice("Low Stakes", 0),
        OptionChoice("Normal Stakes", 1),
        OptionChoice("High Stakes", 2),
    ])
async def create(context: ApplicationContext, stake: int):
    """Add the command /<prefix> create <stake>

    Starts a game in a channel.
    """

    expected_type: type[Game] = context.command.game_type

    session = database_connector()

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
        message += "stakes game has been processed. I am C1RC3 #" + str(randint(0, 63)) + ", and I shall be your table's arbitrator today. Please state your name for the record, in order for your participation to be counted.\"`"
        await ghost_reply(context, message)

    session.close()

@base_game_cmds.command(name = "join", description = "Join a game in this channel")
@option("name", str, description = "The name of your character; how C1RC3 refers to you", min_length = 1, max_length = 20)
async def join(context: ApplicationContext, name: str):
    """Add the command /<prefix> join <name>

    Join a game as a player in a channel.
    """

    expected_type: type[Game] = context.command.game_type

    session = database_connector()

    game: Game = expected_type.find_game(session, context.channel_id)
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
                if len(game.players) == 1:
                    # First to join
                    await context.channel.send("`\"As the first player, you shall be responsible for initiating the first bet of the game.\"`")
            else:
                log(get_time() + " >> " + str(context.author) + " tried to rejoin a game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "`\"You are already part of this table.\"`", True)

    session.close()

@base_game_cmds.command(name = "concede", description = "Declare your loss (i.e. you've been fully TFed)")
async def concede(context: ApplicationContext):
    """Add the command /<prefix> concede

    Forfeit a game.
    """

    expected_type: type[Game] = context.command.game_type

    session = database_connector()
    
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

    session.close()

@base_game_cmds.command(name = "identify", description = "Be reminded of other players' identities and chips")
async def identify(context: ApplicationContext):
    """Add the command /<prefix> identify

    For a player to view others' chips & discord users.
    """

    expected_type: type[Game] = context.command.game_type

    session = database_connector()

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " tried to identify players at an empty table in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`", True)
    else:
        log(get_time() + " >> " + str(context.author) + " identified players in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        message = "`\"The unique soul identifications for each player at this table are:\"`\n"
        for player in game.players:
            message += "**" + player.name + "**: " + player.mention() + "\n"
            message += "    __Chips__: " + format_chips(player.get_chips()) + "\n"
            message += "    __Used__: " + format_chips(player.get_used()) + "\n"
        await ghost_reply(context, message, True)

    session.close()

@base_game_cmds.command(name = "rename", description = "Ask to be called something else")
@option("new_name", str, description = "New name C1RC3 will refer to you by", min_length = 1, max_length = 20)
@option("private", bool, description = "Whether to keep the response only visible to you")
async def rename(context: ApplicationContext, new_name: str, private: bool):
    """Add the command /<prefix> rename <new_name> <private>

    For a player to go by a new name.
    """

    expected_type: type[Game] = context.command.game_type

    session = database_connector()

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

    session.close()

@base_game_cmds.command(name = "chips", description = "Recount how many chips you have in the game")
@option("private", bool, description = "Whether to keep the response only visible to you")
async def chips(context: ApplicationContext, private: bool):
    """Add the command /<prefix> chips <private>

    For a player to view their own chips.
    """

    expected_type: type[Game] = context.command.game_type

    session = database_connector()
    
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

    session.close()

@base_game_cmds.command(name = "bet", description = "Bet an amount of chips")
@option("physical", int, description = "The amount of physical chips to bet", min_value = 0, max_value = 100, default = 0)
@option("mental", int, description = "The amount of mental chips to bet", min_value = 0, max_value = 20, default = 0)
@option("artificial", int, description = "The amount of artificial chips to bet", min_value = 0, max_value = 2, default = 0)
@option("supernatural", int, description = "The amount of supernatural chips to bet", min_value = 0, max_value = 20, default = 0)
@option("merge", int, description = "The amount of merge chips to bet", min_value = 0, max_value = 3, default = 0)
@option("swap", int, description = "The amount of swap chips to bet", min_value = 0, max_value = 25, default = 0)
async def bet(context: ApplicationContext, physical: int, mental: int, artificial: int, supernatural: int, merge: int, swap: int):
    """Add the command /<prefix> bet [chip amounts]
    
    Places a bet for a player in a game.
    """

    expected_type: type[Game] = context.command.game_type

    # Extract chip args
    chips: list[int] = list(locals().values())[1:7]

    if all_zero(chips):
        log(get_time() + " >> " + str(context.author) + " tried to bet nothing in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"You cannot bet nothing.\"`", True)
        return

    session = database_connector()

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
        elif game.get_bet_turn().bet == "[0, 0, 0, 0, 0, 0]" and player != game.get_bet_turn():
            log(get_time() + " >> " + str(context.author) + " tried to bet out of turn in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot bet until the initial bet has been decided on.\"`", True)
        else:
            log(get_time() + " >> " + str(context.author) + " placed bet of " + str(chips) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            player.set_bet(session, chips)
            await ghost_reply(context, "*C1RC3 nods to your request, as she reiterates,* `\"" + player.name + " has placed a bet of:\"`\n## " + format_chips(chips))

    session.close()

@base_game_cmds.command(name = "use", description = "Use an amount of chips from your stash")
@option("physical", int, description = "The amount of physical chips to use", min_value = 0, default = 0)
@option("mental", int, description = "The amount of mental chips to use", min_value = 0, default = 0)
@option("artificial", int, description = "The amount of artificial chips to use", min_value = 0, default = 0)
@option("supernatural", int, description = "The amount of supernatural chips to use", min_value = 0, default = 0)
@option("merge", int, description = "The amount of merge chips to use", min_value = 0, default = 0)
@option("swap", int, description = "The amount of swap chips to use", min_value = 0, default = 0)
async def use(context: ApplicationContext, physical: int, mental: int, artificial: int, supernatural: int, merge: int, swap: int):
    """Add the command /<prefix> use [chip amounts]

    For a player to consume their chips.
    """

    expected_type: type[Game] = context.command.game_type

    # Extract chip args
    chips: list[int] = list(locals().values())[1:7]

    session = database_connector()

    if all_zero(chips):
        log(get_time() + " >> " + str(context.author) + " tried to use no chips in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"You cannot use no chips.\"`", True)
        return

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

    session.close()

@base_game_cmds.command(name = "convert", description = "Convert one type of chips to another")
@option("conversion", int, description = "What types of chips to convert", choices = [
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
])
@option("amount", int, description = "The amount of chips to convert", min_value = 1)
async def convert(context: ApplicationContext, conversion: int, amount: int):
    """Add the command /<prefix> convert <conversion> <amount>

    For a player to dissolve/craft an amount of chips.
    """

    expected_type: type[Game] = context.command.game_type

    session = database_connector()

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
            consumed, produced = chip_conversions[conversion]
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
                if player.use_chips(session, consumed, False):
                    player.pay_chips(session, produced)
                    log(get_time() + " >> " + str(context.author) + " converted " + str(consumed) + " to " + str(produced) + " chips in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await ghost_reply(context, "`\"" + player.name + " has converted:\"`\n## " + format_chips(consumed) + " to " + format_chips(produced))
                else:
                    log(get_time() + " >> " + str(context.author) + " converted more chips than they had (" + str(consumed) + ") in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await ghost_reply(context, "`\"You do not possess enough chips to convert that many.\"`", True)

    session.close()

@base_game_cmds.command(name = "tfadd", description = "Add a TF to a player")
@option("player", User, description = "The player to add a TF to")
@option("description", str, description = "What the TF is", min_length = 1, max_length = 100)
@option("cost", int, description = "How much the TF costs", min_value = 1, max_value = 999)
@option("cost_type", int, description = "What type of chips this costs", choices = [
    OptionChoice("Physical", 0),
    OptionChoice("Mental", 1),
    OptionChoice("Artificial", 2),
    OptionChoice("Supernatural", 3),
    OptionChoice("Merge", 4),
    OptionChoice("Swap", 5),
])
async def tfadd(context: ApplicationContext, player: User, description: str, cost: int, cost_type: int):
    """Add the command /<prefix> tfadd <player> <description> <cost> <cost_type>

    Add a tf entry to another player
    """

    expected_type: type[Game] = context.command.game_type

    session = database_connector()

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " added tf with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`", True)
    else:
        author = game.is_playing(session, context.author.id)
        if author is None:
            log(get_time() + " >> " + str(context.author) + " added tf in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot edit tfs in a game you are not a part of.\"`", True)
        else:
            target = game.is_playing(session, player.id)
            if target is None:
                log(get_time() + " >> " + str(context.author) + " added tf to someone who's not playing in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "`\"You cannot edit the tfs of someone who is not playing.\"`", True)
            else:
                target.add_tf_entry(session, description, cost, cost_type)
                log(get_time() + " >> " + str(context.author) + " added tf " + str([description, cost, cost_type]) + " to " + str(player) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "`\"TF successfully added.\"`", True)
    
    session.close()

@base_game_cmds.command(name = "tfremove", description = "Remove a TF from a player")
@option("player", User, description = "The player to remove a TF from")
@option("index", int, description = "Which TF to remove", min_value = 0)
async def tfremove(context: ApplicationContext, player: User, index: int):
    """Add the command /<prefix> tfremove <player> <index>

    Remove a tf entry from another player
    """

    expected_type: type[Game] = context.command.game_type

    session = database_connector()

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " removed tf with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`", True)
    else:
        author = game.is_playing(session, context.author.id)
        if author is None:
            log(get_time() + " >> " + str(context.author) + " removed tf in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot edit tfs in a game you are not a part of.\"`", True)
        else:
            target = game.is_playing(session, player.id)
            if target is None:
                log(get_time() + " >> " + str(context.author) + " removed tf of someone who's not playing in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "`\"You cannot edit the tfs of someone who is not playing.\"`", True)
            else:
                try:
                    target.remove_tf_entry(session, index)
                except InvalidArgumentError:
                    log(get_time() + " >> " + str(context.author) + " removed tf " + str(index) + " that doesn't exist from " + str(player) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await ghost_reply(context, "`\"You cannot remove a TF that doesn't exist.\"`", True)
                else:
                    log(get_time() + " >> " + str(context.author) + " removed tf " + str(index) + " from " + str(player) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await ghost_reply(context, "`\"TF successfully removed.\"`", True)
    
    session.close()

@base_game_cmds.command(name = "tfmark", description = "Mark a TF of a player as done")
@option("player", User, description = "The player to mark a TF of")
@option("index", int, description = "Which TF to mark as done", min_value = 0)
async def tfmark(context: ApplicationContext, player: User, index: int):
    """Add the command /<prefix> tfmark <player> <index>

    Mark the tf entry of another player as done
    """

    expected_type: type[Game] = context.command.game_type

    session = database_connector()

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " marked tf with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`", True)
    else:
        author = game.is_playing(session, context.author.id)
        if author is None:
            log(get_time() + " >> " + str(context.author) + " marked tf in the wrong game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot edit tfs in a game you are not a part of.\"`", True)
        else:
            target = game.is_playing(session, player.id)
            if target is None:
                log(get_time() + " >> " + str(context.author) + " marked tf of someone who's not playing in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "`\"You cannot edit the tfs of someone who is not playing.\"`", True)
            else:
                try:
                    target.toggle_tf_entry(session, index)
                except InvalidArgumentError:
                    log(get_time() + " >> " + str(context.author) + " marked tf " + str(index) + " that doesn't exist of " + str(player) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await ghost_reply(context, "`\"You cannot mark a TF that doesn't exist.\"`", True)
                else:
                    log(get_time() + " >> " + str(context.author) + " marked tf " + str(index) + " of " + str(player) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await ghost_reply(context, "`\"TF successfully marked.\"`", True)
    
    session.close()

@base_game_cmds.command(name = "tflist", description = "List the TFs of a player")
@option("player", User, description = "The player to view the TFs of")
async def tflist(context: ApplicationContext, player: User):
    """Add the command /<prefix> tflist <player>

    View the tf entries of another player or yourself
    """

    expected_type: type[Game] = context.command.game_type

    session = database_connector()

    cost_types = ["PHYS", "MENT", "ARTI", "SUPE", "MERG", "SWAP"]

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " viewed tfs with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no game of that type running at this table at the moment.\"`", True)
    else:
        target = game.is_playing(session, player.id)
        if target is None:
            log(get_time() + " >> " + str(context.author) + " viewed tfs of someone who's not playing in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot view the tfs of someone who is not playing.\"`", True)
        elif context.author == player:
            # Viewing own tfs
            message = "*Your current TFs:*\n```\n"

            for entry in target.get_tf_entry():
                if entry[3]:
                    message += entry[0] + " (" + str(entry[1]) + " " + cost_types[entry[2]] + ")\n"

            message += "```"

            log(get_time() + " >> " + str(context.author) + " viewed their own tfs in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, message, True)
        else:
            message = "*" + target.name + "'s current TFs:*\n```\nTO DO\n"

            for index, entry in enumerate(target.get_tf_entry()):
                if not entry[3]:
                    message += "    " + str(index) + ": " + entry[0] + " (" + str(entry[1]) + " " + cost_types[entry[2]] + ")\n"

            message += "\nFINISHED\n"

            for index, entry in enumerate(target.get_tf_entry()):
                if entry[3]:
                    message += "    " + str(index) + ": " + entry[0] + " (" + str(entry[1]) + " " + cost_types[entry[2]] + ")\n"

            message += "```"

            log(get_time() + " >> " + str(context.author) + " viewed tfs of " + str(player) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, message, True)
    
    session.close()


game_admin_cmds = admin_cmds.create_subgroup("game", "Admin commands directly related to games in general")

@game_admin_cmds.command(name = "force_end_game", description = "Admin command to end a game in this channel")
@option("private", bool, description = "Whether to keep the response only visible to you", default = False)
async def admin_force_end_game(context: ApplicationContext, private: bool):
    """Add the command /admin game force_end_game
    
    Delete a game
    """

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

@game_admin_cmds.command(name = "remove_player", description = "Admin command to forcibly remove a player from a game")
@option("user", User, description = "User to remove from the game")
@option("private", bool, description = "Whether to keep the response only visible to you", default = False)
async def admin_remove_player(context: ApplicationContext, user: User, private: bool):
    """Add the command /admin game remove_player
    
    Delete a player from a game
    """

    session = database_connector()

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to remove player from no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. There is no game at this table.\"`", True)
    else:
        player = game.is_playing(session, user.id)
        if player is None:
            log(get_time() + " >> Admin " + str(context.author) + " tried to remove non-existent player in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. This person is not playing at this table.\"`", True)
        else:
            log(get_time() + " >> Admin " + str(context.author) + " removed player " + str(user) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. Player " + player.name + " has been forcibly removed from this table.\"`", private)
            player.leave(session)

    session.close()

@game_admin_cmds.command(name = "set_chips", description = "Admin command to manually set chips in a game")
@option("user", User, description = "User whose chips you are editting")
@option("physical", int, description = "The amount of physical chips to set", min_value = 0, default = 0)
@option("mental", int, description = "The amount of mental chips to set", min_value = 0, default = 0)
@option("artificial", int, description = "The amount of artificial chips to set", min_value = 0, default = 0)
@option("supernatural", int, description = "The amount of supernatural chips to set", min_value = 0, default = 0)
@option("merge", int, description = "The amount of merge chips to set", min_value = 0, default = 0)
@option("swap", int, description = "The amount of swap chips to set", min_value = 0, default = 0)
@option("private", bool, description = "Whether to keep the response only visible to you", default = False)
async def admin_set_chips(context: ApplicationContext, user: User, physical: int, mental: int, artificial: int, supernatural: int, merge: int, swap: int, private: bool):
    """Add the command /admin game set_chips
    
    Set a player's chips
    """

    session = database_connector()

    # Extract chip args
    chips: list[int] = list(locals().values())[2:8]

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
            await ghost_reply(context, "`\"Administrator-level Access detected. " + player.name + " now has the following chips:\"`\n## " + format_chips(chips), private)

    session.close()

@game_admin_cmds.command(name = "set_used", description = "Admin command to manually set used chips in a game")
@option("user", User, description = "User whose used chips you are editting")
@option("physical", int, description = "The amount of physical chips to set", min_value = 0, default = 0)
@option("mental", int, description = "The amount of mental chips to set", min_value = 0, default = 0)
@option("artificial", int, description = "The amount of artificial chips to set", min_value = 0, default = 0)
@option("supernatural", int, description = "The amount of supernatural chips to set", min_value = 0, default = 0)
@option("merge", int, description = "The amount of merge chips to set", min_value = 0, default = 0)
@option("swap", int, description = "The amount of swap chips to set", min_value = 0, default = 0)
@option("private", bool, description = "Whether to keep the response only visible to you", default = False)
async def admin_set_used(context: ApplicationContext, user: User, physical: int, mental: int, artificial: int, supernatural: int, merge: int, swap: int, private: bool):
    """Add the command /admin game set_used
    
    Set a player's used chips
    """

    session = database_connector()

    # Extract chip args
    chips: list[int] = list(locals().values())[2:8]

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

@game_admin_cmds.command(name = "set_bet", description = "Admin command to manually change the bet in a game")
@option("physical", int, description = "The amount of physical chips to set", min_value = 0, default = 0)
@option("mental", int, description = "The amount of mental chips to set", min_value = 0, default = 0)
@option("artificial", int, description = "The amount of artificial chips to set", min_value = 0, default = 0)
@option("supernatural", int, description = "The amount of supernatural chips to set", min_value = 0, default = 0)
@option("merge", int, description = "The amount of merge chips to set", min_value = 0, default = 0)
@option("swap", int, description = "The amount of swap chips to set", min_value = 0, default = 0)
@option("private", bool, description = "Whether to keep the response only visible to you", default = False)
async def admin_set_bet(context: ApplicationContext, physical: int, mental: int, artificial: int, supernatural: int, merge: int, swap: int, private: bool):
    """Add the command /admin game set_bet
    
    Set game's bet
    """

    session = database_connector()

    # Extract chip args
    chips: list[int] = list(locals().values())[1:7]

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to set bet with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. There is no game at this table.\"`", True)
    else:
        game.set_bet(session, chips)
        log(get_time() + " >> Admin " + str(context.author) + " set bet to " + str(chips) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"Administrator-level Access detected. The bet in this game has been has been updated to:\"`\n## " + format_chips(chips), private)

    session.close()

@game_admin_cmds.command(name = "set_stake", description = "Admin command to change the stake of a game in this channel")
@option("stake", int, description = "What stake to set the game to", choices = [
    OptionChoice("Low Stakes", 0),
    OptionChoice("Normal Stakes", 1),
    OptionChoice("High Stakes", 2),
])
@option("private", bool, description = "Whether to keep the response only visible to you", default = False)
async def admin_set_stake(context: ApplicationContext, stake: int, private: bool):
    """Add the command /admin game set_stake
    
    Set game's stake
    """

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

@game_admin_cmds.command(name = "set_bet_turn", description = "Admin command to change whose turn it is to bet in a game")
@option("index", int, description = "Index of player to set bet turn to", min_value = 0)
@option("private", bool, description = "Whether to keep the response only visible to you", default = False)
async def admin_set_bet_turn(context: ApplicationContext, index: int, private: bool):
    """Add the command /admin game set_bet_turn
    
    Set game's bet turn
    """

    session = database_connector()

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to change bet turn for no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. There is no game at this table.\"`", True)
    else:
        try:
            game.advance_bet_turn(session, index)
        except:
            log(get_time() + " >> Admin " + str(context.author) + " tried to change bet turn of game out of bounds in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. Index is out of bounds of player list.\"`", True)
        else:
            log(get_time() + " >> Admin " + str(context.author) + " changed bet turn of game to " + str(index) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. It is now " + game.get_bet_turn().name + "'s turn to initiate the bet.\"`", private)

    session.close()

@game_admin_cmds.command(name = "merge", description = "Admin command to merge two players in a game")
@option("kept", User, description = "Player that will keep their body")
@option("absorbed", User, description = "Player that will be merged into the other")
async def admin_merge(context: ApplicationContext, kept: User, absorbed: User):
    """Add the command /admin game merge
    
    Merge two players
    """

    session = database_connector()

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to merge players for no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. There is no game at this table.\"`", True)
    else:
        player1 = game.is_playing(session, kept.id)
        player2 = game.is_playing(session, absorbed.id)
        if player1 is None or player2 is None:
            log(get_time() + " >> Admin " + str(context.author) + " tried to merge non-players in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. One or more of these people is not playing at this table.\"`", True)
        elif game.is_midround():
            log(get_time() + " >> Admin " + str(context.author) + " tried to merge players midround in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. I am unable to merge players in the middle of a round.\"`", True)
        else:
            log(get_time() + " >> Admin " + str(context.author) + " merged players " + str(absorbed) + " into " + str(kept) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. Merge request has been processed. " + player2.name + "'s chips and winnings shall be combined with " + player1.name + "'s.\"`")
            player1.pay_chips(session, player2.get_chips())
            # Jank way of adding used chips without adding new function lol
            player1.pay_chips(session, player2.get_used())
            player1.use_chips(session, player2.get_used())
            await context.channel.send("`\"" + player1.name + " now has:\"`\n## " + format_chips(player1.get_chips()) + "\n`\"and has used:\"`\n## " + format_chips(player1.get_used()))

            # Combine names
            player1.rename(session, player1.name + " / " + player2.name)

            # Delete old player
            player2.leave(session)

    session.close()

@game_admin_cmds.command(name = "swap", description = "Admin command to swap two players in a game")
@option("user1", User, description = "Player to be swapped")
@option("user2", User, description = "Player to be swapped")
async def admin_swap(context: ApplicationContext, user1: User, user2: User):
    """Add the command /admin game swap
    
    Swap two players' tf lists
    """

    session = database_connector()

    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to swap players for no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. There is no game at this table.\"`", True)
    else:
        player1 = game.is_playing(session, user1.id)
        player2 = game.is_playing(session, user2.id)
        if player1 is None or player2 is None:
            log(get_time() + " >> Admin " + str(context.author) + " tried to swap non-players in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. One or more of these people is not playing at this table.\"`", True)
        elif game.is_midround():
            log(get_time() + " >> Admin " + str(context.author) + " tried to swap players midround in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. Request failed. I am unable to merge players in the middle of a round.\"`", True)
        else:
            temp_tfs = player1.get_tf_entry()
            player1.set_tf_entry(session, player2.get_tf_entry())
            player2.set_tf_entry(session, temp_tfs)

            log(get_time() + " >> Admin " + str(context.author) + " swapped players " + str(user1) + " and " + str(user2) + " in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"Administrator-level Access detected. Player swap has been processed.\"`", True)

    session.close()