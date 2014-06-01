


class RendezVousError(Exception):
    """An error specific to RendezVous."""
    pass


class MissingDeckError(RendezVousError):
    """One or more deck files are missing."""
    pass


class InvalidSpecialEffectError(RendezVousError):
    """Effect has an invalid EffectType."""
    pass


class DeckSyntaxWarning(SyntaxWarning):
    """There is a non-fatal error in the deck definition file."""
    pass


class GameSettings:
    NUM_PLAYERS = 2     #: the number of players in the game (including AI)
    CARDS_ON_BOARD = 4  #: the number of cards each players plays per turn
    CARDS_IN_HAND = 10  #: the number of cards held in a player's Hand
    NUM_ROUNDS = 20     #: the number of rounds in a single game



## Enumerations:  Enum base class added in Python 3.4  ;)

class Operator:
    """Requirement count operator."""
    AT_LEAST = -1
    EXACTLY = 0
    NO_MORE_THAN = 1


class Alignment:
    """Application identifiers for "same as my player" or.. not."""
    ALL = None
    FRIENDLY = 1
    ENEMY = 0
    # Note: these values are counted upon by RendezVousGame._apply()
    #       and Application._reverse_alignment


class SpecialSuit:
    """Special values for a Card's suit."""
    SPECIAL = "**SPECIAL**"  #: indicates a SpecialCard


class SpecialValue:
    """Special non-numerical card values."""
    WIN = 100         #: automatically win the match
    LOSE = -100       #: automatically lose the match
    KISS = 555        #: both sides treated as "winning"
    SPECIAL = 999     #: SpecialCard (ignore value)
    # Note: WIN and LOSE as opposites is counted upon by Card.apply()

    def all():
        for i in (SpecialValue.WIN, SpecialValue.LOSE, SpecialValue.KISS):
            yield i


class EffectType:
    """Types of things SpecialCards can do."""
    BUFF = 0     #: adjust the perceived value of the card
                 #      VALUE: +/- card value, or SpecialValue.WIN/LOSE
    WAIT = 1     #: force the card to wait through the next round
                 #      VALUE: N/A
    SWITCH = 2   #: card value is switched with its opponent
                 #      VALUE: new value (substituted dynamically)
    REVERSE = 3  #: card value is reversed (1 becomes 10)
                 #      VALUE: N/A
    REPLACE = 4  #: card suit is replaced with the one given
                 #      VALUE: new suit
    KISS = 5     #: the card's match is kissed (both treated as a win)
                 #      VALUE: N/A
    CLONE = 6    #: the card is replaced by the specified suit, value
                 #      VALUE: new Card (substituted dynamically)
    FLUSH = 7    #: the player's hand is flushed and refilled
                 #      VALUE: N/A
    
