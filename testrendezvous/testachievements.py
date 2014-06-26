import os
import unittest

from rendezvous.deck import SpecialCard, Card
from rendezvous.gameplay import Scoreboard, Gameboard
from rendezvous.statistics import Statistics, BaseStats
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
        self.assertEqual(self.a.suit, SpecialSuit.ANY)
        self.assertEqual(self.a.description,
                         "Play 5 games of RendezVous.")

    def test_parse_play_specific(self):
        self.a._parse_code("Play 5 Specific")
        self.assertEqual(self.a.type, AchieveType.PLAY)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, "Specific")
        self.assertEqual(self.a.description,
                         "Play 5 games of RendezVous with Specific.")
                         
    def test_parse_win(self):
        self.a._parse_code("Win 5")
        self.assertEqual(self.a.type, AchieveType.WIN)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, SpecialSuit.ANY)
        self.assertEqual(self.a.description,
                         "Win at least 5 games of RendezVous.")
                         
    def test_parse_win_specific(self):
        self.a._parse_code("Win 5 Specific")
        self.assertEqual(self.a.type, AchieveType.WIN)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, "Specific")
        self.assertEqual(self.a.description,
                         "Win at least 5 games of RendezVous with Specific.")

    def test_parse_streak(self):
        self.a._parse_code("Streak 5")
        self.assertEqual(self.a.type, AchieveType.STREAK)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, SpecialSuit.ANY)
        self.assertEqual(self.a.description,
                         "Win 5 games of RendezVous in a row.")

    def test_parse_streak(self):
        self.a._parse_code("Streak 5 Specific")
        self.assertEqual(self.a.type, AchieveType.STREAK)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, "Specific")
        self.assertEqual(self.a.description,
                         "Win 5 games of RendezVous in a row with Specific.")
        
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

    def test_parse_equal(self):
        self.a._parse_code("Each == 400")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, SpecialSuit.EACH)
        self.assertEqual(self.a.operator, Operator.EXACTLY)
        self.assertEqual(self.a.value, 400)
        self.assertEqual(self.a.description,
             "Finish a game with your score exactly 400 in every suit.")

    def test_parse_suit_value(self):
        self.a._parse_code("Boyfriend < Girlfriend")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, "Boyfriend")
        self.assertEqual(self.a.operator, Operator.LESS_THAN)
        self.assertEqual(self.a.value, "Girlfriend")
        self.assertEqual(self.a.description,
             "Finish a game with your Boyfriend score less than that of your Girlfriend.")

    def test_parse_suit_index(self):
        self.a._parse_code("Boyfriend < SUIT1")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, "Boyfriend")
        self.assertEqual(self.a.operator, Operator.LESS_THAN)
        self.assertEqual(self.a.value, "SUIT1")
        self.assertEqual(self.a.description,
             "Finish a game with your Boyfriend score less than that of your first suit.")
             
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

    def test_parse_only(self):
        self.a._parse_code("Only Specific Win")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 0)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, "Specific")
        self.assertEqual(self.a.operator, Operator.AT_LEAST)
        self.assertEqual(self.a.value, SpecialValue.WIN)
        self.assertEqual(self.a.description,
             "Win a game in only Specific.")

    def test_parse_suit_index(self):
        self.a._parse_code("SUIT1 200")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, "SUIT1")
        self.assertEqual(self.a.description,
             "Finish a game with your first suit score at least 200.")

    def test_parse_use(self):
        self.a._parse_code("Use Boyfriend")
        self.assertEqual(self.a.type, AchieveType.USE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, "Boyfriend")
        self.assertEqual(self.a.description,
             "Play the Boyfriend card.")

    def test_parse_wait(self):
        self.a._parse_code("Wait 1 Boyfriend")
        self.assertEqual(self.a.type, AchieveType.WAIT)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, "Boyfriend")
        self.assertEqual(self.a.description,
             "Have the dealer hold your Boyfriend card.")

    def test_parse_use_enemy(self):
        self.a._parse_code("Use 2 Enemy Boyfriend")
        self.assertEqual(self.a.type, AchieveType.USE)
        self.assertEqual(self.a.count, 2)
        self.assertEqual(self.a.alignment, Alignment.ENEMY)
        self.assertEqual(self.a.suit, "Boyfriend")
        self.assertEqual(self.a.description,
             "Have the dealer play at least 2 Boyfriend cards.")

    def test_parse_wait_enemy(self):
        self.a._parse_code("Wait 2 Enemy Boyfriend")
        self.assertEqual(self.a.type, AchieveType.WAIT)
        self.assertEqual(self.a.count, 2)
        self.assertEqual(self.a.alignment, Alignment.ENEMY)
        self.assertEqual(self.a.suit, "Boyfriend")
        self.assertEqual(self.a.description,
             "Hold at least 2 of the dealer's Boyfriend cards.")

    def test_parse_use_any(self):
        self.a._parse_code("Use 4 FRIENDLY")
        self.assertEqual(self.a.type, AchieveType.USE)
        self.assertEqual(self.a.count, 4)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, SpecialSuit.ANY)
        self.assertEqual(self.a.description,
             "Play at least 4 cards.")

    def test_parse_wait_any(self):
        self.a._parse_code("Wait 4 ENEMY")
        self.assertEqual(self.a.type, AchieveType.WAIT)
        self.assertEqual(self.a.count, 4)
        self.assertEqual(self.a.alignment, Alignment.ENEMY)
        self.assertEqual(self.a.suit, SpecialSuit.ANY)
        self.assertEqual(self.a.description,
             "Hold at least 4 of the dealer's cards.")
    
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
        self.stats.base.played = 0
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_play_equal(self):
        self.a._parse_code("Play 1")
        self.stats.base.played = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_play_greater(self):
        self.a._parse_code("Play 1")
        self.stats.base.played = 2
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_play_deck(self):
        self.a._parse_code("Play 1 DeckName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'].played = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_play_suit(self):
        self.a._parse_code("Play 1 SuitName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'].played = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_win_less(self):
        self.a._parse_code("Win 1")
        self.stats.base.wins = 0
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_win_equal(self):
        self.a._parse_code("Win 1")
        self.stats.base.wins = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_win_greater(self):
        self.a._parse_code("Win 1")
        self.stats.base.wins = 2
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_win_deck(self):
        self.a._parse_code("Win 1 DeckName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'].wins = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_win_suit(self):
        self.a._parse_code("Win 1 SuitName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'].wins = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_streak_less(self):
        self.a._parse_code("Streak 1")
        self.stats.base.win_streak = 0
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_streak_equal(self):
        self.a._parse_code("Streak 1")
        self.stats.base.win_streak = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_streak_greater(self):
        self.a._parse_code("Streak 1")
        self.stats.base.win_streak = 2
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_streak_deck(self):
        self.a._parse_code("Streak 1 DeckName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'].win_streak = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_streak_suit(self):
        self.a._parse_code("Streak 1 SuitName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'].win_streak = 1
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

    def test_only_true(self):
        self.a._parse_code("Only Boyfriend 200")
        self.score.scores = [[300, 100], [100, 300]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_only_all(self):
        self.a._parse_code("Only Boyfriend 200")
        self.score.scores = [[300, 300], [100, 300]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_only_none(self):
        self.a._parse_code("Only Boyfriend 200")
        self.score.scores = [[100, 100], [300, 100]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        
    def test_enemy(self):
        self.a._parse_code("Enemy Each 500")
        self.score.scores = [[600, 200], [600, 600]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))
        
    def test_less_than(self):
        self.a._parse_code("Any < 500")
        self.score.scores = [[200, 200], [600, 600]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_equal(self):
        self.a._parse_code("Any = 500")
        self.score.scores = [[500, 100], [100, 100]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_equal_greater(self):
        self.a._parse_code("Any = 500")
        self.score.scores = [[600, 100], [100, 100]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        
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

    def test_suit_index_false(self):
        self.a._parse_code("SUIT1 200")
        self.score.scores = [[100, 300], [300, 300]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_suit_index_true(self):
        self.a._parse_code("SUIT2 200")
        self.score.scores = [[100, 300], [300, 300]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))


class TestAchievementCheckRound(unittest.TestCase):

    def setUp(self):
        self.a = Achievement('Test')
        self.board = Gameboard()
        
    def test_use(self):
        self.a._parse_code("USE Boyfriend")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Girlfriend", i+1) for i in range(4)]]
        self.assertFalse(self.a.check_round(self.board, 1))
        
    def test_use_true(self):
        self.a._parse_code("USE Boyfriend")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", 1)] +
                            [Card("Girlfriend", i+1) for i in range(3)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_wait(self):
        self.a._parse_code("WAIT Girlfriend")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Girlfriend", i+1) for i in range(4)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_wait_true(self):
        self.a._parse_code("WAIT Girlfriend")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Girlfriend", i+1) for i in range(4)]]
        self.board._wait[1][0] = True
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_count_less(self):
        self.a._parse_code("USE 2 Boyfriend")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", 1)] +
                            [Card("Girlfriend", i+1) for i in range(3)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_count_equal(self):
        self.a._parse_code("USE 2 Boyfriend")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", 1), Card("Boyfriend", 2)] +
                            [Card("Girlfriend", i+1) for i in range(2)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_count_greater(self):
        self.a._parse_code("USE 2 Boyfriend")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+1) for i in range(4)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_friendly(self):
        self.a._parse_code("WAIT FRIENDLY")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+1) for i in range(4)]]
        self.board._wait[1][1] = True
        self.assertFalse(self.a.check_round(self.board, 0))
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_enemy(self):
        self.a._parse_code("WAIT ENEMY")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+1) for i in range(4)]]
        self.board._wait[1][1] = True
        self.assertTrue(self.a.check_round(self.board, 0))
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_value(self):
        self.a._parse_code("Use Boyfriend 5")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+1) for i in range(4)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_value_true(self):
        self.a._parse_code("Use Boyfriend 5")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+2) for i in range(4)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_special(self):
        self.a._parse_code("Use Perfume")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+2) for i in range(4)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_special_true(self):
        self.a._parse_code("Use Perfume")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+2) for i in range(3)] +
                            [SpecialCard("Perfume", "Desc", None, None, None)]]
        self.assertTrue(self.a.check_round(self.board, 1))
        
        
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
        
    def test_unlocked_tutorial(self):
        """Verify SpecialCards not unlocked until the first Achievement."""
        self.assertFalse(self.a.unlocked("Flowers"))
        self.a.achieve("RendezVous Student")
        self.assertTrue(self.a.unlocked("Flowers"))
        
    def test_unlocked_invalid(self):
        """Verify unlocked SpecialCards not associated with an Achievement."""
        self.a.achieve("RendezVous Student")
        self.assertTrue(self.a.unlocked("Invalid SpecialCard"))


if __name__ == "__main__":
    unittest.main()
