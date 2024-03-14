"""This module relates to the game 'Blackjack'."""

from typing import List

from discord import ApplicationContext, Option, OptionChoice
from sqlalchemy.orm import Session

from bot import bot_client, database_connector
from auxiliary import perms, guilds, log, get_time, all_zero
from dbmodels import Blackjack, BlackjackPlayer, Game
from emojis import standard_deck, format_cards
from game import bet, concede, chips, use, convert

bj_cmds = bot_client.create_group("bj", "Commands to run the game of Blackjack", guild_ids = guilds, guild_only = True)

@bj_cmds.command(name = "join", description = "Join a Blackjack game in this channel, or creates one if there isn't one")
async def bj_join(
    context: ApplicationContext,
    name: Option(str, description = "Name that C1RC3 will refer to you as", required = True, min_length = 1)
):
    """Adds the command /bj join"""

    session = database_connector()

    game: Blackjack = Blackjack.find_game(session, context.channel_id)
    if game is not None:
        if game.type != "blackjack":
            log(get_time() + " >> " + str(context.author) + " tried to join a non-Blackjack game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: non-bj game in channel already")
        else:
            # Try to join existing game
            if game.is_full():
                log(get_time() + " >> " + str(context.author) + " tried to join a full Blackjack game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await context.respond(".", ephemeral = True, delete_after = 0)
                await context.channel.send("PLACEHOLDER: game full")
            elif game.is_midround():
                # Can't join game in the middle of a round
                log(get_time() + " >> " + str(context.author) + " tried to join a Blackjack game mid-round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await context.respond(".", ephemeral = True, delete_after = 0)
                await context.channel.send("PLACEHOLDER: round currently ongoing")
            else:
                if (player := game.join_game(session, context.author.id, name)) is not None:
                    log(get_time() + " >> " + str(context.author) + " joined a Blackjack game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await context.respond(".", ephemeral = True, delete_after = 0)
                    await context.channel.send("PLACEHOLDER: " + player.name + " successfully joined game")
                else:
                    log(get_time() + " >> " + str(context.author) + " tried to rejoin a Blackjack game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await context.respond(".", ephemeral = True, delete_after = 0)
                    await context.channel.send("PLACEHOLDER: already in game")
    else:
        # Create new game if no game exists yet
        player = Blackjack.create_game(session, context.channel_id).join_game(session, context.author.id, name)
        log(get_time() + " >> " + str(context.author) + " started a Blackjack game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: " + player.name + " started new game")

    session.close()

@bj_cmds.command(name = "rename", description = "Ask C1RC3 to call you something else, in case your name has been changed")
async def bj_rename(
    context: ApplicationContext,
    name: Option(str, description = "Name that C1RC3 will refer to you as", required = True, min_length = 1)
):
    """Adds the command /bj rename"""

    log(get_time() + " >> " + str(context.author) + " tried to rename themselves in [" + str(context.guild) + "], [" + str(context.channel) + "]")
    await context.respond(".", ephemeral = True, delete_after = 0)
    await context.channel.send("PLACEHOLDER: not implemented yet srry")

@bj_cmds.command(name = "bet", description = "Bet an amount of chips")
async def bj_bet(
    context: ApplicationContext,
    phys_chips: Option(int, description = "The amount of physical chips to bet", min_value = 0, default = 0),
    ment_chips: Option(int, description = "The amount of mental chips to bet", min_value = 0, default = 0),
    arti_chips: Option(int, description = "The amount of artificial chips to bet", min_value = 0, default = 0),
    supe_chips: Option(int, description = "The amount of supernatural chips to bet", min_value = 0, default = 0),
    merg_chips: Option(int, description = "The amount of merging chips to bet", min_value = 0, default = 0),
    swap_chips: Option(int, description = "The amount of swap chips to bet", min_value = 0, default = 0)
):
    """Adds the command /bj bet"""

    # Extract chip args
    chips: List[int] = list(locals().values())[1:7]

    session = database_connector()

    game: Blackjack
    player: BlackjackPlayer
    bet_placed, game = await bet(context, session, chips, "blackjack")

    if bet_placed:
        if game.bets_aligned():
            log(get_time() + " >> The Blackjack round has started in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            game.set_bet(session, chips)

            shuffled = game.start_round(session)
            if shuffled:
                await context.channel.send("PLACEHOLDER: deck was shuffled")

            await context.channel.send("PLACEHOLDER: bets aligned. round start")
            await context.channel.send("PLACEHOLDER: insert cards here (just use /bj hand for now)")
            await context.channel.send("PLACEHOLDER: first turn is " + game.get_turn_name())

    session.close()

@bj_cmds.command(name = "hand", description = "Peek at the hand you've been given")
async def bj_hand(
    context: ApplicationContext
):
    """Adds the command /bj hand"""

    session = database_connector()
    
    game = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " looked at their Blackjack hand with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: no game here")
    elif game.type != "blackjack":
        log(get_time() + " >> " + str(context.author) + " looked at their Blackjack hand with a different game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: not blackjack")
    else:
        player: BlackjackPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " looked at their Blackjack hand with a game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: you're not part of this game")
        elif not game.is_midround():
            log(get_time() + " >> " + str(context.author) + " looked at their Blackjack hand outside of a round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: round hasn't started")
        else:
            log(get_time() + " >> " + str(context.author) + " looked at their Blackjack hand in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond("PLACEHOLDER: your cards; this message will disappear in 30 seconds\n" + format_cards(standard_deck, player.get_hand()), ephemeral = True, delete_after = 30)

    session.close()

@bj_cmds.command(name = "hit", description = "Ask C1RC3 for a card...will you bust?")
async def bj_hit(
    context: ApplicationContext
):
    """Adds the command /bj hit"""

    session = database_connector()
    
    game: Blackjack = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " hit in Blackjack with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: no game here")
    elif game.type != "blackjack":
        log(get_time() + " >> " + str(context.author) + " hit in Blackjack while it wasn't Blackjack in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: not blackjack")
    else:
        player: BlackjackPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " hit in a Blackjack game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: you're not part of this game")
        elif not game.is_midround():
            log(get_time() + " >> " + str(context.author) + " hit in Blackjack outside of a round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: round hasn't started")
        elif game.get_turn() != context.author.id:
            log(get_time() + " >> " + str(context.author) + " hit in Blackjack outside of their turn in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: not your turn")
        else:
            # No need to test for hit state; if standing or busted it cannot be their turn already
            log(get_time() + " >> " + str(context.author) + " hit in Blackjack in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            drawn = game.draw(session, 1)
            await context.channel.send("PLACEHOLDER: " + player.name + " drew the card\n" + format_cards(standard_deck, [drawn]))
            if player.add_card(session, drawn):
                # Test for 5 card charlie
                if len(player.get_hand()) == 5:
                    await bj_end_round(context, session, game)
                else:
                    game.next_turn(session)
            else:
                # Busted, so test for round end
                await context.channel.send("PLACEHOLDER: " + player.name + " busted")
                if game.is_all_done():
                    await bj_end_round(context, session, game)
                else:
                    # Round didn't end with bust
                    game.next_turn(session)

    session.close()

@bj_cmds.command(name = "stand", description = "Keep your current hand until the end of the round")
async def bj_stand(
    context: ApplicationContext
):
    """Adds the command /bj stand"""

    session = database_connector()
    
    game: Blackjack = Game.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " stood in Blackjack with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: no game here")
    elif game.type != "blackjack":
        log(get_time() + " >> " + str(context.author) + " stood in Blackjack while it wasn't Blackjack in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await context.respond(".", ephemeral = True, delete_after = 0)
        await context.channel.send("PLACEHOLDER: not blackjack")
    else:
        player: BlackjackPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " stood in a Blackjack game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: you're not part of this game")
        elif not game.is_midround():
            log(get_time() + " >> " + str(context.author) + " stood in Blackjack outside of a round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: round hasn't started")
        elif game.get_turn() != context.author.id:
            log(get_time() + " >> " + str(context.author) + " stood in Blackjack outside of their turn in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: not your turn")
        else:
            log(get_time() + " >> " + str(context.author) + " stood in Blackjack in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await context.respond(".", ephemeral = True, delete_after = 0)
            await context.channel.send("PLACEHOLDER: " + player.name + " stood")
            player.stand(session)

            # player stood, so test for round end
            if game.is_all_done():
                await bj_end_round(context, session, game)
            else:
                # Round didn't end with stand
                game.next_turn(session)

    session.close()

@bj_cmds.command(name = "concede", description = "You lost (use when fully TFed or at the end of a mental round)")
async def bj_concede(
    context: ApplicationContext
):
    """Adds the command /bj concede"""

    session = database_connector()

    await concede(context, session, "blackjack")

    session.close()

@bj_cmds.command(name = "chips", description = "Recount how many chips you have in your current pile")
async def bj_chips(
    context: ApplicationContext
):
    """Adds the command /bj chips"""

    session = database_connector()

    await chips(context, session, "blackjack")

    session.close()

@bj_cmds.command(name = "use", description = "Use an amount of chips from your current pile")
async def bj_use(
    context: ApplicationContext,
    phys_chips: Option(int, description = "The amount of physical chips to use", min_value = 0, default = 0),
    ment_chips: Option(int, description = "The amount of mental chips to use", min_value = 0, default = 0),
    arti_chips: Option(int, description = "The amount of artificial chips to use", min_value = 0, default = 0),
    supe_chips: Option(int, description = "The amount of supernatural chips to use", min_value = 0, default = 0),
    merg_chips: Option(int, description = "The amount of merging chips to use", min_value = 0, default = 0),
    swap_chips: Option(int, description = "The amount of swap chips to use", min_value = 0, default = 0)
):
    """Adds the command /bj use"""

    # Extract chip args
    chips: List[int] = list(locals().values())[1:7]

    session = database_connector()

    await use(context, session, chips, "blackjack")

    session.close()

@bj_cmds.command(name = "convert", description = "Convert one type of chips to another")
async def bj_convert(
    context: ApplicationContext,
    type: Option(int, description = "What chips to convert", required = True, choices = [
        OptionChoice("Dissolve Mental", 0),
        OptionChoice("Dissolve Artificial", 1),
        OptionChoice("Craft Artificial", 2),
        OptionChoice("Dissolve Supernatural to Physical", 3),
        OptionChoice("Dissolve Supernatural to Mental", 4),
        OptionChoice("Craft Supernatural from Physical", 5),
        OptionChoice("Craft Supernatural from Mental", 6),
        OptionChoice("Dissolve Merge to Physical", 7),
        OptionChoice("Dissolve Merge to Mental", 8),
        OptionChoice("Dissolve Swap to Physical", 9),
        OptionChoice("Dissolve Swap to Mental", 10),
    ]),
    amount: Option(int, description = "The amount of chips to convert", min_value = 1, default = 1)
):
    """Adds the command /bj convert"""

    session = database_connector()

    await convert(context, session, type, amount, "blackjack")

    session.close()

async def bj_end_round(context: ApplicationContext, session: Session, game: Blackjack) -> None:
    """Does round end stuff"""

    log(get_time() + " >> " + str(context.author) + " Blackjack round ended in [" + str(context.guild) + "], [" + str(context.channel) + "]")
    await context.channel.send("PLACEHOLDER: round ended")
    for player in game.players:
        await context.channel.send("## __" + player.name + "__\n" + format_cards(standard_deck, player.get_hand()))
    
    # End the round
    win_con, winners = game.end_round(session)
    if len(winners) == 1:
        if win_con == "f":
            await context.channel.send("PLACEHOLDER: " + winners[0][1] + " won w/ 5-card charlie")
        elif win_con == "b":
            await context.channel.send("PLACEHOLDER: " + winners[0][1] + " won w/ blackjack")
        else:
            await context.channel.send("PLACEHOLDER: " + winners[0][1] + " won")
    else:
        if win_con == "b":
            await context.channel.send("PLACEHOLDER: " + str([winner[1] for winner in winners]) + " tied w/ blackjack")
        else:
            await context.channel.send("PLACEHOLDER: " + str([winner[1] for winner in winners]) + " tied")
        
        # Start new round because tied
        shuffled = game.start_round(session, [winner[0] for winner in winners])
        if shuffled:
            await context.channel.send("PLACEHOLDER: deck was shuffled")
        await context.channel.send("PLACEHOLDER: insert cards here (just use /bj hand for now)")
        await context.channel.send("PLACEHOLDER: first turn is " + game.get_turn_name())