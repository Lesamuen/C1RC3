"""This module relates to the game 'Tourney'."""

print("Loading module 'tourney'...")

from discord import ApplicationContext, Option, OptionChoice
from sqlalchemy.orm import Session

from bot import bot_client, database_connector
from auxiliary import guilds, log, get_time, ghost_reply
from dbmodels import Tourney, TourneyPlayer
from emojis import standard_deck, format_cards, format_chips
from game import create, join, concede, identify, rename, chips, bet, use, convert
from admin import admin_cmds

ty_cmds = bot_client.create_group("ty", "Commands to run the game of Tourney", guild_ids = guilds, guild_only = True)

@ty_cmds.command(name = "create", description = "Start a Tourney game in this channel")
async def ty_create(
    context: ApplicationContext,
    stake: Option(int, description = "What stake to set the game to", required = True, choices = [
        OptionChoice("Low Stakes", 0),
        OptionChoice("Normal Stakes", 1),
        OptionChoice("High Stakes", 2),
    ])
):
    """Add the command /ty create"""

    session = database_connector()

    await create(context, session, stake, Tourney)

    session.close()

@ty_cmds.command(name = "join", description = "Join a Tourney game in this channel")
async def ty_join(
    context: ApplicationContext,
    name: Option(str, description = "The name that C1RC3 will refer to you as", required = True, min_length = 1, max_length = 20)
):
    """Add the command /ty join"""

    session = database_connector()

    await join(context, session, name, Tourney)

    session.close()

@ty_cmds.command(name = "concede", description = "Tell C1RC3 you lost (use when fully TFed or at the end of a mental round)")
async def ty_concede(
    context: ApplicationContext
):
    """Add the command /ty concede"""

    session = database_connector()

    await concede(context, session, Tourney)

    session.close()

@ty_cmds.command(name = "identify", description = "Be reminded of the other players' identities and chips")
async def ty_identify(
    context: ApplicationContext
):
    """Add the command /ty identify"""

    session = database_connector()

    await identify(context, session, Tourney)

    session.close()

@ty_cmds.command(name = "rename", description = "Ask C1RC3 to call you something else, in case your name has been changed")
async def ty_rename(
    context: ApplicationContext,
    name: Option(str, description = "Name that C1RC3 will refer to you as", required = True, min_length = 1, max_length = 20),
    private: Option(bool, description = "Whether to keep the response only visible to you", required = True)
):
    """Add the command /ty rename"""

    session = database_connector()

    await rename(context, session, name, private, Tourney)

    session.close()

@ty_cmds.command(name = "chips", description = "Recount how many chips you have in your current pile")
async def ty_chips(
    context: ApplicationContext,
    private: Option(bool, description = "Whether to keep the response only visible to you", required = True)
):
    """Add the command /ty chips"""

    session = database_connector()

    await chips(context, session, private, Tourney)

    session.close()

@ty_cmds.command(name = "bet", description = "Bet an amount of chips")
async def ty_bet(
    context: ApplicationContext,
    physical: Option(int, description = "The amount of physical chips to bet", min_value = 0, max_value = 100, default = 0),
    mental: Option(int, description = "The amount of mental chips to bet", min_value = 0, max_value = 20, default = 0),
    artificial: Option(int, description = "The amount of artificial chips to bet", min_value = 0, max_value = 2, default = 0),
    supernatural: Option(int, description = "The amount of supernatural chips to bet", min_value = 0, max_value = 20, default = 0),
    merge: Option(int, description = "The amount of merge chips to bet", min_value = 0, max_value = 3, default = 0),
    swap: Option(int, description = "The amount of swap chips to bet", min_value = 0, max_value = 25, default = 0)
):
    """Add the command /ty bet"""

    # Extract chip args
    chips: list[int] = list(locals().values())[1:7]

    session = database_connector()

    game: Tourney
    bet_placed, game = await bet(context, session, chips, Tourney)

    if bet_placed and game.bets_aligned():
        log(get_time() + " >> The Tourney round has started in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        game.set_bet(session, chips)

        game.start_round(session)
        
        await context.channel.send("`\"The players have agreed on a bet. The round shall now begin.\"`\n"\
            "*C1RC3 places all of the cards into a compartment that slides open in her arm, and shuts it."\
            " A moment of whirring later, she opens it again and pulls out a newly shuffled deck."\
            " She begins to draw cards from the deck, sliding " + str(len(game.players) + 2) + " of them face-down to each player.*\n"\
            "`\"Match 1 out of " + str(len(game.players) + 1) + " has commenced. Each of you, please send forth the card you wish to compete.\"`")
        
        # Ping everyone for beginning of match
        mention = ""
        for player in game.players:
            mention += player.mention() + " "
        await context.channel.send(mention, delete_after = 0)

    session.close()

@ty_cmds.command(name = "use", description = "Use an amount of chips from your current pile")
async def ty_use(
    context: ApplicationContext,
    physical: Option(int, description = "The amount of physical chips to use", min_value = 0, default = 0),
    mental: Option(int, description = "The amount of mental chips to use", min_value = 0, default = 0),
    artificial: Option(int, description = "The amount of artificial chips to use", min_value = 0, default = 0),
    supernatural: Option(int, description = "The amount of supernatural chips to use", min_value = 0, default = 0),
    merge: Option(int, description = "The amount of merge chips to use", min_value = 0, default = 0),
    swap: Option(int, description = "The amount of swap chips to use", min_value = 0, default = 0)
):
    """Add the command /ty use"""

    # Extract chip args
    chips: list[int] = list(locals().values())[1:7]

    session = database_connector()

    await use(context, session, chips, Tourney)

    session.close()

@ty_cmds.command(name = "convert", description = "Convert one type of chips to another")
async def ty_convert(
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
    """Add the command /ty convert"""

    session = database_connector()

    await convert(context, session, type, amount, Tourney)

    session.close()

@ty_cmds.command(name = "hand", description = "View the cards at your disposal to pick one to contest")
async def ty_hand(
    context: ApplicationContext
):
    """Add the command /ty hand"""

    session = database_connector()
    
    game = Tourney.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " looked at their Tourney hand with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no Tourney game running at this table at the moment.\"`", True)
    else:
        player: TourneyPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " looked at their Tourney hand with a game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot look at your hand in a game you are not a part of.\"`", True)
        elif not game.is_midround():
            log(get_time() + " >> " + str(context.author) + " looked at their Tourney hand outside of a round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You currently do not have a hand to look at; the round hasn't started yet.\"`", True)
        else:
            log(get_time() + " >> " + str(context.author) + " looked at their Tourney hand (" + str(player.get_hand()) + ") in [" + str(context.guild) + "], [" + str(context.channel) + "]")

            # Show own hand
            hand = player.get_hand()
            message = "\n`\"Here is your current hand:\"`\n"
            for i in range(len(hand)):
                message += "## " + str(i + 1) + ": " + standard_deck[hand[i][0]] + (" (Played)" if hand[i][1] else " (Unplayed)") + "\n"

            await ghost_reply(context, message, True)

    session.close()

@ty_cmds.command(name = "recon", description = "Inspect your opponents")
async def ty_recon(
    context: ApplicationContext,
):
    """Add the command /ty recon"""

    session = database_connector()
    
    game = Tourney.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " looked at their Tourney opponents with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no Tourney game running at this table at the moment.\"`", True)
    else:
        player: TourneyPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " looked at their Tourney opponents in a game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot inspect your opponents in a game you are not a part of.\"`", True)
        else:
            log(get_time() + " >> " + str(context.author) + " did some Tourney recon in [" + str(context.guild) + "], [" + str(context.channel) + "]")

            # Get opponents' revealed cards/points
            message = "`\"What cards your opponents have sent forward already:\"`\n"
            other_player: TourneyPlayer
            for other_player in game.players:
                if other_player != player:
                    message += "(" + str(other_player.points) + ") **" + other_player.name + "**:\n"
                    message += format_cards(standard_deck, [card[0] for card in other_player.get_hand() if card[1]])
                    message += "\n"
            message += "\n`\"You currently have " + str(player.points) + " points.\"`"

            await ghost_reply(context, message, True)

    session.close()

@ty_cmds.command(name = "play", description = "Choose one of your cards to send into the Tourney")
async def ty_play(
    context: ApplicationContext,
    card: Option(int, description = "Which card to play", min_value = 1, max_value = 8)
):
    """Add the command /ty play"""

    session = database_connector()

    game: Tourney = Tourney.find_game(session, context.channel_id)
    if game is None:
        log(get_time() + " >> " + str(context.author) + " played a Tourney card with no game in [" + str(context.guild) + "], [" + str(context.channel) + "]")
        await ghost_reply(context, "`\"There is no Tourney game running at this table at the moment.\"`", True)
    else:
        player: TourneyPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(get_time() + " >> " + str(context.author) + " played a Tourney card in a game they're not part of in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You cannot play a card in a game you are not a part of.\"`", True)
        elif not game.is_midround():
            log(get_time() + " >> " + str(context.author) + " played a Tourney card outside of a round in [" + str(context.guild) + "], [" + str(context.channel) + "]")
            await ghost_reply(context, "`\"You currently have no cards to play; the round hasn't started yet.\"`", True)
        else:
            # Try to play the card chosen
            try:
                success = player.play_card(session, card - 1)
            except:
                await ghost_reply(context, "`\"You do not have that many cards in your hand.\"`", True)
            else:
                if not success:
                    await ghost_reply(context, "`\"You've already played that card before.\"`", True)
                else:
                    await ghost_reply(context, "*C1RC3 looks at the card " + player.name + " slid forward to the center of the table, and confirms,* `\"" + player.name + " has chosen a card.\"`")

                    # Test to see if the turn is over
                    if game.all_played():
                        message = "`\"All players have brought forth a card. The Tourney shall now proceed...\"`"\
                            " *The " + str(len(game.players)) + " cards on the table all flip over magically, revealing themselves:*\n"
                        for player in game.players:
                            message += "# " + standard_deck[player.get_hand()[player.played][0]] + " (" + player.name + ")\n"
                        winner: TourneyPlayer = game.evaluate_turn(session)
                        message += "\n*Everyone's cards flash red, except for " + winner.name + "'s.*\n"\
                            "`\"" + winner.name + " takes this match! You have been awarded a point, bringing you to a total of " + str(winner.points) + " points.\"`\n"\
                            "*C1RC3 waves her hand, and the center of the table clears itself.*"
                        
                        # Test to see if the round is over
                        if game.turn <= len(game.players) + 1:
                            # Round not over, next turn
                            message2 = "`\"Match " + str(game.turn) + " has commenced. Once again, send forth the card you wish to compete.\"`"
                        else:
                            # Round over
                            message2 = "`\"That was the last match of the round--it is time to decide a victor.\"`\n"
                            for player in game.players:
                                message2 += "## " + player.name + ": " + str(player.points) + "\n"
                            winners = game.end_round(session)
                            winners_unsorted = [player for player in game.players if player in winners]
                            if len(winners) > 1:
                                message2 += "`\"There are multiple candidates for a victor this round; " + winners_unsorted[0].name
                                for i in range(len(winners) - 2):
                                    message2 += ", " + winners_unsorted[i + 1].name
                                message2 += " and " + winners_unsorted[-1].name + ", please send forth your final contender.\"`\n"\
                                    "*Automatically, their cards magically float up into the air and set themselves down in the center of the table.*\n"
                                for player in winners_unsorted:
                                    message2 += "# " + standard_deck[player.tiebreaker()] + " (" + player.name + ")\n"
                                message2 += "*The card that rises up is " + winners[0].name + "'s, while the others fly back over to C1RC3's deck.*\n"

                            message2 += "`\"Congratulations, " + winners[0].name + "; you have bested all of your opponents in the Tourney!"
                            if winners[0].points > 2:
                                message2 += " Because you ended with " + str(winners[0].points) + " points, your chips rewarded shall be multiplied by " + str(winners[0].points - 1) + "!"
                            message2 += "\"`\n*C1RC3 opens a compartment in her abdomen where a pile of fresh chips lays, and pushes it over to " + winners[0].name + ", making a sizeable pile of:*\n# "\
                                + format_chips(winners[0].get_chips())
                            message2 += "\n\n`\"" + game.get_bet_turn().name + " shall decide the next initial bet.\"`"
                        
                        await context.channel.send(message)
                        await context.channel.send(message2)

                        # Ping everyone for end of match/round
                        mention = ""
                        for player in game.players:
                            mention += player.mention() + " "
                        await context.channel.send(mention, delete_after = 0)

    session.close()

