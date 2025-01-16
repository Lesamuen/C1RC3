"""This module relates to the game 'Tourney'."""

print("Loading module 'tourney'...")

from discord import ApplicationContext, option

from ..base.bot import bot_client, database_connector
from ..base.auxiliary import log, loc, loc_arr, get_time, ghost_reply
from ..base.dbmodels import Tourney, TourneyPlayer
from ..base.emojis import standard_deck, format_cards, format_chips
from .game import base_game_cmds

# Inherit and register command group to Discord
ty_cmds = base_game_cmds.copy()
ty_cmds.name = "ty"
ty_cmds.description = "Commands to run the game of Tourney"
for i, cmd in enumerate(ty_cmds.subcommands):
    cmd = cmd.copy()
    cmd.game_type = Tourney
    ty_cmds.subcommands[i] = cmd
bot_client.add_application_command(ty_cmds)


@ty_cmds.command(name = "hand", description = "Review the cards in your hand")
async def ty_hand(
    context: ApplicationContext
):
    """Add the command /ty hand
    
    View player hand
    """

    session = database_connector()
    
    game = Tourney.find_game(session, context.channel_id)
    if game is None:
        log(loc("ty.hand.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("ty.none"), True)
    else:
        player: TourneyPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("ty.hand.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("ty.hand.spec"), True)
        elif not game.is_midround():
            log(loc("ty.hand.out.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("ty.hand.out"), True)
        else:
            log(loc("ty.hand.log", get_time(), context.guild, context.channel, context.author))

            # Show own hand
            await ghost_reply(context, loc("ty.hand", "".join([loc("ty.hand.card",
                    i + 1,
                    standard_deck[card[0]],
                    loc_arr("ty.hand.card.played", card[1])
                    )
                for i, card in enumerate(player.get_hand())
                ])), True)

    session.close()

@ty_cmds.command(name = "recon", description = "Inspect your opponents' points and cards")
async def ty_recon(
    context: ApplicationContext,
):
    """Add the command /ty recon
    
    View everyone's points and used cards
    """

    session = database_connector()
    
    game = Tourney.find_game(session, context.channel_id)
    if game is None:
        log(loc("ty.recon.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("ty.none"), True)
    else:
        player: TourneyPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("ty.recon.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("ty.recon.spec"), True)
        else:
            log(loc("ty.recon.log", get_time(), context.guild, context.channel, context.author))

            # Get opponents' revealed cards/points
            await ghost_reply(context, loc("ty.recon",
                    "".join([
                        loc("ty.recon.opp",
                            other_player.points,
                            other_player.name,
                            format_cards(standard_deck, [card[0] for card in other_player.get_hand() if card[1]])
                            )
                        for other_player in game.players
                        if other_player != player
                        ]),
                    player.points
                    ),
                True)

    session.close()

@ty_cmds.command(name = "play", description = "Choose one of your cards to send into the Tourney")
@option("card", int, description = "Which card to play", min_value = 1, max_value = 8)
async def ty_play(context: ApplicationContext, card: int):
    """Add the command /ty play
    
    Play a card
    """

    session = database_connector()

    game: Tourney = Tourney.find_game(session, context.channel_id)
    if game is None:
        log(loc("ty.play.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("ty.none"), True)
    else:
        player: TourneyPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("ty.play.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("ty.play.spec"), True)
        elif not game.is_midround():
            log(loc("ty.play.out.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("ty.play.out"), True)
        else:
            # Try to play the card chosen
            try:
                success = player.play_card(session, card - 1)
            except:
                log(loc("ty.play.fail.log", get_time(), context.guild, context.channel, context.author, card - 1))
                await ghost_reply(context, loc("ty.play.fail"), True)
            else:
                if not success:
                    log(loc("ty.play.dupe.log", get_time(), context.guild, context.channel, context.author, card - 1))
                    await ghost_reply(context, loc("ty.play.dupe"), True)
                else:
                    log(loc("ty.play.log", get_time(), context.guild, context.channel, context.author, card - 1))
                    await ghost_reply(context, loc("ty.play", player.name, player.name))

                    # Test to see if the turn is over
                    if game.all_played():
                        played = "".join([loc("ty.turn.played",
                                standard_deck[player.get_hand()[player.played][0]],
                                player.name
                                )
                            for player in game.players
                            ])
                        winner: TourneyPlayer = game.evaluate_turn(session)

                        log(loc("ty.turn.log", game.turn - 1, winner.user()))

                        message = [loc("ty.turn",
                            len(game.players),
                            played,
                            winner.name,
                            winner.name,
                            winner.points
                            )]
                        
                        # Test to see if the round is over
                        if game.turn <= len(game.players) + 1:
                            # Round not over, next turn
                            message.append(loc("ty.turn.next", game.turn))
                        else:
                            # Round over
                            winners = game.end_round(session)
                            winners_unsorted = [player for player in game.players if player in winners]

                            log(loc("ty.turn.end.log", winners[0].user()))

                            message.append(loc("ty.turn.end",
                                "".join([loc("ty.turn.points", player.name, player.points)
                                    for player in game.players
                                    ]),
                                loc("ty.turn.tie",
                                        ", ".join([winner.name for winner in winners_unsorted]),
                                        "".join([loc("ty.turn.played", standard_deck[winner.tiebreaker()], winner.name)
                                            for winner in winners_unsorted
                                            ]),
                                        winners[0].name
                                        )
                                    if len(winners) > 1
                                    else "",
                                winners[0].name,
                                loc("ty.turn.over", winners[0].points, winners[0].points - 1)
                                    if winners[0].points > 2
                                    else "",
                                winners[0].name,
                                format_chips(winners[0].get_chips()),
                                game.get_bet_turn().name
                                ))

                        await context.channel.send("".join(message))

                        # Ping everyone for end of match/round
                        await context.channel.send(" ".join([player.mention() for player in game.players]), delete_after = 0)

    session.close()

async def ty_start_round(context: ApplicationContext):
    """Test for round start"""

    session = database_connector()

    game: Tourney = Tourney.find_game(session, context.channel_id)

    # Game must exist, and bets must be placed outside of round
    if game is not None and not game.is_midround() and game.bets_aligned():
        log(loc("ty.start.log", get_time(), context.guild, context.channel))

        bet_placed = game.players[0].get_bet()
        game.set_bet(session, bet_placed)

        game.start_round(session)
        
        await context.channel.send(loc("ty.start", len(game.players) + 2), len(game.players) + 1)
        
        # Ping everyone for beginning of match
        await context.channel.send(" ".join([player.mention() for player in game.players]), delete_after = 0)

    session.close()

# Register round start logic to invoke after betting
for cmd in ty_cmds.walk_commands():
    if cmd.name == "bet":
        cmd.after_invoke(ty_start_round)
        break