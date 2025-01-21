"""This module relates to the game 'Blackjack'."""

print("Loading module 'blackjack'...")

from discord import ApplicationContext
from sqlalchemy.orm import Session

from ..base.bot import bot_client, database_connector
from ..base.auxiliary import log, get_time, ghost_reply, loc, loc_arr
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
        log(loc("bj.hand.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("bj.none"), True)
    else:
        player: BlackjackPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("bj.hand.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("bj.hand.spec"), True)
        elif not game.is_midround():
            log(loc("bj.hand.out.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("bj.hand.out"), True)
        else:
            log(loc("bj.hand.log", get_time(), context.guild, context.channel, context.author, player.get_hand()))
            other_hands = "".join([
                loc("bj.hand.per",
                    other_player.name,
                    "None"
                        if len(other_player.get_hand()) == 0
                        else format_cards(standard_deck, other_player.get_hand(True)),
                    "N/A"
                        if len(other_player.get_hand()) == 0
                        else "Bust" if other_player.busted()
                        else "".join([
                            str(other_player.hand_value(True)),
                            "+"
                        ])
                    )
                for other_player in game.players
                if other_player != player
                ])
            hand = player.get_hand()
            hand_val = "N/A" if len(hand) == 0 else player.hand_value(raw = True)
            hand = "None" if len(hand) == 0 else format_cards(standard_deck, hand)
            await ghost_reply(context, loc("bj.hand", other_hands, hand, hand_val), True)

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
        log(loc("bj.hit.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("bj.none"), True)
    else:
        player: BlackjackPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("bj.hit.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("bj.hit.spec"), True)
        elif not game.is_midround():
            log(loc("bj.hit.out.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("bj.hit.out"), True)
        elif game.get_turn().user_id != context.author.id:
            log(loc("bj.hit.turn.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("bj.hit.turn"), True)
        else:
            # No need to test for hit state; if standing or busted it cannot be their turn already
            drawn = game.draw(session)
            log(loc("bj.hit.log", get_time(), context.guild, context.channel, context.author, drawn))
            await ghost_reply(context, loc("bj.hit", player.name, format_cards(standard_deck, drawn)))

            busted = not player.add_card(session, drawn[0])
            if busted and game.is_all_done():
                # End round if all but one busted
                await bj_end_round(context, session, game)
            else:
                game.next_turn(session)

                await context.channel.send(loc("bj.next",
                    loc("bj.hit.bust", player.name, format_cards(standard_deck, player.get_hand()))
                        if busted
                            # Using boolean short circuit to log because I'm deranged
                            and (log(loc("bj.hit.bust.log", context.author)) is None) 
                        else "",
                    game.get_turn().name
                ))

                await context.channel.send(game.get_turn().mention(), delete_after = 0)

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
        log(loc("bj.stand.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("bj.none"), True)
    else:
        player: BlackjackPlayer = game.is_playing(session, context.author.id)
        if player is None:
            log(loc("bj.stand.spec.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("bj.stand.spec"), True)
        elif not game.is_midround():
            log(loc("bj.stand.out.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("bj.stand.out"), True)
        elif game.get_turn().user_id != context.author.id:
            log(loc("bj.stand.turn.log", get_time(), context.guild, context.channel, context.author))
            await ghost_reply(context, loc("bj.stand.turn"), True)
        else:
            log(loc("bj.stand.log", get_time(), context.guild, context.channel, context.author))
            player.stand(session)
            await ghost_reply(context, loc("bj.stand", player.name))

            # player stood, so test for round end
            if game.is_all_done():
                await bj_end_round(context, session, game)
            else:
                # Round didn't end with stand
                game.next_turn(session)
                await context.channel.send(loc("bj.next", "", game.get_turn().name))
                await context.channel.send(game.get_turn().mention(), delete_after = 0)

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
    
    hands = "".join([loc("bj.end.hand",
            player.name,
            "None"
                if len(player.get_hand()) == 0
                else format_cards(standard_deck, player.get_hand()),
            player.hand_value(raw = True),
            loc_arr("bj.end.con", player.hand_value())
            )
        for player in game.players
    ])
    
    # End the round
    win_con, winners = game.end_round(session)
    log(loc("bj.end.log", get_time(), context.guild, context.channel, [str(winner.user()) for winner in winners]))
    if len(winners) == 1:
        # Round ended with single winner
        await context.channel.send("".join([loc("bj.end", hands), loc("bj.end.win",
            winners[0].name,
            loc_arr("bj.end.con.win", win_con),
            winners[0].name,
            format_chips(winners[0].get_chips()),
            game.get_bet_turn().name
            )]))
    else:
        # Round ended with a tie
        await context.channel.send("".join([
            loc("bj.end", hands),
            loc("bj.end.tie",
                ", ".join([winner.name for winner in winners]),
                loc_arr("bj.end.con.win", win_con),
                format_chips(game.get_bet()),
                # Should only log reshuffle if reshuffle occurred
                loc("bj.reshuffle", log(loc("bj.reshuffle.log")))
                    if game.start_round(session, winners)
                    else "",
                "".join([loc("bj.start.hand",
                        player.name,
                        format_cards(standard_deck, player.get_hand(True))
                            if len(player.get_hand()) > 0
                            else "None"
                        )
                    for player in game.players
                    ]),
                game.get_turn().name
                )
            ]))

    # Ping everyone for end of round
    await context.channel.send(" ".join([player.mention() for player in game.players]), delete_after = 0)

    # No need to close session; this function is not to be called on its own

async def bj_start_round(context: ApplicationContext):
    """Test for round start"""

    session = database_connector()

    game: Blackjack = Blackjack.find_game(session, context.channel_id)

    # Game must exist, and bets must be placed outside of round
    if game is not None and not game.is_midround() and game.bets_aligned():
        log(loc("bj.start.log", get_time(), context.guild, context.channel))
        bet_placed = game.players[0].get_bet()
        game.set_bet(session, bet_placed)

        await context.channel.send(loc("bj.start",
            # Should only log reshuffle if reshuffle occurred
            loc("bj.reshuffle", log(loc("bj.reshuffle.log")))
                if game.start_round(session)
                else "",
            "".join([loc("bj.start.hand", player.name, format_cards(standard_deck, player.get_hand(True)))
                for player in game.players]),
            game.get_turn().name
            ))
        
        await context.channel.send(game.get_turn().mention(), delete_after = 0)

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
        log(loc("admin.bj.deck.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("bj.none"), True)
    else:
        log(loc("admin.bj.deck.log", get_time(), context.guild, context.channel, context.author))
        deck = game.get_deck()
        # Reverse deck order because drawing is from end
        deck = deck[::-1]
        await ghost_reply(context, loc("admin.bj.deck", deck))

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
        log(loc("admin.bj.shuffle.none.log", get_time(), context.guild, context.channel, context.author))
        await ghost_reply(context, loc("bj.none"), True)
    else:
        log(loc("admin.bj.shuffle.log", get_time(), context.guild, context.channel, context.author))
        game.shuffle(session)
        await ghost_reply(context, loc("admin.bj.shuffle"))

    session.close()