import warnings
import re


from rendezvous import settings
GameSettings = settings.GameSettings()


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


class AchievementSyntaxWarning(SyntaxWarning):
    """There is a non-fatal error in the achievement definition file."""
    pass


## Enumerations:  Enum base class added in Python 3.4  ;)

class Operator:
    """Requirement count operator."""
    AT_LEAST = -1
    EXACTLY = 0
    NO_MORE_THAN = 1
    LESS_THAN = 2


class Alignment:
    """Application identifiers for "same as my player" or.. not."""
    ALL = None
    FRIENDLY = 1
    ENEMY = 0
    # Note: these values are counted upon by RendezVousGame._apply()
    #       and Application._reverse_alignment


class SpecialSuit:
    """Special values for a Card's suit, or for Achievements."""
    SPECIAL = "**SPECIAL**"  #: indicates a SpecialCard
    ANY = "Any"              #: any suit, or many of them
    EACH = "Each"            #: every suit
    ONE = "One"              #: exactly one suit
    TOTAL = "Total"          #: total score


class SpecialValue:
    """Special non-numerical card values."""
    WIN = 100         #: automatically win the match
    LOSE = -100       #: automatically lose the match
    KISS = 555        #: both sides treated as "winning"
    SPECIAL = -999    #: SpecialCard (ignore value)
    # Note: WIN and LOSE as opposites is counted upon by Card.apply()

    @staticmethod
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
    CLONE = 6    #: the card is replaced by the first REQUIRED suit, value
                 #      VALUE: new Card (substituted dynamically)
    FLUSH = 7    #: the player's hand is flushed and refilled
                 #      VALUE: N/A
                 

class AchieveType:
    """Types of Achievements to shoot for."""
    SCORE = 0    #: suit or total score threshold
    PLAY = 1     #: number of games played
    WIN = 2      #: number of games won
    STREAK = 3   #: number of games won in a row
    ROUND = 4    ## marker to start round-based types
    USE = 5      #: use a specific card or suit
    WAIT = 6     #: hold a specific card or suit

    @classmethod
    def per_round(cls, achievetype):
        return achievetype > cls.ROUND


def FileReader(filename):

    """Read [TAG]Value text files. Return a generator of (tag, value) pairs."""
        
    file = open(filename, 'r')
    try:
        for line in file:
            if line == "\n":
                continue
            match = re.search('\[(.*)\](.*)', line.strip())
            if not match:
                warnings.warn("Unexpected text in %s: %s" 
                                % (filename, line),
                              SyntaxWarning)
                continue

            yield(match.group(1).upper(), match.group(2))
    finally:
        file.close()
    
