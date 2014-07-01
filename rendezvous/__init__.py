import warnings
import re
import os


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

    @staticmethod
    def all():
        for i in (SpecialSuit.ANY, SpecialSuit.EACH, SpecialSuit.ONE,
                  SpecialSuit.TOTAL):
            yield i


class SpecialValue:
    """Special non-numerical card values."""
    WIN = 10000       #: automatically win the match
    LOSE = -10000     #: automatically lose the match
    DRAW = 33333      #: notes a tie
    KISS = 55555      #: both sides treated as "winning"
    SPECIAL = -99999  #: SpecialCard (ignore value)
    # Note: WIN and LOSE as opposites is counted upon by Card.apply()

    @staticmethod
    def all():
        for i in (SpecialValue.WIN, SpecialValue.LOSE, SpecialValue.DRAW,
                  SpecialValue.KISS):
            yield i


class TargetField:
    """Target field of a card."""
    ALL = 0      #: both suit and value; implicitly includes specials
    SUIT = 1     #: one of the five standard suits
    VALUE = 2    #: one of the ten standard values


class EffectType:
    """Types of things SpecialCards can do."""
    BUFF = 0       #: adjust the perceived value of the card
                   #      VALUE: +/- card value, or SpecialValue.WIN/LOSE
    WAIT = 1       #: force the card to wait through the next round
                   #      VALUE: N/A
    SWITCH = 2     #: card value is switched with its opponent
                   #      VALUE: new value (substituted dynamically)
    REVERSE = 3    #: card value is reversed (1 becomes 10)
                   #      VALUE: N/A
    REPLACE = 4    #: card suit is replaced with the one given
                   #      VALUE: new suit
    KISS = 5       #: the card's match is kissed (both treated as a win)
                   #      VALUE: N/A
    CLONE = 6      #: the card is replaced by the first REQUIRED suit, value
                   #      VALUE: new Card (substituted dynamically)
    FLUSH = 7      #: the player's hand is flushed and refilled
                   #      VALUE: N/A
    RANDOMIZE = 8  #: the card is replaced with a random suit and/or value
                   #      VALUE: choice of TargetField
                 

class AchieveType:
    """Types of Achievements to shoot for."""
    MULTIPLE = -1  #: multiple sub-achievement types
    SCORE = 0      #: suit or total score threshold
    
    PLAY = 1       #: number of games played
    WIN = 2        #: number of games won
    LOSE = 3       #: number of games lost
    DRAW = 4       #: number of games tied
    STREAK = 5     #: number of games won/lost/tied in a row
    
    ROUND = 8      ## marker to start round-based types
    USE = 9        #: use a specific card or suit
    WAIT = 10      #: hold a specific card or suit

    @classmethod
    def per_round(cls, achievetype):
        return achievetype > cls.ROUND

    @classmethod
    def stats(cls, achievetype):
        return achievetype > cls.SCORE and not cls.per_round(achievetype)


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

            yield(match.group(1).strip().upper(), match.group(2).strip())
    finally:
        file.close()


class Currency:

    """Some form of currency with which to purchase items."""

    def __init__(self, name, description, directory="player"):
        self.name = name
        self.plural = self._get_plural()
        self.description = description
        self._balance = 0
        self.filename = os.path.join(directory, name + ".txt")
        if not os.path.isdir(directory):
            os.mkdir(directory)
        self._read()

    def _get_plural(self):
        """Return the proper plural of self.name."""
        if self.name.endswith("s"):
            return self.name + "es"
        return self.name + "s"

    def __str__(self):
        """Return e.g. "13 kisses"."""
        return "%s %s" % (self.balance,
                          self.name if self.balance == 1 else self.plural)

    # Use functions to allow record-keeping later if we choose...
    def earn(self, number, reason=""):
        """Record earned currency."""
        self.balance += number

    def purchase(self, item, price):
        """Debit the given price for the item; return True for success."""
        if self.balance >= price:
            self.balance -= price
            return True
        return False

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        self._balance = value
        self._write()

    def _read(self):
        """Read the current balance from a file."""
        try:
            f = open(self.filename, 'r')
        except:
            self._balance = 0
            return
        self._balance = int(f.readline())
        f.close()

    def _write(self):
        """Save the current balance to a file."""
        f = open(self.filename, 'w')
        try:
            f.write(str(self._balance))
        finally:
            f.close()
