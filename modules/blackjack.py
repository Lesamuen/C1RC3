"""This module relates to the game 'Blackjack'."""

print("Loading module 'blackjack'...")

from typing import List

from discord import ApplicationContext, Option, OptionChoice
from sqlalchemy.orm import Session

from bot import bot_client, database_connector
from auxiliary import guilds, log, get_time, ghost_reply
from dbmodels import Blackjack, BlackjackPlayer
from emojis import standard_deck, format_cards, format_chips
from game import create, join, concede, identify, rename, chips, bet, use, convert

bj_cmds = bot_client.create_group("bj", "Commands to run the game of Blackjack", guild_ids = guilds, guild_only = True)

@bj_cmds.command(name = "create", description = "Start a Blackjack game in this channel")
async def bj_create(
    context: ApplicationContext,
    stake: Option(int, description = "What stake to set the game to", required = True, choices = [
        OptionChoice("Low Stakes", 0),
        OptionChoice("Normal Stakes", 1),
        OptionChoice("High Stakes", 2),
    ])
):
    """Add the command /bj create"""

    session = database_connector()

    await create(context, session, stake, Blackjack)

    session.close()

@bj_cmds.command(name = "join", description = "Join a Blackjack game in this channel")
async def bj_join(
    context: ApplicationContext,
    name: Option(str, description = "The name that C1RC3 will refer to you as", required = True, min_length = 1)
):
    """Add the command /bj join"""

    session = database_connector()

    await join(context, session, name, Blackjack)

    session.close()

@bj_cmds.command(name = "concede", description = "Tell C1RC3 you lost (use when fully TFed or at the end of a mental round)")
async def bj_concede(
    context: ApplicationContext
):
    """Add the command /bj concede"""

    session = database_connector()

    await concede(context, session, Blackjack)

    session.close()

@bj_cmds.command(name = "identify", description = "Be reminded of the other players' identities and chips")
async def bj_identify(
    context: ApplicationContext
):
    """Add the command /bj identify"""

    session = database_connector()

    await identify(context, session, Blackjack)

    session.close()

@bj_cmds.command(name = "rename", description = "Ask C1RC3 to call you something else, in case your name has been changed")
async def bj_rename(
    context: ApplicationContext,
    name: Option(str, description = "Name that C1RC3 will refer to you as", required = True, min_length = 1),
    private: Option(bool, description = "Whether to keep the response only visible to you", default = False)
):
    """Add the command /bj rename"""

    session = database_connector()

    await rename(context, session, name, private, Blackjack)

    session.close()

@bj_cmds.command(name = "chips", description = "Recount how many chips you have in your current pile")
async def bj_chips(
    context: ApplicationContext,
    private: Option(bool, description = "Whether to keep the response only visible to you", default = False)
):
    """Add the command /bj chips"""

    session = database_connector()

    await chips(context, session, private, Blackjack)

    session.close()

@bj_cmds.command(name = "bet", description = "Bet an amount of chips")
async def bj_bet(
    context: ApplicationContext,
    physical: Option(int, description = "The amount of physical chips to bet", min_value = 0, max_value = 100, default = 0),
    mental: Option(int, description = "The amount of mental chips to bet", min_value = 0, max_value = 20, default = 0),
    artificial: Option(int, description = "The amount of artificial chips to bet", min_value = 0, max_value = 2, default = 0),
    supernatural: Option(int, description = "The amount of supernatural chips to bet", min_value = 0, max_value = 20, default = 0),
    merge: Option(int, description = "The amount of merge chips to bet", min_value = 0, max_value = 3, default = 0),
    swap: Option(int, description = "The amount of swap chips to bet", min_value = 0, max_value = 25, default = 0)
):
    """Add the command /bj bet"""

    # Extract chip args
    chips: List[int] = list(locals().values())[1:7]

    session = database_connector()

    game: Blackjack
    bet_placed, game = await bet(context, session, chips, Blackjack)

    if bet_placed:
        if game.bets_aligned():
            log(get_time() + " >> The Blackjack round has started in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            game.set_bet(session, chips)

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
            message += "`\"The first turn goes to " + game.get_turn().name + " this round.\"`"
            
            await context.channel.send(message)

    session.close()

@bj_cmds.command(name = "use", description = "Use an amount of chips from your current pile")
async def bj_use(
    context: ApplicationContext,
    physical: Option(int, description = "The amount of physical chips to use", min_value = 0, default = 0),
    mental: Option(int, description = "The amount of mental chips to use", min_value = 0, default = 0),
    artificial: Option(int, description = "The amount of artificial chips to use", min_value = 0, default = 0),
    supernatural: Option(int, description = "The amount of supernatural chips to use", min_value = 0, default = 0),
    merge: Option(int, description = "The amount of merge chips to use", min_value = 0, default = 0),
    swap: Option(int, description = "The amount of swap chips to use", min_value = 0, default = 0)
):
    """Add the command /bj use"""

    # Extract chip args
    chips: List[int] = list(locals().values())[1:7]

    session = database_connector()

    await use(context, session, chips, Blackjack)

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
    """Add the command /bj convert"""

    session = database_connector()

    await convert(context, session, type, amount, Blackjack)

    session.close()

@bj_cmds.command(name = "hand", description = "Peek at the hand you've been given")
async def bj_hand(
    context: ApplicationContext
):
    """Add the command /bj hand"""

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
                message += "\n`\"Here is your current hand:\"`\n\n## Total Value: 0"
            else:
                message += "\n`\"Here is your current hand:\"`\n# " + format_cards(standard_deck, hand) + "\n## Total Value: " + str(player.hand_value())
            await ghost_reply(context, message, True)

    session.close()

@bj_cmds.command(name = "hit", description = "Ask C1RC3 for a card...will you bust?")
async def bj_hit(
    context: ApplicationContext
):
    """Add the command /bj hit"""

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
            drawn = game.draw(session, 1)
            log(get_time() + " >> " + str(context.author) + " drew " + str(drawn) + " in Blackjack in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"" + player.name + " hits,\"` *C1RC3 affirms.*\n"\
                "*She pulls a card from the top of the deck and sets it down for all to see.*\n# " + format_cards(standard_deck, [drawn]))
            if player.add_card(session, drawn):
                # Test for 5 card charlie
                if len(player.get_hand()) == 5:
                    await bj_end_round(context, session, game)
                else:
                    game.next_turn(session)
                    await context.channel.send("`\"It is now your turn, " + game.get_turn().name + ".\"`")
            else:
                # Busted, so test for round end
                log("                     >> " + str(context.author) + " busted.")
                await context.channel.send("*C1RC3 shakes her head as she calculates the hand.* `\"Unfortunately, you have busted, " + player.name + ".\"`")
                if game.is_all_done():
                    await bj_end_round(context, session, game)
                else:
                    # Round didn't end with bust
                    game.next_turn(session)
                    await context.channel.send("`\"It is now your turn, " + game.get_turn().name + ".\"`")

    session.close()

@bj_cmds.command(name = "stand", description = "Keep your current hand until the end of the round")
async def bj_stand(
    context: ApplicationContext
):
    """Add the command /bj stand"""

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
            await ghost_reply(context, "`\"" + player.name + ", it is currently not your turn. You may not stand yet.\"`")
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
                await context.channel.send("`\"It is now your turn, " + game.get_turn().name + ".\"`")

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
        message += ".\"`\n*C1RC3 opens a compartment in her abdomen where a pile of fresh chips lays, and pushes it over to " + winners[0][1] + ", making a sizeable pile of*\n"\
            + "# " + format_chips(game.players[winners[0][0]].get_chips())
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
                message += "\n"
            else:
                message += "# " + format_cards(standard_deck, hand) + "\n"
        message += "`\"The first turn goes to " + game.get_turn().name + " this round.\"`"
    log("                     >> " + str([str(bot_client.get_user(game.players[winner[0]].user_id)) for winner in winners]) + " won.")

    await context.channel.send(message)
