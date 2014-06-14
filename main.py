import os

from kivy.app import App
from kivy.core.image import Image
from kivy.graphics.texture import Texture
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.loader import Loader

from rendezvous.deck import DeckDefinition, Card
from rendezvous.gameplay import RendezVousGame
from rendezvous.statistics import Statistics
from rendezvous.achievements import AchievementList

from gui import DEALER, PLAYER
from gui.screens.game import GameScreen, WinnerScreen


__version__ = '0.3.6'


class RendezVousWidget(ScreenManager):

    """Arrange the screen - hand at the bottom, gameboard, score, etc.

    Attributes:
      game        -- behind-the-scenes RendezVousGame
      achieved    -- Achievements earned during the game
      dealer_play -- cards picked out for the dealer
      main        -- primary screen for gameplay

    """

    def __init__(self, **kwargs):
        """Arrange the widgets."""
        ScreenManager.__init__(self, transition=FadeTransition(), **kwargs)
        app = App.get_running_app()

        # Prepare internal storage
        self.game = RendezVousGame(deck=app.loaded_deck,
                                   achievements=app.achievements)
        self.game.new_game()
        self._cards_played = []  # hand indices played so far
        self.achieved = []
        self.dealer_play = None

        # Prepare the screens
        self.main = GameScreen(game=self.game, name='main')
        self.add_widget(self.main)

        # Prepare the tutorial (if needed)
        if app.achievements.achieved == []:
            self.switch_to(HandIntroTutorial(game=self.game,
                                             name='tutorial-hand'))
            

    def card_touched(self, card_display):
        """Handle a touch to a displayed card."""
        if card_display.card is None: return
        if self.dealer_play is None:
            self.dealer_play = self.game.players[DEALER].AI_hard(
                                    DEALER, self.game.board, self.game.score)
        if self.game.board.is_full(PLAYER): return  # not during scoring!
        
        loc = card_display.parent
        if loc is self.main.hand_display:
            card = self.main.hand_display.get(card_display)
            self.main.gameboard.place_card(card)
            if self.game.board.is_full(PLAYER):
                failures = self.main.gameboard.validate()
                for card in failures:
                    self.main.hand_display.return_card(card)
                if failures == []:
                    self.main.hand_display.confirm()
                    self._play_dealer()
                    
        elif loc.parent is self.main.gameboard:
            card = self.main.gameboard.remove_card(card_display)
            self.main.hand_display.return_card(card)

    def _play_dealer(self):
        """Place the dealer's selected cards on the board."""
        self.main.gameboard.play_dealer(self.dealer_play,
                                        callback=self._specials)
        for card in self.dealer_play:
            self.game.players[DEALER].remove(card)
        self.dealer_play = None

    def _specials(self):
        """Apply all specials."""
        self.main.gameboard.apply_specials(self.game, self.main.hand_display,
                                           self._score)

    def _score(self):
        """Score the round."""
        self.main.gameboard.score_round(self.main.scoreboard,
                                        callback=self._next_round)

    def _next_round(self):
        """Clear the board for the next round."""
        game_over = self.game.next_round()
        if game_over:
            self.achieved += App.get_running_app().record_score(self.game.score)
            self._winner = WinnerScreen(self.game.score, self.achieved,
                                        name='winner')
            self.switch_to(self._winner)
            return
        elif self.game.board.is_full(PLAYER):
            self.dealer_play = self.game.players[DEALER].AI_hard(
                                    DEALER, self.game.board, self.game.score)
            self._play_dealer()
        else:
            self.main.round_counter.round_number = self.game.round
            self.main.gameboard.highlight(None)
            self.main.gameboard.update()
            self.main.hand_display.update()

    def play_again(self):
        """Start a new game."""
        self.game.new_game()
        self.achieved = []
        self.main.gameboard.highlight(None)
        self.main.gameboard.update()
        self.main.hand_display.update()
        self.main.scoreboard.update()
        self.main.round_counter.round_number = 1
        self.current = 'main'
        self.remove_widget(self._winner)


class RendezVousApp(App):

    """Main RendezVous App, with deck loaded."""
    
    deck_texture = ObjectProperty()

    def _image_loaded(self, loader):
        """Update the deck image when it's finished loading."""
        if loader.image.texture:
            self.deck_texture = loader.image.texture

    def _achievements_loaded(self, loader):
        if loader.image.texture:
            self.achievement_texture = loader.image.texture

    def build(self):
        """Load the deck image and create the RendezVousWidget."""
        self.icon = os.path.join("data", "RVlogo.ico")
        user_dir = self.user_data_dir
        if not os.path.isdir(user_dir):
            user_dir = "player"
        self.statistics = Statistics(os.path.join(user_dir, "stats.txt"))
        self.achievements = AchievementList(os.path.join(user_dir, "unlocked.txt"))
        #self.achievement_texture = Image(self.achievements.image_file).texture
        loader = Loader.image(self.achievements.image_file)
        loader.bind(on_load=self._achievements_loaded)
        self.loaded_deck = DeckDefinition()
        loader = Loader.image(self.loaded_deck.img_file)
        loader.bind(on_load=self._image_loaded)
        self.deck_texture = Image(self.loaded_deck.img_file).texture
        return RendezVousWidget(app=self)
        
    def record_score(self, score):
        """Update meta-data at the end of each game."""
        self.statistics.record_game(score, PLAYER)
        return self.achievements.check(score, PLAYER, self.statistics)

    def get_texture(self, card):
        """Return the appropriate texture to display."""
        if card is None or card.name is " ":
            #return Texture.create()
            region = self.loaded_deck.get_back_texture()
        else:
            region = self.loaded_deck.get_card_texture(card)
        return self.deck_texture.get_region(*region)

    def get_suit_texture(self, suit):
        """Return the appropriate texture to display."""
        if suit:
            region = self.loaded_deck.get_suit_texture(suit)
            return self.deck_texture.get_region(*region)
        else:
            return Image(os.path.join("data", "RVlogo.png")).texture
            
    def get_achievement_texture(self, achievement):
        """Return the appropriate texture to display."""
        region = self.achievements.get_achievement_texture(achievement)
        return self.achievement_texture.get_region(*region)
        
    def on_pause(self):
        return True
    def on_resume(self):
        pass


if __name__ == '__main__':
    RendezVousApp().run()
