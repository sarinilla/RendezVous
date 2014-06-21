from kivy.app import App
from kivy.properties import ObjectProperty, ListProperty, NumericProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.progressbar import ProgressBar
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label

from rendezvous import GameSettings
from rendezvous.deck import Card
from rendezvous.achievements import Achievement

from gui import PLAYER, DEALER
from gui.components import BoardDisplay, ScoreDisplay, HandDisplay
from gui.components import RoundCounter, ToolTipDisplay
from gui.components import SuitDisplay, SuitScoreDisplay


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


## Win/Lose Screen ##

class AchievementEarnedDisplay(BoxLayout):

    """Show an Achievement earned this game."""

    achievement = ObjectProperty(Achievement(' '))


class UnlockDisplay(BoxLayout):

    """Show an Achievement with an unlocked SpecialCard."""
    
    DUMMY_CARD = Card(" ", 0)
    DUMMY_CARD.name = " "
    DUMMY_CARD.description = " "

    achievement = ObjectProperty(Achievement(' '))
    reward = ObjectProperty(DUMMY_CARD, allownone=True)


class ScoreSurround(BoxLayout):

    center_widget = ObjectProperty()
    scores = ListProperty()

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, orientation="vertical", **kwargs)
        self.add_widget(Label(text=str(self.scores[0])))
        self.add_widget(self.center_widget)
        self.add_widget(Label(text=str(self.scores[1])))


class DealerDisplay(Widget):

    """Display one dealer image."""

    player = NumericProperty()
    score = ObjectProperty()

    def get_dealer(self):
        """Return the suit and win/loss for the dealer image to show."""
        won = len(self.score.wins(self.player)) - len(self.score.wins(self.player-1))
        if won != 0: won = int(won / abs(won))
        suit = self.score.best_suit(self.player) if won else self.score.best_suit(self.player-1)
        return (suit, -won)


class FinalScoreDisplay(BoxLayout):

    """Display the winner/loser announcement and suit wins."""

    score = ObjectProperty()

    def __init__(self, **kwargs):
        """Add suit win details below the total score display (kvlang)."""
        BoxLayout.__init__(self, orientation="vertical", **kwargs)
        announce = BoxLayout()
        announce.add_widget(DealerDisplay(player=PLAYER, score=self.score))
        announce.add_widget(Label(text=self.get_win_text()))
        announce.add_widget(DealerDisplay(player=DEALER, score=self.score))
        self.add_widget(announce)
        pwins = self.score.wins(PLAYER)
        dwins = self.score.wins(DEALER)
        wins = BoxLayout()
        for suit in pwins:
            wins.add_widget(ScoreSurround(scores=self.score.by_suit(suit),
                                          center_widget=SuitDisplay(suit=suit)))
        main_bar = ProgressBar(max=len(pwins + dwins), value=len(pwins))
        wins.add_widget(ScoreSurround(scores=(self.score.total(PLAYER),
                                              self.score.total(DEALER)),
                                      center_widget=main_bar,
                                      size_hint=(7, 1)))
        for suit in dwins:
            wins.add_widget(ScoreSurround(scores=self.score.by_suit(suit),
                                          center_widget=SuitDisplay(suit=suit)))
        self.add_widget(wins)
        
    def get_win_text(self):
        """Return the win/lose/draw text to display."""
        pscore = len(self.score.wins(PLAYER))
        dscore = len(self.score.wins(DEALER))
        if pscore > dscore:
            return "YOU WIN!" 
        elif pscore == dscore:
            return "It's a draw!"
        else:
            return "Dealer won."


class WinnerScreen(Screen):

    """Displays the winner/loser announcement [and an unlock]."""

    def __init__(self, score, achieved=None, **kwargs):
        Screen.__init__(self, **kwargs)
    
        self.ids.carousel.add_widget(FinalScoreDisplay(score=score))
        deck = App.get_running_app().loaded_deck
        for achievement in achieved:
            if achievement.reward is None:
                ach = AchievementEarnedDisplay(achievement=achievement)
                self.ids.carousel.add_widget(ach)
                continue
            unlock = UnlockDisplay(achievement=achievement,
                                   reward=deck.get_special(achievement.reward))
            self.ids.carousel.add_widget(unlock)
        if achieved:
            self.ids.carousel.index = 1
