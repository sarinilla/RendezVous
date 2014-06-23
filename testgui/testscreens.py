import unittest

from gui.screens.deck import *
from gui.screens.game import *


## Achievements ##

class TestAchievementDisplay(unittest.TestCase):

    def setUp(self):
        from gui.screens.achievements import AchievementDisplay
        self.ad = AchievementDisplay()

    def test_init(self):
        pass

    def test_get_shading(self):
        self.assertEqual(self.ad.get_shading(True), (1, 1, 1, 1))
        self.assertEqual(self.ad.get_shading(False), (.25, .25, .25, 1))

    def test_get_backdrop(self):
        self.assertEqual(self.ad.get_backdrop(True), (0, 0, 0, 1))
        self.assertEqual(self.ad.get_backdrop(False), (.25, .25, .25, 1))

    def test_get_card_no_reward(self):
        self.ad.achievement = Achievement("Name", "Desc")
        self.assertIs(self.ad.get_card(True), None)
        self.assertIs(self.ad.get_card(False), None)
        
    def test_get_card_reward(self):
        self.ad.achievement = Achievement("Name", "Desc", "Reward")
        self.assertIs(self.ad.get_card(True), "Reward")
        self.assertIs(self.ad.get_card(False), "HIDDEN")

        
## Deck ##

class TestDeckDisplay(unittest.TestCase):

    def setUp(self):
        from rendezvous.deck import DeckCatalogEntry
        self.deck = DeckCatalogEntry("Name", "Desc", "Directory", "Base")
        self.deck.texture = None  # prevent loading
        self.deck.hand_texture = None  # prevent loading
        self.dd = DeckDisplay(deck=self.deck, purchased=False)

    def test_init(self):
        pass

    def test_get_shading(self):
        self.assertEqual(self.dd.get_shading(True), (1, 1, 1, 1))
        self.assertEqual(self.dd.get_shading(False), (.5, .5, .5, 1))
        
    def test_get_backdrop(self):
        self.assertEqual(self.dd.get_backdrop(True), (0, 0, 0, 1))
        self.assertEqual(self.dd.get_backdrop(False), (.5, .5, .5, 1))

    def test_clicked(self):
        pass  # no App running


class TestDeckCatalogScreen(unittest.TestCase):

    def setUp(self):
        from rendezvous.deck import DeckCatalog
        self.catalog = DeckCatalog()
        self.dcs = DeckCatalogScreen(catalog=self.catalog)

    def test_init(self):
        self.assertEqual(len(self.dcs.carousel.slides), len(self.catalog))
        self.assertEqual(self.dcs.carousel.slides[0].deck.base_filename,
                         "Standard")


## Game ##

class TestGameScreen(unittest.TestCase):

    def setUp(self):
        from rendezvous.gameplay import RendezVousGame
        self.game = RendezVousGame()
        self.game.new_game()
        self.gs = GameScreen(game=self.game)

    def test_init(self):
        self.assertIs(self.gs.gameboard.board, self.game.board)
        self.assertIsInstance(self.gs.round_counter, RoundCounter)
        self.assertIs(self.gs.scoreboard.scoreboard, self.game.score)
        self.assertIsInstance(self.gs.tooltip, ToolTipDisplay)
        self.assertIs(self.gs.hand_display.hand, self.game.players[PLAYER])


class TestUnlockDisplay(unittest.TestCase):

    def setUp(self):
        self.ud = UnlockDisplay()

    def test_init(self):
        pass


@unittest.skip("can't load rendezvous.kv without an app?")
class TestWinnerScreen(unittest.TestCase):

    def setUp(self):
        from rendezvous.deck import DeckDefinition
        from rendezvous.gameplay import Scoreboard
        from kivy.lang import Builder
        Builder.load_file('rendezvous.kv')
        self.ws = WinnerScreen(score=Scoreboard(DeckDefinition()))

    def test_init(self):
        pass

    def test_achievements(self):
        from rendezvous.achievements import Achievement
        self.ws = WinnerScreen(score=Scoreboard(DeckDefinition()),
                               achieved=[Achievement("Name")])


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
        
