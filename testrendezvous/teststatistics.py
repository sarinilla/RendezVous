import os
import unittest

from rendezvous.gameplay import Scoreboard
from rendezvous.statistics import *


class DummyDeckDefinition:
    suits = ["Test Suit"]


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
        self.assertEqual(self.s.wins, 0)
        self.assertEqual(self.s.played, 0)
        self.assertEqual(self.s.win_streak, 0)
        
    def test_record_win(self):
        self.score.scores = [[500], [400]]
        self.s.record_game(self.score, 0)
        self.assertEqual(self.s.wins, 1)
        self.assertEqual(self.s.played, 1)
        self.assertEqual(self.s.win_streak, 1)
        
    def test_record_draw(self):
        self.score.scores = [[500], [500]]
        self.s.record_game(self.score, 0)
        self.assertEqual(self.s.wins, 0)
        self.assertEqual(self.s.played, 1)
        self.assertEqual(self.s.win_streak, 0)
        
    def test_record_loss(self):
        self.score.scores = [[500], [600]]
        self.s.record_game(self.score, 0)
        self.assertEqual(self.s.wins, 0)
        self.assertEqual(self.s.played, 1)
        self.assertEqual(self.s.win_streak, 0)
        
    def test_win_streak(self):
        self.score.scores = [[500], [400]]
        self.s.record_game(self.score, 0)
        self.s.record_game(self.score, 0)
        self.assertEqual(self.s.win_streak, 2)
        self.score.scores = [[500], [600]]
        self.s.record_game(self.score, 0)
        self.assertEqual(self.s.win_streak, 0)
        
    def test_retrieve(self):
        self.score.scores = [[500], [400]]
        self.s.record_game(self.score, 0)
        s = Statistics('test_other.test')
        self.assertEqual(s.wins, 0)
        self.assertEqual(s.played, 0)
        self.assertEqual(s.win_streak, 0)
        s = Statistics('test_stats.test')
        self.assertEqual(s.wins, 1)
        self.assertEqual(s.played, 1)
        self.assertEqual(s.win_streak, 1)
