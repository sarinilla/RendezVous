from kivy.core.image import Image
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.actionbar import ActionBar
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.carousel import Carousel

from gui.components import ToolTipDisplay


class DeckDisplay(BoxLayout):

    """Display a single deck and allow purchase / selection."""

    deck = ObjectProperty()
    purchased = BooleanProperty()

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        if 'texture' not in dir(self.deck):
            self.deck.texture = Image(self.deck.icon).texture

    def get_shading(self, purchased):  # include purchased for auto-binding
        """Return the color to tint the entire display."""
        if self.purchased: return (1, 1, 1, 1)
        else: return (.5, .5, .5, 1)


class DeckCatalogScreen(Screen):

    """Provide a means of exploring and purchasing available decks."""

    catalog = ObjectProperty()

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.carousel = Carousel(direction="right")
        standard = self.catalog["Lovers & Spies Deck"]
        self.carousel.add_widget(DeckDisplay(deck=standard, purchased=True))
        for deck in self.catalog:
            if deck == standard: continue
            purchased = self.catalog.purchased(deck) is not None
            self.carousel.add_widget(DeckDisplay(deck=deck, purchased=purchased))
                                     
        main = BoxLayout(orientation="vertical")
        main.add_widget(ActionBar())
        main.add_widget(self.carousel)
        self.add_widget(main)
