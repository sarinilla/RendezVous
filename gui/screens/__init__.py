from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty

from gui import PLAYER, DEALER


class FinalScoreDisplay(BoxLayout):

    """Display the winner/loser announcement and final score."""

    score = ObjectProperty()

    def get_win_text(self):
        pscore = self.score.total(PLAYER)
        dscore = self.score.total(DEALER)
        if pscore > dscore:
            return "YOU WIN!" 
        elif pscore == dscore:
            return "It's a draw!"
        else:
            return "Dealer won."
