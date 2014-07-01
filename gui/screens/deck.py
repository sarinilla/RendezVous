from kivy.app import App
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
        try:
            self._update_textures(kwargs['deck'])
        except KeyError:
            pass
        BoxLayout.__init__(self, **kwargs)

    def _update_textures(self, deck):
        if 'texture' not in dir(deck):
            deck.texture = Image(deck.icon).texture
        if 'hand_texture' not in dir(deck):
            deck.hand_texture = Image(deck.hand).texture
        
    def get_shading(self, purchased):  # include purchased for auto-binding
        """Return the color to tint the entire display."""
        if purchased: return (1, 1, 1, 1)
        else: return (.5, .5, .5, 1)

    def get_backdrop(self, purchased):  # include purchased for auto-binding
        """Return the color to tint the entire display."""
        if purchased: return (0, 0, 0, 1)
        else: return (.5, .5, .5, 1)

    def clicked(self):
        """Handle a purchase or deck selection."""
        app = App.get_running_app()
        if self.purchased:
            app.load_deck(self.deck.base_filename)
            app.root.switcher('home')
        else:
            app.purchase_deck(self.deck)


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

    def update(self):
        for slide in self.carousel.slides:
            if slide.deck.base_filename == "Standard":
                continue
            slide.purchased = self.catalog.purchased(slide.deck) is not None
