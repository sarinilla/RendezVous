import unittest


from gui.screens import FinalScoreDisplay
from gui.screens.game import *


class TestFinalScoreDisplay(unittest.TestCase):

    def setUp(self):
        from rendezvous.deck import DeckDefinition
        from rendezvous.gameplay import Scoreboard
        self.score = Scoreboard(DeckDefinition())
        self.sd = FinalScoreDisplay(score=self.score)

    def test_init(self):
        pass

    def test_text_win(self):
        self.score[0][0] = -20
        self.assertEqual(self.sd.get_win_text(), "YOU WIN!")

    def test_text_lose(self):
        self.score[0][0] = 20
        self.assertEqual(self.sd.get_win_text(), "Dealer won.")

    def test_text_draw(self):
        self.assertEqual(self.sd.get_win_text(), "It's a draw!")


## Game ##

class TestGameScreen(unittest.TestCase):

    def setUp(self):
        from rendezvous.gameplay import RendezVousGame
        self.game = RendezVousGame()
        self.gs = GameScreen(game=self.game)

    def test_init(self):
        self.assertIs(self.gs.gameboard.board, self.game.board)
        self.assertIsInstance(self.gs.round_counter, RoundCounter)
        self.assertIs(self.gs.scoreboard.scoreboard, self.game.score)
        self.assertIsInstance(self.gs.tooltip, ToolTipDisplay)
        self.assertIs(self.gs.hand_display.hand, self.game.players[PLAYER])


class TestAchievementDisplay(unittest.TestCase):

    def setUp(self):
        self.ad = AchievementDisplay()

    def test_init(self):
        pass


class TestUnlockDisplay(unittest.TestCase):

    def setUp(self):
        self.ud = UnlockDisplay()

    def test_init(self):
        pass


class TestWinnerScreen(unittest.TestCase):

    def setUp(self):
        from rendezvous.deck import DeckDefinition
        from rendezvous.gameplay import Scoreboard
        self.ws = WinnerScreen(score=Scoreboard(DeckDefinition()))

    def test_init(self):
        pass

    def test_achievements(self):
        from rendezvous.achievements import Achievement
        self.ws = WinnerScreen(score=Scoreboard(DeckDefinition()),
                               achieved=[Achievement("Name")])
        
