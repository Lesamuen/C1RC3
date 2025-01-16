"""Contains all Discord-emoji related stuff like decks and chips"""

print("Loading module 'emoji'...")

from .auxiliary import loc_en, loc

# Aliases for backwards compat
chip_emojis: list[str] = loc_en["chips"]
standard_deck: list[str] = loc_en["deck.standard"]

def format_chips(chips: list[int]) -> str:
    """Format chips into a human readable format for Discord."""

    # If no chips, say "0 basic chips".
    no_chips = True
    for chip_type in chips:
        if chip_type > 0:
            no_chips = False
            break
    if no_chips:
        return "".join(["0 ", chip_emojis[0]])
    else:
        # Chips exist, so go through every non-zero chip and list them
        return ", ".join([
            " ".join([str(chip_type), chip_emojis[i]])
            for i, chip_type in enumerate(chips) if chip_type > 0
            ])

def format_cards(card_set: list[str], cards: list[int]) -> str:
    """Format card emojis into a human readable format for Discord"""

    return "".join([card_set[card] for card in cards])