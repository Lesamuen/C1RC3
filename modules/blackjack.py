"""This module relates to the game 'Blackjack'."""

from typing import List

from discord import ApplicationContext, Option, OptionChoice
from sqlalchemy.orm import Session

from bot import bot_client, database_connector
from auxiliary import guilds, log, get_time, ghost_reply
from dbmodels import Blackjack, BlackjackPlayer, Game
from emojis import standard_deck, format_cards, format_chips
from game import bet, concede, chips, use, convert, rename

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
            await ghost_reply(context, "`\"There is already a different game running at this table.\"`")
        else:
            # Try to join existing game
            if game.is_full():
                log(get_time() + " >> " + str(context.author) + " tried to join a full Blackjack game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "`\"This table is already full.\"`")
            elif game.is_midround():
                # Can't join game in the middle of a round
                log(get_time() + " >> " + str(context.author) + " tried to join a Blackjack game mid-round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                await ghost_reply(context, "`\"This table is in the middle of a round; please wait until the round is over before joining.\"`")
            else:
                if (player := game.join_game(session, context.author.id, name)) is not None:
                    log(get_time() + " >> " + str(context.author) + " joined a Blackjack game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await ghost_reply(context, "*C1RC3 nods.* `\"Request accepted. " + player.name + ", please be seated before the round begins.\"`")
                else:
                    log(get_time() + " >> " + str(context.author) + " tried to rejoin a Blackjack game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
                    await ghost_reply(context, "*C1RC3 stays silent for a couple of seconds as she tries to process your request.\n`\"...You are already part of this table.\"`")
    else:
        # Create new game if no game exists yet
        player = Blackjack.create_game(session, context.channel_id).join_game(session, context.author.id, name)
        log(get_time() + " >> " + str(context.author) + " started a Blackjack game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "*C1RC3 approaches you as you ring the bell on the table, and takes her place at the dealer's stand.*\n`\"Your request has been processed.\"`\n*She turns to the rest of the floor, as she announces with her voice amplified,*\n`\""
             + player.name + " has begun a new blackjack game!\"`")

    session.close()

@bj_cmds.command(name = "rename", description = "Ask C1RC3 to call you something else, in case your name has been changed")
async def bj_rename(
    context: ApplicationContext,
    name: Option(str, description = "Name that C1RC3 will refer to you as", required = True, min_length = 1)
):
    """Adds the command /bj rename"""

    session = database_connector()

    await rename(context, session, name, "blackjack")

    session.close()

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

            message = "`\"The players have agreed on a bet. The round shall now begin.\"`\n"
            if shuffled:
                message += "*Before C1RC3 begins to draw cards, she places all of the cards into a compartment that slides open in her arm, and shuts it."\
                    " A moment of whirring later, she opens it again and pulls out a newly shuffled deck.*\n"
            message += "*She begins to draw cards from the deck, deftly placing them down in front of each player.*\n"
            for player in game.players:
                message += "## __" + player.name + "__\n"
                hand = player.get_hand()
                if len(hand) >= 2:
                    hand[1] = 52
                message += "# " + format_cards(standard_deck, hand) + "\n"
            message += "`\"The first turn goes to " + game.get_turn_name() + " this round.\"`"
            
            await context.channel.send(message)

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
        await ghost_reply(context, "`\"There is no game running at this table at the moment.\"`")
    elif game.type != "blackjack":
        log(get_time() + " >> " + str(context.author) + " looked at their Blackjack hand with a different game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is a different type of game running at this table at the moment; you may be at the wrong table.\"`")
    else:
        player: BlackjackPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " looked at their Blackjack hand with a game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "*C1RC3 stares at you for a few seconds.* `\"You cannot look at your hand in a game you are not a part of.\"`")
        elif not game.is_midround():
            log(get_time() + " >> " + str(context.author) + " looked at their Blackjack hand outside of a round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + ", you currently do not have a hand; please bet and begin the round before I can deal you cards.\"`")
        else:
            log(get_time() + " >> " + str(context.author) + " looked at their Blackjack hand in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            message = "`\"Here are your opponents' current hands:\"`\n"
            for other_player in game.players:
                if other_player != player:
                    other_hand = other_player.get_hand()
                    if len(other_hand) >= 2:
                        other_hand[1] = 52
                    message += "**" + other_player.name + "**: " + format_cards(standard_deck, other_hand) + "\n"
            message += "\n`\"Here is your current hand:\"`\n# " + format_cards(standard_deck, player.get_hand()) + "\n## Total Value: " + str(player.hand_value())
            await context.respond(message, ephemeral = True, delete_after = 30)

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
        await ghost_reply(context, "`\"There is no game running at this table at the moment.\"`")
    elif game.type != "blackjack":
        log(get_time() + " >> " + str(context.author) + " hit in Blackjack while it wasn't Blackjack in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is a different type of game running at this table at the moment; you may be at the wrong table.\"`")
    else:
        player: BlackjackPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " hit in a Blackjack game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "*C1RC3 stares at you for a few seconds.* `\"You cannot be dealt cards in a game you are not a part of.\"`")
        elif not game.is_midround():
            log(get_time() + " >> " + str(context.author) + " hit in Blackjack outside of a round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + ", you currently do not have a hand; please bet and begin the round before I can deal you cards.\"`")
        elif game.get_turn() != context.author.id:
            log(get_time() + " >> " + str(context.author) + " hit in Blackjack outside of their turn in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + ", it is currently not your turn. You may not hit yet.\"`")
        else:
            # No need to test for hit state; if standing or busted it cannot be their turn already
            log(get_time() + " >> " + str(context.author) + " hit in Blackjack in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            drawn = game.draw(session, 1)
            await ghost_reply(context, "*C1RC3 pulls a card from the top of the deck and sets it down for all to see.*\n# " + format_cards(standard_deck, [drawn]) \
                 + "\n`\"That is your card, " + player.name + ".\"`")
            if player.add_card(session, drawn):
                # Test for 5 card charlie
                if len(player.get_hand()) == 5:
                    await bj_end_round(context, session, game)
                else:
                    game.next_turn(session)
                    await context.channel.send("`\"It is now your turn, " + game.get_turn_name() + ".\"`")
            else:
                # Busted, so test for round end
                await context.channel.send("*C1RC3 nods as she calculates the hand.* `\"Unfortunately, you have busted, " + player.name + ".\"`")
                if game.is_all_done():
                    await bj_end_round(context, session, game)
                else:
                    # Round didn't end with bust
                    game.next_turn(session)
                    await context.channel.send("`\"It is now your turn, " + game.get_turn_name() + ".\"`")

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
        await ghost_reply(context, "`\"There is no game running at this table at the moment.\"`")
    elif game.type != "blackjack":
        log(get_time() + " >> " + str(context.author) + " stood in Blackjack while it wasn't Blackjack in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is a different type of game running at this table at the moment; you may be at the wrong table.\"`")
    else:
        player: BlackjackPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " stood in a Blackjack game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "*C1RC3 stares at you for a few seconds.* `\"You cannot 'stand' in a game you are not a part of.\"`")
        elif not game.is_midround():
            log(get_time() + " >> " + str(context.author) + " stood in Blackjack outside of a round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + ", you currently do not have a hand; please bet and begin the round before I can deal you cards.\"`")
        elif game.get_turn() != context.author.id:
            log(get_time() + " >> " + str(context.author) + " stood in Blackjack outside of their turn in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + ", it is currently not your turn. You may not stand yet.\"`")
        else:
            log(get_time() + " >> " + str(context.author) + " stood in Blackjack in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "*C1RC3 nods at you.* `\"Understood. " + player.name + " has stood,\"` *she reiterates.*")
            player.stand(session)

            # player stood, so test for round end
            if game.is_all_done():
                await bj_end_round(context, session, game)
            else:
                # Round didn't end with stand
                game.next_turn(session)
                await context.channel.send("`\"It is now your turn, " + game.get_turn_name() + ".\"`")

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
    """Adds the command /bj convert"""

    session = database_connector()

    await convert(context, session, type, amount, "blackjack")

    session.close()

async def bj_end_round(context: ApplicationContext, session: Session, game: Blackjack) -> None:
    """Does round end stuff"""

    log(get_time() + " >> " + str(context.author) + " Blackjack round ended in [" + str(context.guild) + "], [" + str(context.channel) + "]")
    message = "`\"The round has ended. I will now reveal everyone's cards.\"`\n"
    for player in game.players:
        message += "## __" + player.name + "__\n# " + format_cards(standard_deck, player.get_hand()) + "\n"
    
    # End the round
    orig_bet = game.get_bet()
    win_con, winners = game.end_round(session)
    if len(winners) == 1:
        message += "`\"The Casino sincerely congratulates " + winners[0][1] + " for winning this round"
        if win_con == "f":
            message += " with a 5-card Charlie"
        elif win_con == "b":
            message += " with a Blackjack"
        message += "!\"`\n*C1RC3 opens a compartment in her abdomen where a pile of fresh chips lays, and pushes it over to " + winners[0][1] + ".*\n"\
            + "# " + format_chips(orig_bet)
    else:
        message += "`\""
        if len(winners) == 2:
            message += winners[0][1] + " and " + winners[1][1] + " have tied"
        elif len(winners) == 3:
            message += winners[0][1] + ", " + winners[1][1] + ", and " + winners[2][1] + " have tied"
        elif len(winners) == 4:
            message += winners[0][1] + ", " + winners[1][1] + ", " + winners[2][1] + ", and " + winners[3][1] + " have tied"
        if win_con == "b":
            message += " with a Blackjack"
        message += "! The new bet has been multiplied to:\"`\n"\
             + "# " + format_chips(game.get_bet()) + "\n"\
             "`\"Each winner will now be given a new hand.\"`\n"
        
        # Start new round because tied
        shuffled = game.start_round(session, [winner[0] for winner in winners])
        if shuffled:
            message += "*Before C1RC3 begins to draw cards, she places all of the cards into a compartment that slides open in her arm, and shuts it."\
                " A moment of whirring later, she opens it again and pulls out a newly shuffled deck.*\n"
        message += "*She begins to draw cards from the deck, deftly placing them down in front of each winner of the previous round.*\n"
        for player in game.players:
            message += "## __" + player.name + "__\n"
            hand = player.get_hand()
            if len(hand) >= 2:
                hand[1] = 52
            message += "# " + format_cards(standard_deck, hand) + "\n"
        message += "`\"The first turn goes to " + game.get_turn_name() + " this round.\"`"

    await context.channel.send(message)