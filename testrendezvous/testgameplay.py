import unittest

from rendezvous.deck import Card, Deck, DeckDefinition
from rendezvous.specials import Effect
from rendezvous.gameplay import *


class TestHand(unittest.TestCase):

    def setUp(self):
        self.hand = Hand(Deck(DeckDefinition()))

    def test_init(self):
        """Verify attributes are initialized properly."""
        self.assertIsInstance(self.hand.deck, Deck)
        self.assertEqual(len(self.hand.cards), 10)

    def test_container(self):
        """Verify shortcut method for treating Hand as an array."""
        self.assertEqual(len(self.hand), 10)
        for i in range(10):
            self.assertIs(self.hand[i], self.hand.cards[i])
        for card in self.hand:
            self.assertIn(card, self.hand.cards)
        self.assertEqual(3, self.hand.index(self.hand[3]))
        self.assertEqual(self.hand[3], self.hand.pop(3))
        self.assertEqual(len(self.hand.cards), 9)

    def test_refill(self):
        """Verify hand is refilled properly after removal of cards."""
        self.hand.cards = self.hand.cards[0:3]
        self.assertEqual(len(self.hand.cards), 3)
        self.hand.refill()
        self.assertEqual(len(self.hand.cards), 10)

    def test_flush(self):
        """Verify hand is flushed and refilled in one move."""
        first = self.hand[0]
        last = self.hand[-1]
        self.hand.flush()
        self.assertEqual(len(self.hand), 10)
        self.assertNotIn(first, self.hand)
        self.assertNotIn(last, self.hand)

    @unittest.skip("need to be more intelligent anyway")
    def test_AI_play(self):
        """Test the (temporary) simple AI play."""
        self.assertEqual(self.hand[:4], self.hand.AI_play(None, None))


class TestGameBoard(unittest.TestCase):

    def setUp(self):
        self.board = Gameboard()

    def test_init(self):
        self.assertEqual(len(self.board.board), 2)
        self.assertEqual(len(self.board.board[0]), 4)

    def test_container(self):
        """Verify shortcut method of leaving out duplicate .board."""
        self.assertEqual(len(self.board), 2)
        self.assertEqual(len(self.board[0]), 4)
        self.assertEqual(sum([1 for card in self.board]), 8)

    def test_is_full(self):
        """Verify is_full method."""
        self.assertFalse(self.board.is_full(0))
        self.board[0][0] = Card("Test", 1)
        self.assertFalse(self.board.is_full(0))
        self.board[0][3] = Card("Test", 4)
        self.assertFalse(self.board.is_full(0))
        self.board[0][1] = Card("Test", 3)
        self.assertFalse(self.board.is_full(0))
        self.board[0][1] = Card("Test", 2)
        self.assertFalse(self.board.is_full(0))
        self.board[0][2] = Card("Test", 3)
        self.assertTrue(self.board.is_full(0))
        self.assertFalse(self.board.is_full(1))

    def test_play_cards_single(self):
        """Verify automatic card placement."""
        self.assertEqual([0], self.board.play_cards(0, [Card("Test", 1)]))
        self.assertEqual([1], self.board.play_cards(0, [Card("Test", 2)]))
        self.board[0][2] = Card("Test", 3)
        self.assertEqual([3], self.board.play_cards(0, [Card("Test", 4)]))
        self.assertEqual([],  self.board.play_cards(0, [Card("Test", 5)]))
        self.assertEqual(self.board.board[0], [Card("Test", 1),
                                               Card("Test", 2),
                                               Card("Test", 3),
                                               Card("Test", 4)])

    def test_play_cards_multi(self):
        """Verify automatic multi-card placement."""
        self.board[1][1] = Card("Wait", 1)
        self.assertEqual([0, 2, 3], self.board.play_cards(1, [Card("Test", 1),
                                                              Card("Test", 2),
                                                              Card("Test", 3)]))
        self.assertEqual(self.board.board[1], [Card("Test", 1),
                                               Card("Wait", 1),
                                               Card("Test", 2),
                                               Card("Test", 3)])  

    def test_waits(self):
        """Verify that WAIT works correctly."""
        self.board[0][3] = Card("Test", 1)
        self.board[1][3] = Card("Test", 2)
        self.board.wait(0, 3)
        self.board.next_round()
        self.assertEqual(self.board[0][3], Card("Test", 1))
        self.assertIs(self.board[1][3], None)        

    def test_waits_reset(self):
        """Verify that WAIT removes buffs correctly."""
        self.board[0][3] = Card("Test", 1)
        self.board[0][3].apply(Effect(EffectType.BUFF, 2))
        self.assertEqual(self.board[0][3], Card("Test", 3))
        self.board.wait(0, 3)
        self.board.next_round()
        self.assertEqual(self.board[0][3], Card("Test", 1))

    def test_clear(self):
        """Verify that WAIT does not affect a clear."""
        self.board[0][3] = Card("Test", 1)
        self.board[1][3] = Card("Test", 2)
        self.board.wait(0, 3)
        self.board.clear()
        self.assertIs(self.board[0][3], None)
        self.assertIs(self.board[1][3], None)


class TestScoreboard(unittest.TestCase):

    def setUp(self):
        self.score = Scoreboard(DeckDefinition())

    def test_init(self):
        """Verify the attributes set by __init__."""
        self.assertEqual(self.score.scores, [[0,0,0,0,0], [0,0,0,0,0]])
        self.assertEqual(self.score.suits, ["Boyfriend", "Girlfriend", "Spy", "Counterspy", "Time"])

    def test_container(self):
        """Verify shortcut method of leaving out duplicate .score."""
        self.assertEqual(len(self.score), 2)
        self.assertEqual(len(self.score[0]), 5)
        self.assertEqual(sum([1 for spot in self.score]), 10)

    def test_total(self):
        """Verify the total is calculated correctly."""
        self.score[0][0] = 10
        self.score[1][3] = 20
        self.assertEqual(self.score.total(0), 10)
        self.assertEqual(self.score.total(1), 20)

    def test_win(self):
        """Verify a win."""
        self.score._win(1, "Boyfriend")
        self.assertEqual(self.score.scores, [[0,0,0,0,0], [10,0,0,0,0]])

    def test_lose(self):
        """Verify a loss."""
        self.score._lose(0, "Time")
        self.assertEqual(self.score.scores, [[0,0,0,0,-10], [0,0,0,0,0]])

    def test_zero(self):
        """Verify that the scoreboard is zeroed on command."""
        self.score._win(1, "Boyfriend")
        self.score._lose(0, "Time")
        self.score.zero()
        self.assertEqual(self.score.scores, [[0,0,0,0,0], [0,0,0,0,0]])

    def test_score_friendly_kiss(self):
        """Verify that a friendly KISS is like a win."""
        self.score._score_match(0, Card("Boyfriend", SpecialValue.KISS),
                          1, Card("Girlfriend", 10))
        self.assertEqual(self.score.scores, [[10,10,0,0,0], [0,0,0,0,0]])
        
    def test_score_enemy_kiss(self):
        """Verify that an enemy KISS is like a win."""
        self.score._score_match(0, Card("Time", 5),
                          1, Card("Time", SpecialValue.KISS))
        self.assertEqual(self.score.scores, [[0,0,0,0,20], [0,0,0,0,0]])
        
    def test_score_friendly_win(self):
        """Verify a friendly WIN."""
        self.score._score_match(0, Card("Boyfriend", SpecialValue.WIN),
                          1, Card("Girlfriend", 10))
        self.assertEqual(self.score.scores, [[10,10,0,0,0], [0,0,0,0,0]])
        
    def test_score_enemy_lose(self):
        """Verify an enemy LOSE."""
        self.score._score_match(0, Card("Time", 5),
                          1, Card("Time", SpecialValue.LOSE))
        self.assertEqual(self.score.scores, [[0,0,0,0,20], [0,0,0,0,0]])
        
    def test_score_friendly_lose(self):
        """Verify a friendly LOSE."""
        self.score._score_match(0, Card("Boyfriend", SpecialValue.LOSE),
                          1, Card("Girlfriend", 10))
        self.assertEqual(self.score.scores, [[-10,0,0,0,0], [0,0,0,0,0]])
        
    def test_score_enemy_win(self):
        """Verify an enemy WIN."""
        self.score._score_match(0, Card("Time", 5),
                          1, Card("Time", SpecialValue.WIN))
        self.assertEqual(self.score.scores, [[0,0,0,0,-10], [0,0,0,0,0]])

    def test_score_kiss_win(self):
        """Verify that KISS overrides WIN."""
        self.score._score_match(0, Card("Boyfriend", SpecialValue.KISS),
                          1, Card("Time", SpecialValue.WIN))
        self.assertEqual(self.score.scores, [[10,0,0,0,10], [0,0,0,0,0]])

    def test_score_kiss_lose(self):
        """Verify that KISS overrides LOSE."""
        self.score._score_match(0, Card("Boyfriend", SpecialValue.LOSE),
                          1, Card("Time", SpecialValue.KISS))
        self.assertEqual(self.score.scores, [[10,0,0,0,10], [0,0,0,0,0]])
        
    def test_score_friendly_special(self):
        """Verify no points for a friendly SPECIAL."""
        self.score._score_match(0, Card("Boyfriend", SpecialValue.SPECIAL),
                          1, Card("Time", 1))
        self.assertEqual(self.score.scores, [[0,0,0,0,0], [0,0,0,0,0]])
        
    def test_score_enemy_special(self):
        """Verify no points for an enemy SPECIAL."""
        self.score._score_match(0, Card("Time", 10),
                          1, Card("Time", SpecialValue.SPECIAL))
        self.assertEqual(self.score.scores, [[0,0,0,0,0], [0,0,0,0,0]])
        
    def test_score_win_special(self):
        """Verify no points for a SPECIAL even on WIN."""
        self.score._score_match(0, Card("Time", SpecialValue.WIN),
                          1, Card("Time", SpecialValue.SPECIAL))
        self.assertEqual(self.score.scores, [[0,0,0,0,0], [0,0,0,0,0]])
        
    def test_score_lose_special(self):
        """Verify no points for a SPECIAL even on LOSE."""
        self.score._score_match(0, Card("Time", SpecialValue.SPECIAL),
                          1, Card("Time", SpecialValue.LOSE))
        self.assertEqual(self.score.scores, [[0,0,0,0,0], [0,0,0,0,0]])
        
    def test_score_kiss_special(self):
        """Verify no points for a SPECIAL even on KISS."""
        self.score._score_match(0, Card("Time", SpecialValue.KISS),
                          1, Card("Time", SpecialValue.SPECIAL))
        self.assertEqual(self.score.scores, [[0,0,0,0,0], [0,0,0,0,0]])
        
    def test_score_greater(self):
        """Verify a simple win."""
        self.score._score_match(0, Card("Spy", 5),
                          1, Card("Counterspy", 4))
        self.assertEqual(self.score.scores, [[0,0,10,10,0], [0,0,0,0,0]])
        
    def test_score_lesser(self):
        """Verify a simple loss."""
        self.score._score_match(0, Card("Spy", 5),
                          1, Card("Counterspy", 6))
        self.assertEqual(self.score.scores, [[0,0,-10,0,0], [0,0,0,0,0]])
        
    def test_score_draw(self):
        """Verify a simple tie."""
        self.score._score_match(0, Card("Spy", 5),
                          1, Card("Counterspy", 5))
        self.assertEqual(self.score.scores, [[0,0,0,0,0], [0,0,0,0,0]])


class TestRendezVousGame(unittest.TestCase):

    """Verify game methods."""

    pass


if __name__ == "__main__":
    unittest.main()
