import os
import unittest

from rendezvous.gameplay import Scoreboard
from rendezvous.statistics import *


class DummyDeckDefinition:
    suits = ["Test Suit"]


class TestBaseStats(unittest.TestCase):

    """Verify data storage and retrieval via BaseStats."""

    def setUp(self):
        self.s = BaseStats()

    def test_init(self):
        self.assertEqual(self.s.wins, 0)
        self.assertEqual(self.s.losses, 0)
        self.assertEqual(self.s.draws, 0)  # property!
        self.assertEqual(self.s.played, 0)
        self.assertEqual(self.s.win_streak, 0)
        self.assertEqual(self.s.best_streak, 0)

    def test_string(self):
        self.assertEqual(str(self.s), "(0, 0, 0, 0, 0)")

    def test_win(self):
        self.s.win()
        self.assertEqual(str(self.s), "(1, 0, 1, 1, 1)")

    def test_loss(self):
        self.s.lose()
        self.assertEqual(str(self.s), "(0, 1, 1, 0, 0)")

    def test_draw(self):
        self.s.draw()
        self.assertEqual(str(self.s), "(0, 0, 1, 0, 0)")

    def test_streak(self):
        self.s.win()
        self.s.win()
        self.assertEqual(self.s.win_streak, 2)
        self.s.draw()
        self.assertEqual(self.s.win_streak, 0)

    def test_best_streak(self):
        self.s.win()
        self.s.win()
        self.s.draw()
        self.assertEqual(self.s.best_streak, 2)

    def test_load(self):
        self.s = BaseStats("(1, 2, 4, 0, 1)")
        self.assertEqual(str(self.s), "(1, 2, 4, 0, 1)")
        self.assertEqual(self.s.draws, 1)


class TestStatistics(unittest.TestCase):

    """Verify data storage and retrieval via Statistics."""
    
    def setUp(self):
        self.s = Statistics('test_stats.test')
        self.score = Scoreboard(DummyDeckDefinition())
        
    def tearDown(self):
        try:
            os.remove('test_stats.test')
        except OSError:
            pass
        
    def test_init(self):
        self.assertEqual(str(self.s.base), "(0, 0, 0, 0, 0)")
        self.assertEqual(self.s.decks, {})
        self.assertEqual(self.s.suits, {})
        
    def test_record_win(self):
        self.score.scores = [[500], [400]]
        self.s.record_game("Test", self.score, 0)
        self.assertEqual(str(self.s.base), "(1, 0, 1, 1, 1)")
        self.assertEqual(str(self.s.decks), "{'Test': (1, 0, 1, 1, 1)}")
        self.assertEqual(str(self.s.suits), "{'Test Suit': (1, 0, 1, 1, 1)}")
        
    def test_record_draw(self):
        self.score.scores = [[500], [500]]
        self.s.record_game("Test", self.score, 0)
        self.assertEqual(str(self.s.base), "(0, 0, 1, 0, 0)")
        
    def test_record_loss(self):
        self.score.scores = [[500], [600]]
        self.s.record_game("Test", self.score, 0)
        self.assertEqual(str(self.s.base), "(0, 1, 1, 0, 0)")
        
    def test_retrieve(self):
        self.score.scores = [[500], [400]]
        self.s.record_game("Test", self.score, 0)
        s = Statistics('test_other.test')
        self.assertEqual(str(s.base), "(0, 0, 0, 0, 0)")
        s = Statistics('test_stats.test')
        self.assertEqual(str(s.base), "(1, 0, 1, 1, 1)")
