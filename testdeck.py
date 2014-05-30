import unittest

from deck import *


class TestCard(unittest.TestCase):

    """Test the Card class."""

    def setUp(self):
        """Initialize a simple card for testing."""
        self.c = Card("My Suit", 5)

    def test_attributes(self):
        """Test the __init__ function's attribute settings."""
        self.c = Card("My Suit", 5)
        self.assertEqual(self.c.name, "My Suit 5")
        self.assertEqual(self.c.description, "A normal My Suit card worth 5 points.")
        self.assertEqual(self.c.suit, "My Suit")
        self.assertEqual(self.c.value, 5)

    def test_string(self):
        """Test the string conversion."""
        self.assertEqual(str(self.c), "My Suit 5")

    def test_repr(self):
        """Test the Python-style string conversion."""
        self.assertEqual(repr(self.c), "Card('My Suit', 5)")

    def test_equality(self):
        """Verify that equality rests on both suit and value."""
        self.assertEqual(self.c, self.c)
        self.assertEqual(self.c, Card("My Suit", 5))
        self.assertNotEqual(self.c, Card("No Suit", 5))
        self.assertNotEqual(self.c, Card("My Suit", 1))

    def test_comparison(self):
        """Verify that < comparison rests on value only."""
        four = Card("My Suit", 4)
        six = Card("My Suit", 6)
        suit = Card("No Suit", 5)
        self.assertTrue(self.c < six)
        self.assertFalse(self.c > six)
        self.assertFalse(self.c < four)
        self.assertTrue(self.c > four)
        self.assertFalse(self.c < suit)
        self.assertFalse(self.c > suit)


class TestDeck(unittest.TestCase):

    """Test the Deck class."""

    def setUp(self):
        """Initialize a simple deck for testing."""
        self.d = Deck([2, 4, 11], False)

    def test_attributes(self):
        """Test the __init__ function's attribute settings."""
        self.assertEqual(self.d._cards, [2, 4, 11])

    def test_draw(self):
        """Test that cards are drawn properly."""
        self.assertEqual(self.d.draw(False), 2)
        self.assertEqual(self.d.draw(False), 4)
        self.assertEqual(self.d.draw(False), 11)
        self.assertRaises(StopIteration, self.d.draw, False)

    def test_shuffle(self):
        """Test that the cards are shuffled correctly."""
        self.d = Deck(list(range(10)))
        self.d.shuffle()
        self.assertNotEqual(self.d._cards, list(range(10)))
        self.assertEqual(sorted(self.d._cards), list(range(10)))

    def test_initial_shuffle(self):
        """Test that the cards begin shuffled by default."""
        self.d = Deck(list(range(10)))
        self.assertNotEqual(self.d._cards, list(range(10)))
        self.assertEqual(sorted(self.d._cards), list(range(10)))

    def test_auto_shuffle(self):
        """Verify that the draw command auto-shuffles by default."""
        self.assertEqual(self.d.draw(), 2)
        self.assertEqual(self.d.draw(), 4)
        self.assertEqual(self.d.draw(), 11)
        self.assertIn(self.d.draw(), [2, 4, 11])


class TestDeckDefinition(unittest.TestCase):

    """Test the definition of a custom playing deck."""

    def setUp(self):
        """Create the standard deck."""
        self.dd = DeckDefinition()

    def test_attributes(self):
        """Verify the simple storage."""
        self.assertEqual(self.dd.name, "Standard RendezVous Deck")
        self.assertEqual(self.dd.desc, "A simple 5-suit deck.")
        self.assertEqual(self.dd.suits, ["Boyfriend", "Girlfriend", "Spy",
                                         "Counterspy", "Time"])
        self.assertEqual(self.dd.values, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(self.dd.specials, [])

    def test_generator(self):
        """Verify the generator yields the full sorted deck."""
        expected = []
        for suit in ['Boyfriend', 'Girlfriend', 'Spy', 'Counterspy', 'Time']:
            for value in range(1, 11):
                expected.append(Card(suit, value))
        self.assertEqual(list(self.dd.cards()), expected)


if __name__ == "__main__":
    unittest.main()
