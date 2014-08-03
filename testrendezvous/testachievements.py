import os
import unittest

from rendezvous import GameSettings, Alignment
from rendezvous.deck import SpecialCard, Card
from rendezvous.specials import Application
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
                         "Win 5 games of RendezVous.")
                         
    def test_parse_win_specific(self):
        self.a._parse_code("Win 5 Specific")
        self.assertEqual(self.a.type, AchieveType.WIN)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, "Specific")
        self.assertEqual(self.a.description,
                         "Win 5 games of RendezVous with Specific.")

    def test_parse_win_streak(self):
        self.a._parse_code("Streak 5")
        self.assertEqual(self.a.type, AchieveType.STREAK)
        self.assertEqual(self.a.value, AchieveType.WIN)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, SpecialSuit.ANY)
        self.assertEqual(self.a.description,
                         "Win 5 games of RendezVous in a row.")

    def test_parse_win_streak_specific(self):
        self.a._parse_code("Streak 5 Specific")
        self.assertEqual(self.a.type, AchieveType.STREAK)
        self.assertEqual(self.a.value, AchieveType.WIN)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, "Specific")
        self.assertEqual(self.a.description,
                         "Win 5 games of RendezVous in a row with Specific.")

    def test_parse_lose(self):
        self.a._parse_code("LOSE 5")
        self.assertEqual(self.a.type, AchieveType.LOSE)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, SpecialSuit.ANY)
        self.assertEqual(self.a.description,
                         "Lose 5 games of RendezVous.")
                         
    def test_parse_lose_specific(self):
        self.a._parse_code("Lose 5 Specific")
        self.assertEqual(self.a.type, AchieveType.LOSE)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, "Specific")
        self.assertEqual(self.a.description,
                         "Lose 5 games of RendezVous with Specific.")

    def test_parse_lose_streak(self):
        self.a._parse_code("Lose Streak 5")
        self.assertEqual(self.a.type, AchieveType.STREAK)
        self.assertEqual(self.a.value, AchieveType.LOSE)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, SpecialSuit.ANY)
        self.assertEqual(self.a.description,
                         "Lose 5 games of RendezVous in a row.")

    def test_parse_lose_streak_specific(self):
        self.a._parse_code("Lose Streak 5 Specific")
        self.assertEqual(self.a.type, AchieveType.STREAK)
        self.assertEqual(self.a.value, AchieveType.LOSE)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, "Specific")
        self.assertEqual(self.a.description,
                         "Lose 5 games of RendezVous in a row with Specific.")

    def test_parse_draw(self):
        self.a._parse_code("DRAW 5")
        self.assertEqual(self.a.type, AchieveType.DRAW)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, SpecialSuit.ANY)
        self.assertEqual(self.a.description,
                         "Tie 5 games of RendezVous.")
                         
    def test_parse_draw_specific(self):
        self.a._parse_code("Draw 5 Specific")
        self.assertEqual(self.a.type, AchieveType.DRAW)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, "Specific")
        self.assertEqual(self.a.description,
                         "Tie 5 games of RendezVous with Specific.")

    def test_parse_draw_streak(self):
        self.a._parse_code("Draw Streak 5")
        self.assertEqual(self.a.type, AchieveType.STREAK)
        self.assertEqual(self.a.value, AchieveType.DRAW)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, SpecialSuit.ANY)
        self.assertEqual(self.a.description,
                         "Tie 5 games of RendezVous in a row.")

    def test_parse_draw_streak_specific(self):
        self.a._parse_code("Draw Streak 5 Specific")
        self.assertEqual(self.a.type, AchieveType.STREAK)
        self.assertEqual(self.a.value, AchieveType.DRAW)
        self.assertEqual(self.a.count, 5)
        self.assertEqual(self.a.suit, "Specific")
        self.assertEqual(self.a.description,
                         "Tie 5 games of RendezVous in a row with Specific.")

    def test_parse_multiple_stat(self):
        self.a._parse_code("Win Specific")
        self.a._parse_code("Lose Another")
        self.assertEqual(self.a.type, AchieveType.MULTIPLE)
        self.assertEqual(self.a.criteria[0].type, AchieveType.WIN)
        self.assertEqual(self.a.criteria[0].count, 1)
        self.assertEqual(self.a.criteria[0].suit, "Specific")
        self.assertEqual(self.a.criteria[1].type, AchieveType.LOSE)
        self.assertEqual(self.a.criteria[1].count, 1)
        self.assertEqual(self.a.criteria[1].suit, "Another")
        self.assertEqual(self.a.description,
            "Win a game of RendezVous with Specific and lose it with Another.")
        
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

    def test_parse_suit_index_value(self):
        self.a._parse_code("Boyfriend < SUIT1")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, "Boyfriend")
        self.assertEqual(self.a.operator, Operator.LESS_THAN)
        self.assertEqual(self.a.value, "SUIT1")
        self.assertEqual(self.a.description,
             "Finish a game with your Boyfriend score less than that of your first suit.")

    def test_parse_suit_index_with_special(self):
        self.a._parse_code("Each == SUIT1")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, SpecialSuit.EACH)
        self.assertEqual(self.a.operator, Operator.EXACTLY)
        self.assertEqual(self.a.value, "SUIT1")
        self.assertEqual(self.a.description,
             "Finish a game with your score in every suit exactly that of your first suit.")

    def test_parse_suit_index_on_both(self):
        self.a._parse_code("SUIT1 < SUIT2")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, "SUIT1")
        self.assertEqual(self.a.operator, Operator.LESS_THAN)
        self.assertEqual(self.a.value, "SUIT2")
        self.assertEqual(self.a.description,
             "Finish a game with your first suit score less than that of your second suit.")
             
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

    def test_parse_suit_score(self):
        self.a._parse_code("Special 200")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, "Special")
        self.assertEqual(self.a.operator, Operator.AT_LEAST)
        self.assertEqual(self.a.value, 200)
        self.assertEqual(self.a.description,
            "Finish a game with your score at least 200 in Special.")
             
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
        self.a._parse_code("Only Specific Draw")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 0)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, "Specific")
        self.assertEqual(self.a.operator, Operator.AT_LEAST)
        self.assertEqual(self.a.value, SpecialValue.DRAW)
        self.assertEqual(self.a.description,
             "Tie a game in only Specific.")

    def test_parse_suit_index(self):
        self.a._parse_code("SUIT1 200")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, "SUIT1")
        self.assertEqual(self.a.operator, Operator.AT_LEAST)
        self.assertEqual(self.a.value, 200)
        self.assertEqual(self.a.description,
             "Finish a game with your first suit score at least 200.")

    def test_parse_two_words(self):
        self.a._parse_code("Two Words < 100")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, "Two Words")
        self.assertEqual(self.a.operator, Operator.LESS_THAN)
        self.assertEqual(self.a.value, 100)
        self.assertEqual(self.a.description,
            "Finish a game with your score less than 100 in Two Words.")

    def test_parse_two_suits(self):
        self.a._parse_code("Boyfriend OR Girlfriend < 100")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suits, ["Boyfriend", "Girlfriend"])
        self.assertEqual(self.a.operator, Operator.LESS_THAN)
        self.assertEqual(self.a.value, 100)
        self.assertEqual(self.a.description,
            "Finish a game with your score less than 100 in Boyfriend or Girlfriend.")

    def test_parse_multiple_suits(self):
        self.a._parse_code("Boyfriend OR Girlfriend OR Time < 100")
        self.assertEqual(self.a.type, AchieveType.SCORE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suits, ["Boyfriend", "Girlfriend", "Time"])
        self.assertEqual(self.a.operator, Operator.LESS_THAN)
        self.assertEqual(self.a.value, 100)
        self.assertEqual(self.a.description,
            "Finish a game with your score less than 100 in Boyfriend, Girlfriend, or Time.")
        
    def test_parse_multiple_score(self):
        self.a._parse_code("SUIT1 < 200")
        self.a._parse_code("SUIT2 Lose")
        self.assertEqual(self.a.type, AchieveType.MULTIPLE)
        self.assertEqual(self.a.criteria[0].type, AchieveType.SCORE)
        self.assertEqual(self.a.criteria[0].count, 1)
        self.assertEqual(self.a.criteria[0].alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.criteria[0].suit, "SUIT1")
        self.assertEqual(self.a.criteria[0].operator, Operator.LESS_THAN)
        self.assertEqual(self.a.criteria[0].value, 200)
        self.assertEqual(self.a.criteria[1].type, AchieveType.SCORE)
        self.assertEqual(self.a.criteria[1].count, 1)
        self.assertEqual(self.a.criteria[1].alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.criteria[1].suit, "SUIT2")
        self.assertEqual(self.a.criteria[1].operator, Operator.AT_LEAST)
        self.assertEqual(self.a.criteria[1].value, SpecialValue.LOSE)
        self.assertEqual(self.a.description,
            "Finish a game with your first suit score less than 200 and lose it in your second suit.")

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

    def test_parse_use_card_value(self):
        self.a._parse_code("Use Boyfriend 10")
        self.assertEqual(self.a.type, AchieveType.USE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, "Boyfriend 10")
        self.assertEqual(self.a.description,
             "Play the Boyfriend 10 card.")

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

    def test_parse_use_value(self):
        self.a._parse_code("Use 4 FRIENDLY < 5")
        self.assertEqual(self.a.type, AchieveType.USE)
        self.assertEqual(self.a.count, 4)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.suit, SpecialSuit.ANY)
        self.assertEqual(self.a.operator, Operator.LESS_THAN)
        self.assertEqual(self.a.value, 5)
        self.assertEqual(self.a.description,
             "Play at least 4 cards with a value less than 5.")

    def test_parse_master(self):
        self.a._parse_code("Master SpecialCard")
        self.assertEqual(self.a.type, AchieveType.MASTER)
        self.assertEqual(self.a.suit, "SpecialCard")
        self.assertEqual(self.a.description,
            "Play the SpecialCard card to its fullest.")

    def test_parse_master_odd_name(self):
        self.a._parse_code("Master 2+2=5")
        self.assertEqual(self.a.type, AchieveType.MASTER)
        self.assertEqual(self.a.suit, "2+2=5")
        self.assertEqual(self.a.description,
            "Play the 2+2=5 card to its fullest.")

    def test_parse_dunce(self):
        self.a._parse_code("Dunce Special Card")
        self.assertEqual(self.a.type, AchieveType.DUNCE)
        self.assertEqual(self.a.suit, "Special Card")
        self.assertEqual(self.a.description,
            "Play the Special Card card to NO effect.")

    def test_parse_match_win(self):
        self.a._parse_code("Match Win")
        self.assertEqual(self.a.type, AchieveType.MATCH)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.value, SpecialValue.WIN)
        self.assertEqual(self.a.count, SpecialSuit.TOTAL)
        self.assertEqual(self.a.description,
            "Win most of the matches in a round.")

    def test_parse_match_lose(self):
        self.a._parse_code("Match Lose")
        self.assertEqual(self.a.type, AchieveType.MATCH)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.value, SpecialValue.LOSE)
        self.assertEqual(self.a.count, SpecialSuit.TOTAL)
        self.assertEqual(self.a.description,
            "Lose most of the matches in a round.")

    def test_parse_match_draw(self):
        self.a._parse_code("Match Draw")
        self.assertEqual(self.a.type, AchieveType.MATCH)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.value, SpecialValue.DRAW)
        self.assertEqual(self.a.count, SpecialSuit.TOTAL)
        self.assertEqual(self.a.description,
            "Tie most of the matches in a round.")

    def test_parse_match_tie(self):
        self.a._parse_code("Match Tie")
        self.assertEqual(self.a.type, AchieveType.MATCH)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.value, SpecialValue.DRAW)
        self.assertEqual(self.a.count, SpecialSuit.TOTAL)
        self.assertEqual(self.a.description,
            "Tie most of the matches in a round.")

    def test_parse_match_count(self):
        self.a._parse_code("Match Win 2")
        self.assertEqual(self.a.type, AchieveType.MATCH)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.value, SpecialValue.WIN)
        self.assertEqual(self.a.count, 2)
        self.assertEqual(self.a.description,
            "Win at least 2 matches in a round.")

    def test_parse_match_count_one(self):
        self.a._parse_code("Match Lose 1")
        self.assertEqual(self.a.type, AchieveType.MATCH)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.value, SpecialValue.LOSE)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.description,
            "Lose at least 1 match in a round.")

    def test_parse_match_count_all(self):
        self.a._parse_code("Match Tie 4")
        self.assertEqual(self.a.type, AchieveType.MATCH)
        self.assertEqual(self.a.alignment, Alignment.FRIENDLY)
        self.assertEqual(self.a.value, SpecialValue.DRAW)
        self.assertEqual(self.a.count, 4)
        self.assertEqual(self.a.description,
            "Tie all 4 matches in a round.")

    def test_parse_match_enemy(self):
        self.a._parse_code("Match Enemy Win 1")
        self.assertEqual(self.a.type, AchieveType.MATCH)
        self.assertEqual(self.a.alignment, Alignment.ENEMY)
        self.assertEqual(self.a.value, SpecialValue.WIN)
        self.assertEqual(self.a.count, 1)
        self.assertEqual(self.a.description,
            "Have the dealer win at least 1 match in a round.")

    def test_parse_multiple_round(self):
        self.a._parse_code("Use Specific")
        self.a._parse_code("Use Another")
        self.assertEqual(self.a.type, AchieveType.MULTIPLE)
        self.assertEqual(self.a.criteria[0].type, AchieveType.USE)
        self.assertEqual(self.a.criteria[0].count, 1)
        self.assertEqual(self.a.criteria[0].suit, "Specific")
        self.assertEqual(self.a.criteria[1].type, AchieveType.USE)
        self.assertEqual(self.a.criteria[1].count, 1)
        self.assertEqual(self.a.criteria[1].suit, "Another")
        self.assertEqual(self.a.description,
            "Play the Specific card and in the same round play the Another card.")
    
    def test_override_description(self):
        self.a = Achievement("Name", "Test Desc")
        self.a._parse_code("One Win")
        self.assertEqual(self.a.description, "Test Desc")

    def test_append_description(self):
        self.a = Achievement("Name", "Test Desc\n", code="One Win",
                             append_description=True)
        self.assertEqual(self.a.description,
            "Test Desc\nWin a game in exactly one suit.")
        
        
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
        self.stats.base.losses = 1
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

    def test_check_lose_less(self):
        self.a._parse_code("Lose 1")
        self.stats.base.losses = 0
        self.stats.base.wins = 1
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_lose_equal(self):
        self.a._parse_code("Lose 1")
        self.stats.base.losses = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_lose_greater(self):
        self.a._parse_code("Lose 1")
        self.stats.base.losses = 2
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_lose_deck(self):
        self.a._parse_code("Lose 1 DeckName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'].losses = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_lose_suit(self):
        self.a._parse_code("Lose 1 SuitName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'].losses = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_draw_less(self):
        self.a._parse_code("Draw 1")
        self.stats.base.wins = 1
        self.stats.base.played = 1
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_draw_equal(self):
        self.a._parse_code("Draw 1")
        self.stats.base.played = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_draw_greater(self):
        self.a._parse_code("Draw 1")
        self.stats.base.played = 2
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_draw_deck(self):
        self.a._parse_code("Draw 1 DeckName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'].played = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_draw_suit(self):
        self.a._parse_code("Draw 1 SuitName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'].played = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_win_streak_less(self):
        self.a._parse_code("Streak 1")
        self.stats.base.streak = 0
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_win_streak_wrong(self):
        self.a._parse_code("Streak 1")
        self.stats.base.streak = 1
        self.stats.base.streak_type = SpecialValue.LOSE
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_win_streak_equal(self):
        self.a._parse_code("Streak 1")
        self.stats.base.streak = 1
        self.stats.base.streak_type = SpecialValue.WIN
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_win_streak_greater(self):
        self.a._parse_code("Streak 1")
        self.stats.base.win_streak = 2
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_win_streak_deck(self):
        self.a._parse_code("Streak 1 DeckName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'].win_streak = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_win_streak_suit(self):
        self.a._parse_code("Streak 1 SuitName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'].win_streak = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_lose_streak_less(self):
        self.a._parse_code("Lose Streak 1")
        self.stats.base.lose_streak = 0
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_lose_streak_wrong(self):
        self.a._parse_code("Lose Streak 1")
        self.stats.base.win_streak = 1
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_lose_streak_equal(self):
        self.a._parse_code("Lose Streak 1")
        self.stats.base.lose_streak = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_lose_streak_greater(self):
        self.a._parse_code("Lose Streak 1")
        self.stats.base.lose_streak = 2
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_lose_streak_deck(self):
        self.a._parse_code("Lose Streak 1 DeckName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'].lose_streak = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_lose_streak_suit(self):
        self.a._parse_code("Lose Streak 1 SuitName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'].lose_streak = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_draw_streak_less(self):
        self.a._parse_code("Draw Streak 1")
        self.stats.base.draw_streak = 0
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_draw_streak_wrong(self):
        self.a._parse_code("Draw Streak 1")
        self.stats.base.win_streak = 1
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_check_draw_streak_equal(self):
        self.a._parse_code("Draw Streak 1")
        self.stats.base.draw_streak = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_draw_streak_greater(self):
        self.a._parse_code("Draw Streak 1")
        self.stats.base.draw_streak = 2
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_draw_streak_deck(self):
        self.a._parse_code("Draw Streak 1 DeckName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.decks['DeckName'].draw_streak = 1
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_check_draw_streak_suit(self):
        self.a._parse_code("Draw Streak 1 SuitName")
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'] = BaseStats()
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        self.stats.suits['SuitName'].draw_streak = 1
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
        
    def test_less_than_false(self):
        self.a._parse_code("Any < 500")
        self.score.scores = [[600, 600], [600, 600]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        
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
        
    def test_suit_draw_false(self):
        self.a._parse_code("Boyfriend Draw")
        self.score.scores = [[400, 500], [200, 500]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))
        
    def test_suit_draw_true(self):
        self.a._parse_code("Boyfriend Draw")
        self.score.scores = [[400, 500], [400, 300]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_suit_index_false(self):
        self.a._parse_code("SUIT1 200")
        self.score.scores = [[100, 300], [300, 300]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_suit_index_true(self):
        self.a._parse_code("SUIT2 200")
        self.score.scores = [[100, 300], [300, 300]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_multiple_suits_neither(self):
        self.a._parse_code("Boyfriend OR Girlfriend 200")
        self.score.scores = [[100, 100], [300, 300]]
        self.assertFalse(self.a.check(self.score, 0, self.stats))

    def test_multiple_suits_first(self):
        self.a._parse_code("Boyfriend OR Girlfriend 200")
        self.score.scores = [[300, 100], [100, 100]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_multiple_suits_last(self):
        self.a._parse_code("Boyfriend OR Girlfriend 200")
        self.score.scores = [[100, 300], [100, 100]]
        self.assertTrue(self.a.check(self.score, 0, self.stats))

    def test_multiple_suits_both(self):
        self.a._parse_code("Boyfriend OR Girlfriend 200")
        self.score.scores = [[300, 300], [100, 100]]
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

    def test_use_enemy_false(self):
        self.a._parse_code("USE enemy Boyfriend")
        self.board.board = [[Card("Girlfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+1) for i in range(4)]]
        self.assertFalse(self.a.check_round(self.board, 1))


    def test_use_enemy_true(self):
        self.a._parse_code("USE enemy Boyfriend")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Girlfriend", i+1) for i in range(4)]]
        self.assertTrue(self.a.check_round(self.board, 1))


    def test_master_none(self):
        self.a._parse_code("MASTER Special")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+1) for i in range(4)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_master_partial(self):
        self.a._parse_code("MASTER Special")
        special = SpecialCard("Special", "Desc", None,
                              Application(alignment=Alignment.FRIENDLY,
                                          suits="Boyfriend"),
                              None)
        special.applied_to = [0, 1]
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [special, Card("Boyfriend", 1)] +
                            [Card("Girlfriend", i+1) for i in range(2)]]
        self.assertFalse(self.a.check_round(self.board, 1))
        
    def test_master_true(self):
        self.a._parse_code("MASTER Special")
        special = SpecialCard("Special", "Desc", None,
                              Application(alignment=Alignment.FRIENDLY,
                                          suits="Boyfriend"),
                              None)
        special.applied_to = [0, 3]
        self.board.board = [[Card("Girlfriend", i+1) for i in range(4)],
                            [special] +
                            [Card("Boyfriend", i+1) for i in range(3)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_master_enemy_false(self):
        self.a._parse_code("MASTER Special")
        special = SpecialCard("Special", "Desc", None,
                              Application(alignment=Alignment.ENEMY,
                                          suits="Boyfriend"),
                              None)
        special.applied_to = [3, 3]
        self.board.board = [[special] +
                            [Card("Boyfriend", i+1) for i in range(3)],
                            [special] +
                            [Card("Boyfriend", i+1) for i in range(3)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_master_enemy_true(self):
        self.a._parse_code("MASTER Special")
        special = SpecialCard("Special", "Desc", None,
                              Application(alignment=Alignment.ENEMY,
                                          suits="Boyfriend"),
                              None)
        special.applied_to = [4, 0]
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [special, Card("Girlfriend", 1)] +
                            [Card("Boyfriend", i+1) for i in range(2)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_master_all_enemy(self):
        self.a._parse_code("MASTER Special")
        special = SpecialCard("Special", "Desc", None,
                              Application(alignment=Alignment.ALL,
                                          suits="Boyfriend"),
                              None)
        special.applied_to = [3, 3]
        self.board.board = [[special] +
                            [Card("Boyfriend", i+1) for i in range(3)],
                            [special] +
                            [Card("Boyfriend", i+1) for i in range(3)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_master_all_friendly(self):
        self.a._parse_code("MASTER Special")
        special = SpecialCard("Special", "Desc", None,
                              Application(alignment=Alignment.ALL,
                                          suits="Boyfriend"),
                              None)
        special.applied_to = [4, 2]
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [special, Card("Girlfriend", 1)] +
                            [Card("Boyfriend", i+1) for i in range(2)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_master_all_true(self):
        self.a._parse_code("MASTER Special")
        special = SpecialCard("Special", "Desc", None,
                              Application(alignment=Alignment.ALL,
                                          suits="Boyfriend"),
                              None)
        special.applied_to = [4, 3]
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [special] +
                            [Card("Boyfriend", i+1) for i in range(3)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_dunce_true(self):
        self.a._parse_code("DUNCE Special")
        special = SpecialCard("Special", "Desc", None,
                              Application(alignment=Alignment.FRIENDLY,
                                          suits=["Boyfriend"]),
                              None)
        special.applied_to = [0, 0]
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [special] +
                            [Card("Girlfriend", i+1) for i in range(3)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_dunce_false(self):
        self.a._parse_code("DUNCE Special")
        special = SpecialCard("Special", "Desc", None,
                              Application(alignment=Alignment.FRIENDLY,
                                          suits=["Boyfriend"]),
                              None)
        special.applied_to = [0, 1]
        self.board.board = [[Card("Girlfriend", i+1) for i in range(4)],
                            [special, Card("Boyfriend", 5)] +
                            [Card("Girlfriend", i+1) for i in range(2)]]
        self.assertFalse(self.a.check_round(self.board, 1))

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

    def test_by_value(self):
        self.a._parse_code("Use == 5")
        self.board.board = [[Card("Boyfriend", i+2) for i in range(4)],
                            [Card("Boyfriend", i+1) for i in range(4)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_by_value_true(self):
        self.a._parse_code("Use == 5")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+2) for i in range(4)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_check_match_win_false(self):
        self.a._parse_code("Match Win")
        self.board.board = [[Card("Boyfriend", 4), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)],
                            [Card("Boyfriend", 5), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 6)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_check_match_win_true(self):
        self.a._parse_code("Match Win")
        self.board.board = [[Card("Boyfriend", 4), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)],
                            [Card("Boyfriend", 5), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_check_match_lose_false(self):
        self.a._parse_code("Match Lose")
        self.board.board = [[Card("Boyfriend", 4), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)],
                            [Card("Boyfriend", 5), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 6)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_check_match_lose_true(self):
        self.a._parse_code("Match Lose")
        self.board.board = [[Card("Boyfriend", 4), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)],
                            [Card("Boyfriend", 4), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 6)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_check_match_tie_false(self):
        self.a._parse_code("Match Draw")
        self.board.board = [[Card("Boyfriend", 4), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)],
                            [Card("Boyfriend", 5), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 8)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_check_match_tie_true(self):
        self.a._parse_code("Match Draw")
        self.board.board = [[Card("Boyfriend", 4), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)],
                            [Card("Boyfriend", 5), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_check_match_count_less(self):
        self.a._parse_code("Match Win 3")
        self.board.board = [[Card("Boyfriend", 4), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)],
                            [Card("Boyfriend", 5), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 8)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_check_match_count_equal(self):
        self.a._parse_code("Match Win 3")
        self.board.board = [[Card("Boyfriend", 4), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)],
                            [Card("Boyfriend", 5), Card("Boyfriend", 5),
                             Card("Boyfriend", 7), Card("Boyfriend", 8)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_check_match_count_more(self):
        self.a._parse_code("Match Win 3")
        self.board.board = [[Card("Boyfriend", 4), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)],
                            [Card("Boyfriend", 5), Card("Boyfriend", 6),
                             Card("Boyfriend", 7), Card("Boyfriend", 8)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_check_match_enemy_false(self):
        self.a._parse_code("Match Enemy Win 1")
        self.board.board = [[Card("Boyfriend", 4), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)],
                            [Card("Boyfriend", 5), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_check_match_enemy_true(self):
        self.a._parse_code("Match Enemy Win 1")
        self.board.board = [[Card("Boyfriend", 4), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 7)],
                            [Card("Boyfriend", 5), Card("Boyfriend", 5),
                             Card("Boyfriend", 6), Card("Boyfriend", 6)]]
        self.assertTrue(self.a.check_round(self.board, 1))

    def test_multi_none(self):
        self.a._parse_code("Use == 5")
        self.a._parse_code("Use == 6")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+1) for i in range(4)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_multi_first(self):
        self.a._parse_code("Use == 5")
        self.a._parse_code("Use == 6")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+2) for i in range(4)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_multi_second(self):
        self.a._parse_code("Use == 5")
        self.a._parse_code("Use == 6")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+6) for i in range(4)]]
        self.assertFalse(self.a.check_round(self.board, 1))

    def test_multi_both(self):
        self.a._parse_code("Use == 5")
        self.a._parse_code("Use == 6")
        self.board.board = [[Card("Boyfriend", i+1) for i in range(4)],
                            [Card("Boyfriend", i+5) for i in range(4)]]
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
                         "Achievement('RendezVous Beginner', 'Play a game of RendezVous with Standard.', 'Reinforcements')")
        self.assertEqual(len(self.a.available), 29)
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
        self.a.achieve("RendezVous Student")
        self.assertTrue(self.a.unlocked("Invalid SpecialCard"))


class TestPerfectGame(unittest.TestCase):
    
    def setUp(self):
        """Load the default Achievements for testing."""
        self.a = AchievementList("test_unlock.test")
        self.s = Scoreboard(DummyDeckDefinition())
        self.backup = GameSettings.NUM_ROUNDS

    def tearDown(self):
        GameSettings.NUM_ROUNDS = self.backup

    def test_perfect_game_false(self):
        """Verify that Perfect Game is not awarded prematurely."""
        GameSettings.NUM_ROUNDS = 20
        self.s.scores = [[300, 100], [100, 300]]
        self.assertEqual(self.a._check_perfect_game(1, self.s), [])
        
    def test_perfect_game_short(self):
        """Verify that Perfect Game is not awarded for a short game."""
        GameSettings.NUM_ROUNDS = 10
        self.s.scores = [[-10, -10], [20, 20]]
        self.assertEqual(self.a._check_perfect_game(1, self.s), [])
        
    def test_perfect_game_tie(self):
        """Verify that Perfect Game doesn't count a perfect tie."""
        GameSettings.NUM_ROUNDS = 20
        self.s.scores = [[0, 0], [0, 0]]
        self.assertEqual(self.a._check_perfect_game(1, self.s), [])
        
    def test_perfect_game_true(self):
        """Verify that Perfect Game is awarded when earned."""
        GameSettings.NUM_ROUNDS = 20
        self.s.scores = [[-10, -10], [20, 20]]
        self.assertNotEqual(self.a._check_perfect_game(1, self.s), [])
        
    def test_perfect_game_with_tie(self):
        """Verify that a tied suit doesn't preclude Perfect Game."""
        GameSettings.NUM_ROUNDS = 20
        self.s.scores = [[0, -10], [0, 20]]
        self.assertNotEqual(self.a._check_perfect_game(1, self.s), [])


if __name__ == "__main__":
    unittest.main()
