from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView

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


class PowerupIcon(Widget):

    """Display one Powerup's icon for use."""

    powerup = ObjectProperty()

    def on_touch_up(self, touch):
        """Use the powerup."""
        if not self.collide_point(*touch.pos): return
        App.get_running_app().root.use_powerup(self.powerup)


class PowerupTray(ModalView):

    """Displays Powerup icons for use during the game."""

    def __init__(self, **kwargs):
        ModalView.__init__(self, size_hint=(.15, 1), pos_hint={'right': 1},
                           **kwargs)
        app = App.get_running_app()
        layout = StackLayout(padding=[dp(10)])
        for powerup in app.powerups.purchased:
            layout.add_widget(PowerupIcon(powerup=powerup,
                                          size_hint=(1, None)))
        self.add_widget(layout)
            

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
        self.close_tray()

    def open_tray(self):
        self.powerup_tray = PowerupTray()
        self.powerup_tray.open()

    def close_tray(self):
        try:
            self.powerup_tray.dismiss()
        except: pass

    def on_touch_down(self, touch):
        if Screen.on_touch_down(self, touch):
            if 'card' in dir(touch) and touch.card is not None:
                return True
        if touch.sx > .75:
            touch.start = touch.sx, touch.sy
            touch.push(attrs=["start"])

    def on_touch_up(self, touch):
        if 'start' in dir(touch):
            move_x, move_y = touch.sx - touch.start[0], touch.sy - touch.start[1]
            if (move_x < 0 and move_y > -0.05 and move_y < 0.05):
                self.open_tray()
        else:
            Screen.on_touch_up(self, touch)
