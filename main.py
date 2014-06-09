import os

from functools import partial
from kivy.clock import Clock
from kivy.app import App
from kivy.properties import ObjectProperty, ListProperty, StringProperty, NumericProperty
from kivy.core.image import Image
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.loader import Loader

from rendezvous import GameSettings, SpecialSuit, EffectType
from rendezvous.deck import DeckDefinition, Deck, Card
from rendezvous.gameplay import Hand, Gameboard, Scoreboard, RendezVousGame


__version__ = '0.1.1'


# Readability constants for the two players
DEALER = 0
PLAYER = 1

# Quick color constants
BLANK = [1, 1, 1, 1]
WHITE = [1, 1, 1, .5]
GREEN = [.25, 1, .25, .5]
RED = [1, .25, .25, .5]
BLUE = [.25, .25, 1, .5]


class CardDisplay(Widget):

    """Widget to show a single RendezVous card."""
    
    card = ObjectProperty(allownone=True)
    color = ListProperty(BLANK)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.card = self.card
            touch.push(attrs=["card"])

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            App.get_running_app().root.card_touched(self)

    def highlight(self, color):
        if color is None:
            self.color = BLANK
        else:
            self.color = color
        self.canvas.ask_update()


class HandDisplay(BoxLayout):

    """Display a hand of cards."""
    
    hand = ObjectProperty()
    slots = ListProperty()

    def __init__(self, **kwargs):
        """Set up the CardDisplays."""
        BoxLayout.__init__(self, **kwargs)
        for card in self.hand:
            display = CardDisplay(card=card)
            self.slots.append(display)
            self.add_widget(display)

    def update(self):
        for i, card in enumerate(self.hand):
            self.slots[i].card = card


class BoardDisplay(BoxLayout):

    """Show the 4x2 Gameboard."""
    
    board = ObjectProperty()
    slots = []

    def __init__(self, **kwargs):
        """Set up the CardDisplays."""
        BoxLayout.__init__(self, orientation="vertical", **kwargs)
        for i in range(len(self.board)):  # for card in board iterates all sides
            side = self.board[i]
            layout = BoxLayout()
            side_slots = []
            for card in self.board[i]:
                display = CardDisplay(card=card)
                side_slots.append(display)
                layout.add_widget(display)
            self.slots.append(side_slots)
            self.add_widget(layout)

    def update(self):
        """Update the visual display."""
        for i in range(len(self.board)):
            for j, card in enumerate(self.board[i]):
                self.slots[i][j].card = None # force update
                self.slots[i][j].card = card
                self.slots[i][j].canvas.ask_update()

    def highlight(self, color):
        """Update all highlight colors at once."""
        for side in self.slots:
            for display in side:
                display.highlight(color)


class SuitDisplay(BoxLayout):

    """Display the 2-player score in one suit."""

    suit = StringProperty()
    pscore = NumericProperty()
    dscore = NumericProperty()


class ScoreDisplay(BoxLayout):

    """Show the score for each suit."""

    scoreboard = ObjectProperty()
    rows = []

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, orientation="vertical", **kwargs)
        for i, suit in enumerate(self.scoreboard.suits):
            display = SuitDisplay(suit=suit,
                                  pscore=self.scoreboard[PLAYER][i],
                                  dscore=self.scoreboard[DEALER][i])
            self.rows.append(display)
            self.add_widget(display)

    def update(self):
        """Update the display scales."""
        for i, display in enumerate(self.rows):
            display.pscore = self.scoreboard[PLAYER][i]
            display.dscore = self.scoreboard[DEALER][i]


class ToolTipDisplay(BoxLayout):

    """Display the details of a card."""

    DUMMY_CARD = Card(" ", 0)
    DUMMY_CARD.name = " "
    DUMMY_CARD.description = "Drag a card here for more information."

    card = ObjectProperty(DUMMY_CARD)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            if 'card' in dir(touch):
                touch.pop()
                if touch.card is not None:
                    self.card = touch.card


class RoundCounter(Label):

    """Display the round number."""

    round_number = NumericProperty()
    max_round = NumericProperty()


class GameScreen(Screen):
    
    """Displays the game in progress."""

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)

        # Prepare the display areas
        game = kwargs["game"]
        self.gameboard = BoardDisplay(board=game.board,
                                      size_hint=(4, 1))
        self.round_counter = RoundCounter(round_number=1,
                                          max_round=GameSettings.NUM_ROUNDS,
                                          size_hint=(1, .1))
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


class WinnerScreen(Screen):

    """Displays the winner/loser announcement."""

    def __init__(self, game, **kwargs):
        Screen.__init__(self, **kwargs)
        winner = game.score.total(PLAYER) >= game.score.total(DEALER)

        main = BoxLayout(orientation="vertical")
        text = Label()
        text.text = "YOU WIN!" if winner else "Dealer won."
        main.add_widget(text)
        main.add_widget(SuitDisplay(pscore=game.score.total(PLAYER),
                                    dscore=game.score.total(DEALER)))
        main.add_widget(Label(text="Play Again?"))
        buttons = BoxLayout()
        play_again = Button(text='YES')
        play_again.bind(on_press=self.replay)
        buttons.add_widget(play_again)
        end = Button(text="no")
        end.bind(on_press=App.get_running_app().stop)
        buttons.add_widget(end)
        main.add_widget(buttons)
        self.add_widget(main)

    def replay(self, *args):
        """Convenience function to play again."""
        self.manager.play_again()


class RendezVousWidget(ScreenManager):

    """Arrange the screen - hand at the bottom, gameboard, score, etc."""

    def __init__(self, **kwargs):
        """Arrange the widgets."""
        ScreenManager.__init__(self, transition=FadeTransition(), **kwargs)
        app = kwargs["app"]

        # Prepare internal storage
        self.game = RendezVousGame(deck=app.loaded_deck)
        self.game.new_game()
        self._cards_played = []

        # Prepare the screens
        self.main = GameScreen(game=self.game, name='main')
        self.add_widget(self.main)

    def card_touched(self, card_display):
        """Handle a touch to a displayed card."""
        if card_display.card is None:
            return
        loc = card_display.parent
        if loc is self.main.hand_display:
            self._place_on_board(card_display)
            if self.game.board.is_full(PLAYER):
                if not self._validate():
                    return
                self._complete_play()
                    
        elif loc.parent is self.main.gameboard:
            self._return_to_hand(card_display)

    def _return_to_hand(self, card_display):
        """Return a touched board card to the hand."""
        try:
            iboard = self.game.board[PLAYER].index(card_display.card)
            ihand = self.game.players[PLAYER].index(card_display.card)
        except ValueError:
            return
        self._cards_played.remove(ihand)
        self.game.board[PLAYER][iboard] = None
        self.main.hand_display.slots[ihand].card = card_display.card
        card_display.card = None

    def _place_on_board(self, card_display):
        """Place the touched hand card onto the board."""
        iboard = self.game.board.play_cards(PLAYER, [card_display.card])[0]
        ihand = self.game.players[PLAYER].index(card_display.card)
        self._cards_played.append(ihand)
        self.main.gameboard.slots[PLAYER][iboard].card = card_display.card
        card_display.card = None

    def _validate(self):
        """Return True if requirements met; else return to hand and False."""
        failures = self.game.validate(PLAYER)
        if not failures:
            return True
        for iboard in failures:
            self._return_to_hand(self.main.gameboard.slots[PLAYER][iboard])
        return False

    def _complete_play(self):
        """Finalize the move and let the dealer play."""
        for ihand in reversed(sorted(self._cards_played)):
            self.game.players[PLAYER].pop(ihand)
        self._cards_played = []
        dplay = self.game.players[DEALER].AI_play(DEALER,
                                                  self.game.board,
                                                  self.game.score)
        self.game.board.play_cards(DEALER, dplay)
        for card in dplay:
            self.game.players[DEALER].remove(card)
        self.main.gameboard.update()
        Clock.schedule_once(self._apply_specials, 0.5)

    def _apply_specials(self, dt, i=None, p=None):
        """Apply specials one-by-one with highlighting."""

        def increment(i, p):
            p += 1
            if p >= len(self.game.board):
                p = 0
                i += 1
                if i >= len(self.game.board[0]):
                    Clock.schedule_once(self._score_round)
                    return None, None
            return i, p

        if i is None:
            i, p = 0, 0
        else:
            self.main.gameboard.slots[p][i].highlight(None)
            i, p = increment(i, p)
            if i is None: return
            
        while self.game.board[p][i].suit != SpecialSuit.SPECIAL:
            i, p = increment(i, p)
            if i is None: return

        self.main.gameboard.slots[p][i].highlight(BLUE)
        self.game._apply(p, i)
        self.main.gameboard.update()
        if self.main.gameboard.slots[p][i].card.effect.effect == EffectType.FLUSH:
            self.main.hand_display.update()
        Clock.schedule_once(partial(self._apply_specials, i=i, p=p), 1.0)


    def _score_round(self, dt):
        """Score the round."""
        for i in range(len(self.game.board[0])):
            for p in range(len(self.game.board)):
                result = self.game.score._score_match(p, self.game.board[p][i],
                                                p-1, self.game.board[p-1][i])
                color = [WHITE, GREEN, RED][result]
                self.main.gameboard.slots[p][i].highlight(color)
        self.main.scoreboard.update()
        Clock.schedule_once(self._next_round, 3.0)

    def _next_round(self, dt):
        """Clear the board for the next round."""
        game_over = self.game.next_round()
        if game_over:
            self._winner = WinnerScreen(self.game, name='winner')
            self.switch_to(self._winner)
            return
        self.main.round_counter.round_number = self.game.round
        for side in self.main.gameboard.slots:
            for slot in side:
                slot.highlight(None)
        self.main.gameboard.update()
        self.main.hand_display.update()

    def play_again(self):
        self.game.new_game()
        self.main.gameboard.highlight(None)
        self.main.gameboard.update()
        self.main.hand_display.update()
        self.main.scoreboard.update()
        self.main.round_counter.round = 1
        self.current = 'main'
        self.remove_widget(self._winner)


class RendezVousApp(App):

    """Main RendezVous App, with deck loaded."""
    
    deck_texture = ObjectProperty()

    def _image_loaded(self, loader):
        """Update the deck image when it's finished loading."""
        if loader.image.texture:
            self.deck_texture = loader.image.texture

    def build(self):
        """Load the deck image and create the RendezVousWidget."""
        self.icon = os.path.join("data", "RVlogo.ico")
        self.loaded_deck = DeckDefinition()
        loader = Loader.image(self.loaded_deck.img_file)
        loader.bind(on_load=self._image_loaded)
        self.deck_texture = Image(self.loaded_deck.img_file).texture
        return RendezVousWidget(app=self)

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
            return Image(self.icon).texture


if __name__ == '__main__':
    RendezVousApp().run()
