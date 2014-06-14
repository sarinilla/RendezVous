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
from gui.components import BLANK, DARKEN
from gui.screens.game import GameScreen, WinnerScreen
from gui.screens.tutorial import HandIntro, BoardIntro, ScoreIntro
from gui.screens.tutorial import PostScoringIntro, TooltipIntro


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
            self.switch_to(HandIntro(game=self.game, name='tutorial-hand'))
            

    def card_touched(self, card_display):
        """Handle a touch to a displayed card."""
        if card_display.card is None: return
        if self.dealer_play is None:
            self.dealer_play = self.game.players[DEALER].AI_hard(
                                    DEALER, self.game.board, self.game.score)
        if self.game.board.is_full(PLAYER): return  # not during scoring!

        if self.current == 'tutorial-tooltip':
            for slot in self.current_screen.hand_display.slots:
                slot.highlight(BLANK)
        
        loc = card_display.parent
        if loc is self.current_screen.hand_display:
            board_shown = self.current not in ('tutorial-hand',
                                               'tutorial-tooltip')
            card = self.current_screen.hand_display.get(card_display)
            if board_shown:
                self.current_screen.gameboard.place_card(card)
            else:
                self.game.board.play_cards(PLAYER, [card])
            if self.game.board.is_full(PLAYER):
                if board_shown:
                    failures = self.current_screen.gameboard.validate()
                else:
                    failures = self.game.board.validate(self.game.board[PLAYER])
                    failures = [self.game.board[PLAYER][i] for i in failures]
                for card in failures:
                    self.current_screen.hand_display.return_card(card)
                if failures == []:
                    self.current_screen.hand_display.confirm()
                    self._play_dealer()
                    
        elif loc.parent is self.current_screen.gameboard:
            card = self.current_screen.gameboard.remove_card(card_display)
            self.current_screen.hand_display.return_card(card)

    def _play_dealer(self):
        """Place the dealer's selected cards on the board."""
        if self.current == 'tutorial-hand':
            self.switch_to(BoardIntro(game=self.game, name='tutorial-board'))
        elif self.current == 'tutorial-tooltip':
            self.current = 'main'
            self.current_screen.gameboard.update()
        self.current_screen.gameboard.play_dealer(self.dealer_play,
                                                  callback=self._specials)
        for card in self.dealer_play:
            self.game.players[DEALER].remove(card)
        self.dealer_play = None

    def _specials(self):
        """Apply all specials."""
        if self.current == 'tutorial-board':
            return  # until continue is pressed
        self.current_screen.gameboard.apply_specials(self.game,
                    self.current_screen.hand_display, self._score)

    def score_tutorial(self):
        """Continue with scoring from tutorial-board."""
        self.switch_to(ScoreIntro(game=self.game, name='tutorial-score'))
        self._score()

    def _score(self):
        """Score the round."""
        self.current_screen.gameboard.score_round(self.current_screen.scoreboard,
                                                  callback=self._next_round)

    def tutorial_scored(self):
        self.switch_to(PostScoringIntro(game=self.game,
                                        name='tutorial-continue'))
        self._next_round()

    def _next_round(self):
        """Clear the board for the next round."""
        if self.current == 'tutorial-score':
            return  # until continue is pressed
        app = App.get_running_app()
        game_over = self.game.next_round()
        if game_over:
            self.achieved += app.record_score(self.game.score)
            if self.current != 'main':
                self._winner = WinIntroScreen(game=self.game,
                                              name='winner')
                self._winner.index = 1
            else:
                self._winner = WinnerScreen(self.game.score, self.achieved,
                                            name='winner')
            self.switch_to(self._winner)
            return
        elif self.game.board.is_full(PLAYER):
            self.dealer_play = self.game.players[DEALER].AI_hard(
                                    DEALER, self.game.board, self.game.score)
            self._play_dealer()
            return

        if self.current == 'tutorial-continue' and self.game.round >= 10:
            special = app.loaded_deck.get_special('Perfume')
            self.game.players[PLAYER].cards[8] = special
            app.achievements.achieved.append("Tutorial")
            self.game.players[PLAYER].deck.shuffle()
            self.switch_to(TooltipIntro(game=self.game, name='tutorial-tooltip'))
            for slot in self.current_screen.hand_display.slots:
                slot.highlight(DARKEN)
            self.current_screen.hand_display.slots[8].highlight(BLANK)
        else:
            self.current_screen.gameboard.highlight(None)
            self.current_screen.gameboard.update()
        self.current_screen.round_counter.round_number = self.game.round
        self.current_screen.hand_display.update()

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
