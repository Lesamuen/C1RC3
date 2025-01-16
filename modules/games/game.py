"""Module containing methods that are applicable to every game"""

print("Loading module 'game'...")

from random import randint

from discord import ApplicationContext, OptionChoice, User, SlashCommandGroup, option

from ..base.auxiliary import log, get_time, all_zero, ghost_reply, loc, loc_arr, guilds, InvalidArgumentError
from ..base.dbmodels import Game, Player
from ..base.emojis import format_chips
from ..misc.admin import admin_cmds
from ..base.bot import database_connector

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

base_game_cmds = SlashCommandGroup("game_template", "If you can see this, something went wrong", guild_ids = guilds)
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
        log(loc("gen.create.exists.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.create.exists"), True)
    else:
        log(loc("gen.create.log", get_time(), context.guild, context.channel, context.author, expected_type))
        expected_type.create_game(session, context.channel_id, stake)
        await ghost_reply(context, loc("gen.create", loc_arr("gen.create.stake", stake), randint(0, 63)))

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
        log(loc("gen.join.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.none"), True)
    else:
        if game.is_full():
            log(loc("gen.join.full.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.join.full"), True)
        elif game.is_midround():
            # Can't join game in the middle of a round
            log(loc("gen.join.mid.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.join.mid"), True)
        else:
            if game.join_game(session, context.author.id, name) is not None:
                log(loc("gen.join.log", get_time(), context.guild, context.channel, context.author, name))
                await ghost_reply(context, loc("gen.join", name))
                if len(game.players) == 1:
                    # First to join
                    await context.channel.send(loc("gen.join.first"))
            else:
                log(loc("gen.join.re.log", get_time(), context.guild, context.channel, context.author))
                await ghost_reply(context, loc("gen.join.re"), True)

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
        log(loc("gen.lose.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.none"), True)
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("gen.lose.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.lose.spec"), True)
        elif game.is_midround():
            log(loc("gen.lose.mid.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.lose.mid"), True)
        else:
            log(loc("gen.lose.log", get_time(), context.guild, context.channel, context.author))

            name = player.name
            player.leave(session)
            if game.started:
                # Game in progress, so check if only one remaining = overall winner
                log(loc("gen.lose.log", get_time(), context.guild, context.channel, context.author))
                message = [loc("gen.lose", name, name)]
                if len(game.players) == 1:
                    winner: Player = game.players[0]
                    log(loc("gen.lose.win.log", winner.name))
                    message.append(
                        loc("gen.lose.win",
                            winner.name,
                            loc("gen.lose.win.nostake")
                                if game.stake == 0
                                else loc("gen.lose.win.stake",
                                    loc_arr("gen.lose.stake", game.stake - 1),
                                    loc_arr("gen.lose.stake", game.stake + 1),
                                    format_chips([n // 2 for n in winner.get_used()]
                                        if game.stake == 1
                                        else winner.get_used())
                                )
                        )
                    )
                    game.end(session)
                await ghost_reply(context, "".join(message))
            else:
                # Game has not started, so safely left the game; if all left, delete game
                await ghost_reply(context, loc("gen.lose.cancel", name))
                if len(game.players) == 0:
                    log(loc("gen.lose.delete.log"))
                    await context.channel.send(loc("gen.lose.delete"))
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
        log(loc("gen.id.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.none"), True)
    else:
        log(loc("gen.id.log", get_time(), context.guild, context.channel, context.author))
        ids = "".join([
            loc("gen.id.player",
                player.name,
                player.mention(),
                format_chips(player.get_chips()),
                format_chips(player.get_used())
            )
            for player in game.players
        ])
        await ghost_reply(context, loc("gen.id", ids), True)

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
        log(loc("gen.name.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.none"), True)
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("gen.name.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.name.spec"), True)
        else:
            player.rename(session, new_name)
            log(loc("gen.name.log", get_time(), context.guild, context.channel, context.author, new_name))
            await ghost_reply(context, loc("gen.name", new_name), private)

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
        log(loc("gen.chips.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.none"), True)
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("gen.chips.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.chips.spec"), True)
        else:
            log(loc("gen.chips.log", get_time(), context.guild, context.channel, context.author, player.get_chips()))
            await ghost_reply(context, loc("gen.chips", player.name, format_chips(player.get_chips())), private)

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
        log(loc("gen.bet.zero.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.bet.zero"), True)
        return

    session = database_connector()

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(loc("gen.bet.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.none"), True)
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("gen.bet.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.bet.spec"), True)
        elif game.is_midround():
            log(loc("gen.bet.mid.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.bet.mid"), True)
        elif game.get_bet_turn().bet == "[0, 0, 0, 0, 0, 0]" and player != game.get_bet_turn():
            log(loc("gen.bet.turn.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.bet.turn"), True)
        else:
            log(loc("gen.bet.log", get_time(), context.guild, context.channel, context.author, chips))
            player.set_bet(session, chips)
            await ghost_reply(context, loc("gen.bet", player.name, format_chips(chips)))

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
        log(loc("gen.use.zero.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.use.zero"), True)
        return

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(loc("gen.use.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.none"), True)
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("gen.use.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.use.spec"), True)
        elif game.is_midround():
            log(loc("gen.use.mid.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.use.mid"), True)
        else:
            success = player.use_chips(session, chips)
            if success:
                log(loc("gen.use.log", get_time(), context.guild, context.channel, context.author, chips))
                await ghost_reply(context, loc("gen.use", player.name, format_chips(chips)))
            else:
                log(loc("gen.use.poor.log", get_time(), context.guild, context.channel, context.author, chips))
                await ghost_reply(context, loc("gen.use.poor"), True)

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
        log(loc("gen.conv.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.none"), True)
    else:
        player = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("gen.conv.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.conv.spec"), True)
        elif game.is_midround():
            log(loc("gen.conv.mid.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.conv.mid"), True)
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
                log(loc("gen.conv.frac.log", get_time(), context.guild, context.channel, context.author, consumed, produced))
                await ghost_reply(context, loc("gen.conv.frac"), True)
            else:
                # convert to int
                consumed = [int(x) for x in consumed]
                produced = [int(x) for x in produced]
                if player.use_chips(session, consumed, False):
                    player.pay_chips(session, produced)
                    log(loc("gen.conv.log", get_time(), context.guild, context.channel, context.author, consumed, produced))
                    await ghost_reply(context, loc("gen.conv", player.name, format_chips(consumed), format_chips(produced)))
                else:
                    log(loc("gen.conv.poor.log", get_time(), context.guild, context.channel, context.author, consumed, produced))
                    await ghost_reply(context, loc("gen.conv.poor"), True)

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
        log(loc("gen.tfa.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.none"), True)
    else:
        author = game.is_playing(session, context.author.id)
        if author is None:
            log(loc("gen.tfa.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.tfa.spec"), True)
        else:
            target = game.is_playing(session, player.id)
            if target is None:
                log(loc("gen.tfa.wrong.log", get_time(), context.guild, context.channel, context.author))
                await ghost_reply(context, loc("gen.tfa.wrong"), True)
            else:
                target.add_tf_entry(session, description, cost, cost_type)
                log(loc("gen.tfa.log", get_time(), context.guild, context.channel, context.author, [description, cost, cost_type], player))
                await ghost_reply(context, loc("gen.tfa"), True)
    
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
        log(loc("gen.tfr.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.none"), True)
    else:
        author = game.is_playing(session, context.author.id)
        if author is None:
            log(loc("gen.tfr.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.tfr.spec"), True)
        else:
            target = game.is_playing(session, player.id)
            if target is None:
                log(loc("gen.tfr.wrong.log", get_time(), context.guild, context.channel, context.author))
                await ghost_reply(context, loc("gen.tfr.wrong"), True)
            else:
                try:
                    target.remove_tf_entry(session, index)
                except InvalidArgumentError:
                    log(loc("gen.tfr.fail.log", get_time(), context.guild, context.channel, context.author, index, player))
                    await ghost_reply(context, loc("gen.tfr.fail"), True)
                else:
                    log(loc("gen.tfr.log", get_time(), context.guild, context.channel, context.author, index, player))
                    await ghost_reply(context, loc("gen.tfr"), True)
    
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
        log(loc("gen.tfm.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.none"), True)
    else:
        author = game.is_playing(session, context.author.id)
        if author is None:
            log(loc("gen.tfm.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.tfm.spec"), True)
        else:
            target = game.is_playing(session, player.id)
            if target is None:
                log(loc("gen.tfm.wrong.log", get_time(), context.guild, context.channel, context.author))
                await ghost_reply(context, loc("gen.tfm.wrong"), True)
            else:
                try:
                    target.toggle_tf_entry(session, index)
                except InvalidArgumentError:
                    log(loc("gen.tfm.fail.log", get_time(), context.guild, context.channel, context.author, index, player))
                    await ghost_reply(context, loc("gen.tfm.fail"), True)
                else:
                    log(loc("gen.tfm.log", get_time(), context.guild, context.channel, context.author, index, player))
                    await ghost_reply(context, loc("gen.tfm"), True)
    
    session.close()

@base_game_cmds.command(name = "tflist", description = "List the TFs of a player")
@option("player", User, description = "The player to view the TFs of")
async def tflist(context: ApplicationContext, player: User):
    """Add the command /<prefix> tflist <player>

    View the tf entries of another player or yourself
    """

    expected_type: type[Game] = context.command.game_type

    session = database_connector()

    game = expected_type.find_game(session, context.channel_id)
    if game is None:
        log(loc("gen.tfl.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("gen.none"), True)
    else:
        target = game.is_playing(session, player.id)
        if target is None:
            log(loc("gen.tfl.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("gen.tfl.spec"), True)
        elif context.author == player:
            # Viewing own tfs
            log(loc("gen.tfl.self.log", get_time(), context.guild, context.channel, context.author))
            entries = "".join([
                loc("gen.tfl.entry.self", entry[0], entry[1], loc_arr("gen.tfl.types", entry[2]))
                for entry in target.get_tf_entry()
                if entry[3]
            ])
            await ghost_reply(context, loc("gen.tfl.self", entries), True)
        else:
            # Viewing other's tfs
            log(loc("gen.tfl.other.log", get_time(), context.guild, context.channel, context.author, player))
            unfinished = "".join([
                loc("gen.tfl.entry.other", index, entry[0], entry[1], loc_arr("gen.tfl.types", entry[2]))
                for index, entry in enumerate(target.get_tf_entry())
                if not entry[3]
            ])
            finished = "".join([
                loc("gen.tfl.entry.other", index, entry[0], entry[1], loc_arr("gen.tfl.types", entry[2]))
                for index, entry in enumerate(target.get_tf_entry())
                if entry[3]
            ])
            await ghost_reply(context, loc("gen.tfl.other", target.name, unfinished, finished), True)
    
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
        log(loc("admin.gen.end.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("admin.gen.none"), True)
    else:
        log(loc("admin.gen.end.log", get_time(), context.guild, context.channel, context.author))
        game.end(session)
        await ghost_reply(context, loc("admin.gen.end"), private)

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
        log(loc("admin.gen.kick.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("admin.gen.none"), True)
    else:
        player = game.is_playing(session, user.id)
        if player is None:
            log(loc("admin.gen.kick.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("admin.gen.spec"), True)
        else:
            log(loc("admin.gen.kick.log", get_time(), context.guild, context.channel, context.author, user))
            await ghost_reply(context, loc("admin.gen.kick", player.name), private)
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
        log(loc("admin.gen.chips.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("admin.gen.none"), True)
    else:
        player = game.is_playing(session, user.id)
        if player is None:
            log(loc("admin.gen.chips.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("admin.gen.spec"), True)
        else:
            player.set_chips(session, chips)
            log(loc("admin.gen.chips.log", get_time(), context.guild, context.channel, context.author, user, chips))
            await ghost_reply(context, loc("admin.gen.chips", player.name, format_chips(chips)), private)

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
        log(loc("admin.gen.used.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("admin.gen.none"), True)
    else:
        player = game.is_playing(session, user.id)
        if player is None:
            log(loc("admin.gen.used.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("admin.gen.spec"), True)
        else:
            player.set_used(session, chips)
            log(loc("admin.gen.used.log", get_time(), context.guild, context.channel, context.author, user, chips))
            await ghost_reply(context, loc("admin.gen.spec", player.name, format_chips(chips)), private)

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
        log(loc("admin.gen.bet.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("admin.gen.none"), True)
    else:
        game.set_bet(session, chips)
        log(loc("admin.gen.bet.log", get_time(), context.guild, context.channel, context.author, chips))
        await ghost_reply(context, loc("admin.gen.bet", format_chips(chips)), private)

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
        log(loc("admin.gen.stake.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("admin.gen.none"), True)
    else:
        log(loc("admin.gen.stake.log", get_time(), context.guild, context.channel, context.author, stake))
        game.set_stake(session, stake)
        await ghost_reply(context, loc("admin.gen.stake", loc_arr("gen.create.stake", stake)), private)

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
        log(loc("admin.gen.turn.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("admin.gen.none"), True)
    else:
        try:
            game.advance_bet_turn(session, index)
        except:
            log(loc("admin.gen.turn.fail.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("admin.gen.turn.fail"), True)
        else:
            log(loc("admin.gen.turn.log", get_time(), context.guild, context.channel, context.author, index))
            await ghost_reply(context, loc("admin.gen.turn", game.get_bet_turn().name), private)

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
        log(loc("admin.gen.merge.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("admin.gen.none"), True)
    else:
        player1 = game.is_playing(session, kept.id)
        player2 = game.is_playing(session, absorbed.id)
        if player1 is None or player2 is None:
            log(loc("admin.gen.merge.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("admin.gen.spec.mult"), True)
        elif game.is_midround():
            log(loc("admin.gen.merge.mid.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("admin.gen.merge.mid"), True)
        else:
            log(loc("admin.gen.merge.log", get_time(), context.guild, context.channel, context.author, absorbed, kept))
            player1.pay_chips(session, player2.get_chips())
            # Jank way of adding used chips without adding new function lol
            player1.pay_chips(session, player2.get_used())
            player1.use_chips(session, player2.get_used())
            await ghost_reply(context, loc("admin.gen.merge", player2.name, player1.name, player1.name, format_chips(player1.get_chips()), format_chips(player1.get_used())))

            # Combine names
            player1.rename(session, "".join([player1.name, " / ", player2.name]))

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
        log(loc("admin.gen.swap.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("admin.gen.none"), True)
    else:
        player1 = game.is_playing(session, user1.id)
        player2 = game.is_playing(session, user2.id)
        if player1 is None or player2 is None:
            log(loc("admin.gen.swap.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("admin.gen.spec.mult"), True)
        elif game.is_midround():
            log(loc("admin.gen.swap.mid.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("admin.gen.swap.mid"), True)
        else:
            log(loc("admin.gen.swap.log", get_time(), context.guild, context.channel, context.author, user1, user2))

            temp_tfs = player1.get_tf_entry()
            player1.set_tf_entry(session, player2.get_tf_entry())
            player2.set_tf_entry(session, temp_tfs)

            await ghost_reply(context, loc("admin.gen.swap", player1.name, player2.name), True)

    session.close()