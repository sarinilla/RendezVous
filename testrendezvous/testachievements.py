import os
import unittest

from rendezvous.deck import SpecialCard
from rendezvous.gameplay import Scoreboard
from rendezvous.statistics import Statistics
from rendezvous.achievements import *


class TestAchievement(unittest.TestCase):

    """Verify the simple storage and usage of an Achievement."""
    
    def setUp(self):
        """Create a simple Achievement for testing."""
        self.a = Achievement("Name", "", "SpecialCard")
    
    def test_init(self):
        self.assertEqual(self.a.name, "Name")
        self.assertEqual(self.a.description, "")
        self.assertEqual(self.a.reward, "SpecialCard")
        
    def test_string(self):
        self.assertEqual(str(self.a), "Name")
        
    def test_equality(self):
        """Verify Achievement equality."""
        self.assertEqual(self.a, Achievement("Name", "", "SpecialCard"))
        
    def test_string_equality(self):
        """Verify that Achievements can be found by name."""
        self.assertEqual(self.a, "Name")
        
    def test_parse_play(self):
        self.a._parse_code("Play 5")
        self.assertEqual(self.a.type, AchieveType.PLAY)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.description,
                         "Play 5 games of RendezVous.")
                         
    def test_parse_win(self):
        self.a._parse_code("Win 5")
        self.assertEqual(self.a.type, AchieveType.WIN)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.description,
                         "Win at least 5 games of RendezVous.")

    def test_parse_streak(self):
        self.a._parse_code("Streak 5")
        self.assertEqual(self.a.type, AchieveType.STREAK)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.description,
                         "Win 5 games of RendezVous in a row.")
        
    def test_parse_enemy(self):
        self.a._parse_code("Enemy Each < 0")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.ENEMY)
        self.assertEqual(self.a.suit, SpecialSuit.EACH)
        self.assertEqual(self.a.operator, Operator.LESS_THAN)
        self.assertEqual(self.a.value, 0)
        self.assertEqual(self.a.description,
             "Finish a game with the dealer's score less than 0 in every suit.")
                         
    def test_parse_friendly(self):
        self.a._parse_code("Friendly Each < 0")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, SpecialSuit.EACH)
        self.assertEqual(self.a.operator, Operator.LESS_THAN)
        self.assertEqual(self.a.value, 0)
        self.assertEqual(self.a.description,
             "Finish a game with your score less than 0 in every suit.")
             
    def test_parse_total(self):
        self.a._parse_code("Friendly Total 800")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, SpecialSuit.TOTAL)
        self.assertEqual(self.a.operator, Operator.AT_LEAST)
        self.assertEqual(self.a.value, 800)
        self.assertEqual(self.a.description,
             "Finish a game with your total score at least 800.")
             
    def test_parse_any(self):
        self.a._parse_code("Any 400")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, SpecialSuit.ANY)
        self.assertEqual(self.a.operator, Operator.AT_LEAST)
        self.assertEqual(self.a.value, 400)
        self.assertEqual(self.a.description,
             "Finish a game with your score at least 400 in any suit.")
             
    def test_parse_one_win(self):
        self.a._parse_code("One < Win")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, SpecialSuit.ONE)
        self.assertEqual(self.a.operator, Operator.LESS_THAN)
        self.assertEqual(self.a.value, SpecialValue.WIN)
        self.assertEqual(self.a.description,
             "Win a game in exactly one suit.")
    
    def test_override_description(self):
        self.a.description = "Test Desc"
        self.a._parse_code("One Win")
        self.assertEqual(self.a.description, "Test Desc")
        
        
class DummyDeckDefinition:
    suits = ["Boyfriend", "Girlfriend"]


class TestAchievementCheck(unittest.TestCase):

    def setUp(self):
        self.a = Achievement('Test')
        self.score = Scoreboard(DummyDeckDefinition())
        self.stats = Statistics()

    def test_check_play_less(self):
        self.a._parse_code("Play 1")
        self.stats.played = 0
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_play_equal(self):
        self.a._parse_code("Play 1")
        self.stats.played = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_play_greater(self):
        self.a._parse_code("Play 1")
        self.stats.played = 2
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_win_less(self):
        self.a._parse_code("Win 1")
        self.stats.wins = 0
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_win_equal(self):
        self.a._parse_code("Win 1")
        self.stats.wins = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_win_greater(self):
        self.a._parse_code("Win 1")
        self.stats.wins = 2
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_streak_less(self):
        self.a._parse_code("Streak 1")
        self.stats.win_streak = 0
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_streak_equal(self):
        self.a._parse_code("Streak 1")
        self.stats.win_streak = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_streak_greater(self):
        self.a._parse_code("Streak 1")
        self.stats.win_streak = 2
        self.assertTrue(self.a.check(self.score, 0, self.stats))
        
    def test_total_false(self):
        self.a._parse_code("500")
        self.score.scores = [[200, 200], [600, 600]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        
    def test_total_true(self):
        self.a._parse_code("500")
        self.score.scores = [[200, 300], [100, 100]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))
        
    def test_any_false(self):
        self.a._parse_code("Any 500")
        self.score.scores = [[200, 200], [600, 600]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        
    def test_any_true(self):
        self.a._parse_code("Any 500")
        self.score.scores = [[600, 600], [200, 200]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))
        
    def test_one_none(self):
        self.a._parse_code("One 500")
        self.score.scores = [[200, 200], [600, 600]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        
    def test_one_one(self):
        self.a._parse_code("One 500")
        self.score.scores = [[600, 200], [600, 600]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))
        
    def test_one_multi(self):
        self.a._parse_code("One 500")
        self.score.scores = [[600, 600], [600, 600]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        
    def test_each_some(self):
        self.a._parse_code("Each 500")
        self.score.scores = [[600, 200], [600, 600]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        
    def test_each_all(self):
        self.a._parse_code("Each 500")
        self.score.scores = [[600, 600], [200, 200]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))
        
    def test_enemy(self):
        self.a._parse_code("Enemy Each 500")
        self.score.scores = [[600, 200], [600, 600]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))
        
    def test_less_than(self):
        self.a._parse_code("Any < 500")
        self.score.scores = [[200, 200], [600, 600]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))
        
    def test_suit_win_false(self):
        self.a._parse_code("Boyfriend WIN")
        self.assertEqual(self.a.suit, "Boyfriend")
        self.score.scores = [[100, 500], [200, 300]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        
    def test_suit_win_true(self):
        self.a._parse_code("Boyfriend WIN")
        self.score.scores = [[400, 500], [200, 300]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))
        
    def test_suit_lose_false(self):
        self.a._parse_code("Boyfriend Lose")
        self.score.scores = [[400, 500], [200, 300]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        
    def test_suit_lose_true(self):
        self.a._parse_code("Boyfriend Lose")
        self.score.scores = [[100, 500], [200, 300]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))
        
        
class TestAchievementList(unittest.TestCase):

    """Verify input/output of achievement lists."""
    
    def setUp(self):
        """Load the default Achievements for testing."""
        self.a = AchievementList("test_unlock.test")
        
    def tearDown(self):
        """Remove the unlock file."""
        os.remove("test_unlock.test")
        
    def test_init(self):
        self.assertEqual(repr(self.a.available[0]), 
                         "Achievement('RendezVous Beginner', 'Play a game of RendezVous.', 'Reinforcements')")
        self.assertEqual(len(self.a.available), 24)
        self.assertEqual(self.a.achieved, [])
        self.assertTrue(os.path.isfile("test_unlock.test"))
        
    def test_achieve(self):
        """Verify that Achievements are recorded and rewards returned."""
        self.assertNotIn("RendezVous Student", self.a.achieved)
        r = self.a.achieve("RendezVous Student")
        self.assertEqual(r.reward, "Gossip")
        self.assertIn("RendezVous Student", self.a.achieved)
        
    def test_achieve_no_reward(self):
        """Verify that None is returned from reward-less Achievements."""
        r = self.a.achieve("RendezVous Addict")
        self.assertIs(r.reward, None)
        
    def test_achieve_invalid(self):
        """Verify behavior when an invalid Achievement is awarded."""
        self.assertRaises(AttributeError, self.a.achieve, "Invalid Achievement")
        
    def test_achieve_duplicate(self):
        """Verify that each Achievement is counted only once."""
        self.assertEqual(len(self.a.achieved), 0)
        self.a.achieve("RendezVous Student")
        self.a.achieve("RendezVous Student")
        self.assertEqual(len(self.a.achieved), 1)
        
    def test_unlocked(self):
        """Verify that SpecialCards are unlocked properly."""
        self.assertFalse(self.a.unlocked("Gossip"))
        self.a.achieve("RendezVous Student")
        self.assertTrue(self.a.unlocked("Gossip"))
        
    def test_unlocked_card(self):
        """Verify that SpecialCards can be passed directly."""
        sc = SpecialCard("Gossip", "Desc", None, None, None)
        self.assertFalse(self.a.unlocked(sc))
        self.a.achieve("RendezVous Student")
        self.assertTrue(self.a.unlocked(sc))
        
    def test_unlocked_invalid(self):
        """Verify unlocked SpecialCards not associated with an Achievement."""
        self.assertTrue(self.a.unlocked("Invalid SpecialCard"))


if __name__ == "__main__":
    unittest.main()
