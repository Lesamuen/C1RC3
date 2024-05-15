"""This module relates to the game 'Blackjack'."""

print("Loading module 'blackjack'...")

from discord import ApplicationContext
from sqlalchemy.orm import Session

from ..base.bot import bot_client, database_connector
from ..base.auxiliary import log, get_time, ghost_reply
from ..base.dbmodels import Blackjack, BlackjackPlayer
from ..base.emojis import standard_deck, format_cards, format_chips
from .game import base_game_cmds
from ..misc.admin import admin_cmds

# Inherit and register command group to Discord
bj_cmds = base_game_cmds.copy()
bj_cmds.name = "bj"
bj_cmds.description = "Commands to run the game of Blackjack"
for i, cmd in enumerate(bj_cmds.subcommands):
    cmd = cmd.copy()
    cmd.game_type = Blackjack
    bj_cmds.subcommands[i] = cmd
bot_client.add_application_command(bj_cmds)


@bj_cmds.command(name = "hand", description = "Peek at the hand you've been given")
async def bj_hand(
    context: ApplicationContext
):
    """Add the command /bj hand
    
    See player's hand & hand value & others' hands
    """

    session = database_connector()
    
    game = Blackjack.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " looked at their Blackjack hand with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no Blackjack game running at this table at the moment.\"`", True)
    else:
        player: BlackjackPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " looked at their Blackjack hand with a game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot look at your hand in a game you are not a part of.\"`", True)
        elif not game.is_midround():
            log(get_time() + " >> " + str(context.author) + " looked at their Blackjack hand outside of a round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You currently do not have a hand to look at; the round hasn't started yet.\"`", True)
        else:
            log(get_time() + " >> " + str(context.author) + " looked at their Blackjack hand (" + str(player.get_hand()) + ") in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            message = "`\"Here are your opponents' current hands:\"`\n"
            other_player: BlackjackPlayer
            for other_player in game.players:
                if other_player != player:
                    message += "**" + other_player.name + "**: "
                    if len(other_player.get_hand()) == 0:
                        message += "No Hand"
                    else:
                        message += format_cards(standard_deck, other_player.get_hand(True)) + " -- "
                        if other_player.busted():
                            message += "Bust"
                        else:
                            message += str(other_player.hand_value(True)) + "+"
                    message += "\n"
            hand = player.get_hand()
            if len(hand) == 0:
                message += "\n`\"Here is your current hand:\"`\n\n## Total Value: N/A"
            else:
                message += "\n`\"Here is your current hand:\"`\n# " + format_cards(standard_deck, hand) + "\n## Total Value: " + str(player.hand_value())
            await ghost_reply(context, message, True)

    session.close()

@bj_cmds.command(name = "hit", description = "Ask for another card, with a possibility of busting")
async def bj_hit(
    context: ApplicationContext
):
    """Add the command /bj hit
    
    Hit in Blackjack
    """

    session = database_connector()
    
    game: Blackjack = Blackjack.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " hit in Blackjack with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no Blackjack game running at this table at the moment.\"`", True)
    else:
        player: BlackjackPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " hit in a Blackjack game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot be dealt cards in a game you are not a part of.\"`", True)
        elif not game.is_midround():
            log(get_time() + " >> " + str(context.author) + " hit in Blackjack outside of a round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You currently do not have a hand to hit with; the round hasn't started yet.\"`", True)
        elif game.get_turn().user_id != context.author.id:
            log(get_time() + " >> " + str(context.author) + " hit in Blackjack outside of their turn in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You may not hit yet; it is not your turn.\"`", True)
        else:
            # No need to test for hit state; if standing or busted it cannot be their turn already
            drawn = game.draw(session)
            log(get_time() + " >> " + str(context.author) + " drew " + str(drawn) + " in Blackjack in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + " hits,\"` *C1RC3 affirms.*\n"\
                "*She pulls a card from the top of the deck and sets it down for all to see.*\n# " + format_cards(standard_deck, drawn))
            if player.add_card(session, drawn[0]):
                # Test for 5 card charlie
                if len(player.get_hand()) == 5:
                    await bj_end_round(context, session, game)
                else:
                    game.next_turn(session)
                    next = game.get_turn()
                    await context.channel.send("`\"It is now your turn, " + next.name + ".\"`")
                    await context.channel.send(next.mention(), delete_after = 0)
            else:
                # Busted, so test for round end
                log("                     >> " + str(context.author) + " busted.")
                await context.channel.send("*C1RC3 shakes her head as she calculates the hand.* `\"Unfortunately, you have busted, " + player.name + ".\"`")
                if game.is_all_done():
                    await bj_end_round(context, session, game)
                else:
                    # Round didn't end with bust
                    await context.channel.send("*The facedown card magically flips itself over, revealing the unfortunate hand:*\n## " + format_cards(standard_deck, player.get_hand()))
                    game.next_turn(session)
                    next = game.get_turn()
                    await context.channel.send("`\"It is now your turn, " + next.name + ".\"`")
                    await context.channel.send(next.mention(), delete_after = 0)

    session.close()

@bj_cmds.command(name = "stand", description = "Keep your current hand until the end of the round")
async def bj_stand(
    context: ApplicationContext
):
    """Add the command /bj stand
    
    Stand in Blackjack
    """

    session = database_connector()
    
    game: Blackjack = Blackjack.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " stood in Blackjack with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no Blackjack game running at this table at the moment.\"`", True)
    else:
        player: BlackjackPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " stood in a Blackjack game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot 'stand' in a game you are not a part of.\"`", True)
        elif not game.is_midround():
            log(get_time() + " >> " + str(context.author) + " stood in Blackjack outside of a round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You currently do not have a hand to stand with; the round hasn't started yet.\"`", True)
        elif game.get_turn().user_id != context.author.id:
            log(get_time() + " >> " + str(context.author) + " stood in Blackjack outside of their turn in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + ", it is currently not your turn. You may not stand yet.\"`", True)
        else:
            log(get_time() + " >> " + str(context.author) + " stood in Blackjack in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + " stands,\"` *C1RC3 affirms.*")
            player.stand(session)

            # player stood, so test for round end
            if game.is_all_done():
                await bj_end_round(context, session, game)
            else:
                # Round didn't end with stand
                game.next_turn(session)
                next = game.get_turn()
                await context.channel.send("`\"It is now your turn, " + next.name + ".\"`")
                await context.channel.send(next.mention(), delete_after = 0)

    session.close()

async def bj_end_round(context: ApplicationContext, session: Session, game: Blackjack) -> None:
    """Handle all functionality for ending a round of Blackjack
    
    ### Parameters
    context: discord.ApplicationContext
        Application command context
    session: sqlalchemy.orm.Session
        Current database scope
    game: Blackjack
        The blackjack game in which the round shall be ended
    """

    log(get_time() + " >> Blackjack round ended in [" + str(context.guild) + "], [" + str(context.channel) + "]")
    message = "`\"The round has ended. I will now reveal everyone's cards.\"`\n"
    player: BlackjackPlayer
    for player in game.players:
        message += "## __" + player.name + "__\n"
        hand = player.get_hand()
        if len(hand) != 0:
            val = player.hand_value(raw = True)
            message += "# " + format_cards(standard_deck, hand) + ": " + str(val)
            if val > 21:
                message += " (Bust)"
            elif len(hand) == 5:
                message += " (5-Card Charlie)"
            elif val == 21:
                message += " (Blackjack)"
        else:
            message += "# No Hand"
        message += "\n"
    
    # End the round
    win_con, winners = game.end_round(session)
    if len(winners) == 1:
        message += "`\"The Casino congratulates " + winners[0][1] + " for winning this round"
        if win_con == "f":
            message += " with a 5-card Charlie"
        elif win_con == "b":
            message += " with a Blackjack"
        message += ".\"`\n*C1RC3 opens a compartment in her abdomen where a pile of fresh chips lays, and pushes it over to " + winners[0][1] + ", making a sizeable pile of:*\n# "\
            + format_chips(game.players[winners[0][0]].get_chips())
        message += "\n`\"" + game.get_bet_turn().name + " shall decide the next initial bet.\"`"
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
        log("                     >> The Blackjack round has re-started in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        if game.start_round(session, [winner[0] for winner in winners]):
            # If true, then shuffled
            log("                     >> Deck was reshuffled.")
            message += "*Before C1RC3 begins to draw cards, she places all of the cards into a compartment that slides open in her arm, and shuts it."\
                " A moment of whirring later, she opens it again and pulls out a newly shuffled deck.*\n"
        message += "*She begins to draw cards from the deck, deftly placing them down in front of each winner of the previous round.*\n"
        for player in game.players:
            message += "## __" + player.name + "__\n"
            hand = player.get_hand(True)
            if len(hand) == 0:
                message += "# No Hand\n"
            else:
                message += "# " + format_cards(standard_deck, hand) + "\n"
        message += "`\"The first turn goes to " + game.get_turn().name + " this round.\"`"
    log("                     >> " + str([str(game.players[winner[0]].user()) for winner in winners]) + " won.")

    await context.channel.send(message)
    if len(winners) == 1:
        # Ping everyone for end of round
        mention = ""
        for player in game.players:
            mention += player.mention() + " "
        await context.channel.send(mention, delete_after = 0)
    else:
        await context.channel.send(game.get_turn().mention(), delete_after = 0)

async def bj_start_round(context: ApplicationContext):
    """Test for round start"""

    session = database_connector()

    game: Blackjack = Blackjack.find_game(session, context.channel_id)

    if game is not None and not game.is_midround() and game.bets_aligned():
        log(get_time() + " >> The Blackjack round has started in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        bet_placed = game.players[0].get_bet()
        game.set_bet(session, bet_placed)

        message = "`\"The players have agreed on a bet. The round shall now begin.\"`\n"
        if game.start_round(session):
            # If true, then shuffled
            log("                     >> Deck was reshuffled.")
            message += "*Before C1RC3 begins to draw cards, she places all of the cards into a compartment that slides open in her arm, and shuts it."\
                " A moment of whirring later, she opens it again and pulls out a newly shuffled deck.*\n"
        message += "*She begins to draw cards from the deck, deftly placing them down in front of each player.*\n"
        player: BlackjackPlayer
        for player in game.players:
            message += "## __" + player.name + "__\n"
            message += "# " + format_cards(standard_deck, player.get_hand(True)) + "\n"
        next = game.get_turn()
        message += "`\"The first turn goes to " + next.name + " this round.\"`"
        
        await context.channel.send(message)
        await context.channel.send(next.mention(), delete_after = 0)

    session.close()

# Register round start logic to invoke after betting
for cmd in bj_cmds.walk_commands():
    if cmd.name == "bet":
        cmd.after_invoke(bj_start_round)
        break

bj_admin_cmds = admin_cmds.create_subgroup("bj", "Admin commands directly related to blackjack")

@bj_admin_cmds.command(name = "show_deck", description = "Admin command to view a blackjack deck")
async def bj_admin_show_deck(
    context: ApplicationContext,
):
    """Add the command /admin bj show_deck
    
    Reveal deck
    """

    session = database_connector()

    game: Blackjack = Blackjack.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to show deck in Blackjack with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no Blackjack game running at this table at the moment.\"`", True)
    else:
        deck = game.get_deck()
        # Reverse deck order because drawing is from end
        deck = deck[::-1]
        await ghost_reply(context, "`\"Administrator-level Access detected. Scanning deck...\"`\n"\
            "```" + str(deck) + "```")

    session.close()

@bj_admin_cmds.command(name = "shuffle", description = "Admin command to shuffle a blackjack deck")
async def bj_admin_shuffle(
    context: ApplicationContext,
):
    """Add the command /admin bj shuffle
    
    Shuffle deck manually
    """

    session = database_connector()

    game: Blackjack = Blackjack.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> Admin " + str(context.author) + " tried to shuffle deck in Blackjack with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no Blackjack game running at this table at the moment.\"`", True)
    else:
        game.shuffle(session)
        await ghost_reply(context, "`\"Administrator-level Access detected. Manually shuffling deck...\"`\n"\
            "*C1RC3 places all of the cards into a compartment that slides open in her arm, and shuts it."\
                " A moment of whirring later, she opens it again and pulls out a newly shuffled deck.*")

    session.close()