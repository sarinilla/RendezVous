from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout

from rendezvous import GameSettings
from rendezvous.deck import Card
from rendezvous.achievements import Achievement

from gui import PLAYER
from gui.components import BoardDisplay, ScoreDisplay, HandDisplay
from gui.components import RoundCounter, ToolTipDisplay
from gui.screens import FinalScoreDisplay


## Classic Game Screen ##

class GameScreen(Screen):
    
    """Displays the game in progress.

    Attributes:
      gameboard     -- displays the Gameboard
      round_counter -- displays the current round
      scoreboard    -- displays the Scoreboard
      hand_display  -- displays the player's Hand
      tooltip       -- displays the details on one card

    """

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)

        # Prepare the display areas
        game = kwargs["game"]
        self.gameboard = BoardDisplay(board=game.board,
                                      size_hint=(4, 1))
        self.round_counter = RoundCounter(round_number=1,
                                          max_round=GameSettings.NUM_ROUNDS,
                                          size_hint=(1, .075))
        self.scoreboard = ScoreDisplay(scoreboard=game.score,
                                       size_hint=(1, .4))
        self.tooltip = ToolTipDisplay(size_hint=(1, .5))
        self.hand_display = HandDisplay(hand=game.players[PLAYER],
                                        size_hint=(1, .3))

        # Lay out the display
        main = BoxLayout(orientation="vertical")
        layout = BoxLayout()
        layout.add_widget(self.gameboard)
        sidebar = BoxLayout(orientation="vertical")
        sidebar.add_widget(self.round_counter)
        sidebar.add_widget(self.scoreboard)
        sidebar.add_widget(self.tooltip)
        layout.add_widget(sidebar)
        main.add_widget(layout)
        main.add_widget(self.hand_display)
        self.add_widget(main)


## Win/Lose Screen ##

class AchievementDisplay(BoxLayout):

    """Show an Achievement earned this game."""

    achievement = ObjectProperty(Achievement(' '))


class UnlockDisplay(BoxLayout):

    """Show an Achievement with an unlocked SpecialCard."""
    
    DUMMY_CARD = Card(" ", 0)
    DUMMY_CARD.name = " "
    DUMMY_CARD.description = " "

    achievement = ObjectProperty(Achievement(' '))
    reward = ObjectProperty(DUMMY_CARD, allownone=True)


class WinnerScreen(Screen):

    """Displays the winner/loser announcement [and an unlock]."""

    def __init__(self, score, achieved=None, **kwargs):
        Screen.__init__(self, **kwargs)
    
        self.ids.carousel.add_widget(FinalScoreDisplay(score=score))
        deck = App.get_running_app().loaded_deck
        for achievement in achieved:
            if achievement.reward is None:
                ach = AchievementDisplay(achievement=achievement)
                self.ids.carousel.add_widget(ach)
                continue
            unlock = UnlockDisplay(achievement=achievement,
                                   reward=deck.get_special(achievement.reward))
            self.ids.carousel.add_widget(unlock)
        if achieved:
            self.ids.carousel.index = 1
