from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty, ListProperty, NumericProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.progressbar import ProgressBar
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label

from gui import PLAYER, DEALER
from gui.components import SuitDisplay, SuitScoreDisplay
from gui.components import AchievementEarnedDisplay, UnlockDisplay
from gui.screens.statistics import StatisticsDisplay


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
        winner = len(pwins) > len(dwins)
        wins = BoxLayout()
        for i, suit in enumerate(pwins):
            display = SuitDisplay(suit=suit)
            Clock.schedule_once(display.flash, 2.0 + 0.45 * (i+1))
            if winner:
                Clock.schedule_once(display.flash,
                                    2.5 + 0.45 * (len(pwins)+1))
            wins.add_widget(ScoreSurround(scores=self.score.by_suit(suit),
                                          center_widget=display))
        main_bar = ProgressBar(max=len(pwins + dwins), value=len(pwins))
        wins.add_widget(ScoreSurround(scores=(self.score.total(DEALER),
                                              self.score.total(PLAYER)),
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
    
        stat = App.get_running_app().statistics
        deck = App.get_running_app().loaded_deck
        self.ids.carousel.add_widget(StatisticsDisplay(statistics=stat,
                                                       deck=deck))
        self.ids.carousel.add_widget(FinalScoreDisplay(score=score))
        for achievement in achieved:
            if achievement.reward is None:
                ach = AchievementEarnedDisplay(achievement=achievement)
                self.ids.carousel.add_widget(ach)
                continue
            unlock = UnlockDisplay(achievement=achievement,
                                   reward=deck.get_special(achievement.reward))
            self.ids.carousel.add_widget(unlock)
        self.ids.carousel.index = 1
        if achieved:
            Clock.schedule_once(lambda dt: self._advance(), 0.5)

    def _advance(self):
        self.ids.carousel.index = 2
