import random


class Card:
    """A single standard RendezVous card.

    Attributes:
      name        -- a user-friendly name for the card
      description -- a user-friendly description of the card's purpose
      suit        -- the name of the card's suit
      value       -- the value of the card

    """

    def __init__(self, suit, value):
        """Set name and description based on the suit and value combination."""
        self.name = "%s %s" % (suit, value)
        self.description = "A normal %s card worth %s points." % (suit, value)
        self.suit = suit
        self.value = value

    def __str__(self):
        """Return the name of the card."""
        return self.name

    def __repr__(self):
        """Return the initialization statement for this Card."""
        return "%s(%s, %s)" % (self.__class__.__name__,
                               repr(self.suit), repr(self.value))

    def __eq__(self, other):
        """Equality rests on both suit and value."""
        return self.suit == other.suit and self.value == other.value

    def __lt__(self, other):
        """Compare by value only."""
        return self.value < other.value

    
class DeckDefinition:
    
    """The available cards to play with."""

    name = "Standard RendezVous Deck"
    desc = "A simple 5-suit deck."
    suits = ['Boyfriend', 'Girlfriend', 'Spy', 'Counterspy', 'Time']
    values = list(range(1, 11))
    specials = []

    def cards(self):
        """Generator; return all card in the deck, unshuffled."""
        for suit in self.suits:
            for value in self.values:
                yield Card(suit, value)
        for special in self.specials:
            yield special


class Deck:
    
    """A player's deck of cards.

    Methods:
      shuffle -- reshuffle the entire deck and start from the beginning
      draw    -- return the top card from the deck

    """

    def __init__(self, cards, shuffle=True):
        """Prep the card list."""
        self._cards = list(cards)
        self._next = self._draw()
        if shuffle:
            self.shuffle()

    def shuffle(self):
        """Shuffle the full deck together."""
        random.shuffle(self._cards)
        self._next = self._draw()

    def _draw(self):
        """Generator; return each card in the current deck."""
        for card in self._cards:
            yield card

    def draw(self, auto_shuffle=True):
        """Return the next card in the current deck."""
        try:
            return next(self._next)
        except StopIteration:
            if not auto_shuffle:
                raise
            self.shuffle()
            return next(self._next)
        
        
