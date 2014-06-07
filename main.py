from kivy.app import App
from kivy.properties import ObjectProperty, ListProperty, StringProperty, NumericProperty
from kivy.core.image import Image
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.loader import Loader

from rendezvous.deck import DeckDefinition, Deck, Card
from rendezvous.gameplay import Hand, Gameboard, Scoreboard


class CardDisplay(Widget):

    """Widget to show a single RendezVous card."""
    
    card = ObjectProperty(allownone=True)


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
            
        self.slots[3].card = None


class BoardDisplay(BoxLayout):

    """Show the 4x2 Gameboard."""
    
    board = ObjectProperty()
    slots = ListProperty()

    def __init__(self, **kwargs):
        """Set up the CardDisplays."""
        BoxLayout.__init__(self, orientation="vertical", **kwargs)
        for i in range(len(self.board)):  # for card in board iterates all sides
            side = self.board[i]
            layout = BoxLayout()
            for card in self.board[i]:
                display = CardDisplay(card=card)
                self.slots.append(display)
                layout.add_widget(display)
            self.add_widget(layout)
            
        self.slots[2].card = Card("Boyfriend", 1)
        self.slots[3].card = Card("Spy", 2)
        self.slots[4].card = Card("Girlfriend", 1)


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
                                  pscore=self.scoreboard[1][i],
                                  dscore=self.scoreboard[0][i])
            self.rows.append(display)
            self.add_widget(display)

        self.rows[0].pscore=20
        self.rows[1].dscore=20
        self.rows[2].pscore=-10
        self.rows[3].pscore=20
        self.rows[3].dscore=20
        self.rows[4].dscore=-10


class RendezVousWidget(BoxLayout):

    """Arrange the screen - hand at the bottom, gameboard, score, etc."""

    def __init__(self, **kwargs):
        """Arrange the widgets."""
        BoxLayout.__init__(self, orientation="vertical", **kwargs)
        app = kwargs["app"]
        layout = BoxLayout()
        layout.add_widget(BoardDisplay(board=Gameboard(),
                                       size_hint=(4, 1)))
        layout.add_widget(ScoreDisplay(scoreboard=Scoreboard(app.loaded_deck),
                                       size_hint=(1, 1)))
        self.add_widget(layout)
        self.add_widget(HandDisplay(hand=Hand(Deck(app.loaded_deck)),
                                    size_hint=(1, .5)))


class RendezVousApp(App):

    """Main RendezVous App, with deck loaded."""
    
    deck_texture = ObjectProperty()

    def _image_loaded(self, loader):
        if loader.image.texture:
            self.deck_texture = loader.image.texture

    def build(self):
        """Load the deck image and create the RendezVousWidget."""
        self.loaded_deck = DeckDefinition()
        loader = Loader.image(self.loaded_deck.img_file)
        loader.bind(on_load=self._image_loaded)
        self.deck_texture = Image(self.loaded_deck.img_file).texture
        return RendezVousWidget(app=self)

    def get_texture(self, card):
        """Return the appropriate texture to display."""
        if card is None:
            return Texture.create()
        region = self.loaded_deck.get_card_texture(card)
        return self.deck_texture.get_region(*region)

    def get_suit_texture(self, suit):
        """Return the appropriate texture to display."""
        region = self.loaded_deck.get_suit_texture(suit)
        return self.deck_texture.get_region(*region)


if __name__ == '__main__':
    RendezVousApp().run()
