from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout

from rendezvous import GameSettings

from gui import PLAYER, DEALER
from gui.components import BoardDisplay, ScoreDisplay, HandDisplay
from gui.components import RoundCounter, ToolTipDisplay
from gui.components import AchievementEarnedDisplay, UnlockDisplay


class RoundAchievementScreen(Screen):

    """Displays unlocks between rounds."""

    def __init__(self, achieved, **kwargs):
        Screen.__init__(self, **kwargs)

        deck = App.get_running_app().loaded_deck
        for achievement in achieved:
            if achievement.reward is None:
                ach = AchievementEarnedDisplay(achievement=achievement)
                self.ids.carousel.add_widget(ach)
                continue
            unlock = UnlockDisplay(achievement=achievement,
                                   reward=deck.get_special(achievement.reward))
            self.ids.carousel.add_widget(unlock)
            

class GameScreen(Screen):
    
    """Displays the game in progress.

    Attributes:
      gameboard     -- displays the Gameboard
      round_counter -- displays the current round
      scoreboard    -- displays the Scoreboard
      hand_display  -- displays the player's Hand
      tooltip       -- displays the details on one card

    """

    game = ObjectProperty()

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)

        # Prepare the display areas
        self.gameboard = BoardDisplay(board=self.game.board,
                                      size_hint=(4, 1))
        self.round_counter = RoundCounter(round_number=self.game.round,
                                          max_round=GameSettings.NUM_ROUNDS,
                                          size_hint=(1, .075))
        self.scoreboard = ScoreDisplay(scoreboard=self.game.score,
                                       size_hint=(1, .4))
        self.tooltip = ToolTipDisplay(size_hint=(1, .5))
        self.hand_display = HandDisplay(hand=self.game.players[PLAYER],
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

    def update(self):
        self.gameboard.update()
        self.hand_display.update()
