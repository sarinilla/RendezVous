from kivy.app import App
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.actionbar import ActionBar
from kivy.uix.popup import Popup
from kivy.uix.carousel import Carousel
from kivy.uix.gridlayout import GridLayout

from gui.screens.powerups import CardSelect

from rendezvous.deck import Card


class CardDetail(Popup):

    """Show a card and its details vertically."""

    card = ObjectProperty()
    display = ObjectProperty()
    blocked = BooleanProperty()

    def __init__(self, **kwargs):
        super(CardDetail, self).__init__(**kwargs)
        self.blocked = str(self.card) in App.get_running_app().loaded_deck.blocked_cards

    def button_text(self, blocked):  # include for auto-binding
        if blocked:
            return "Replace"
        return "Remove"

    def get_backdrop(self, blocked):  # include for auto-binding
        if blocked:
            return (.5, .5, .5, 1)
        return (0, 0, 0, 1)

    def get_shading(self, blocked):  # include for auto-binding
        if blocked:
            return (.5, .5, .5, 1)
        return (1, 1, 1, 1)

    def clicked(self):
        deck = App.get_running_app().loaded_deck
        if self.blocked:
            deck.blocked_cards.remove(str(self.card))
            self.display.color = (1, 1, 1, 1)
        else:
            deck.blocked_cards.append(str(self.card))
            self.display.color = (.5, 0, 0, 1)
        self.blocked = not self.blocked
        self.dismiss()


class DeckEditScreen(Screen):

    """Provide a means of exploring and deactivating cards in a deck."""

    definition = ObjectProperty()

    LOCKED_CARD = Card(" ", 0)
    LOCKED_CARD.name = "HIDDEN"
    LOCKED_CARD.description = "Complete achievements to unlock additional cards."

    # Must add ActionBar from Python each time or its size is inconsistent
    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        main = BoxLayout(orientation="vertical")
        main.add_widget(ActionBar(size_hint=(1, .125)))
        carousel = Carousel(direction='right')
        layout = GridLayout(rows=2)
        i, c = 0, 0
        for card in self.definition.cards(App.get_running_app().achievements,
                                          use_blocks=False):
            color = (1, 1, 1, 1)
            if str(card) in self.definition.blocked_cards:
                color = (.5, 0, 0, 1)
            layout.add_widget(CardSelect(card=card,
                                         color=color,
                                         callback=self._card_detail,
                                         args=(card,)))
            i += 1
            c += 1
            if i == 10:
                carousel.add_widget(layout)
                layout = GridLayout(rows=2)
                i = 0
        if c < 50 + len(self.definition.specials):
            layout.add_widget(CardSelect(card=self.LOCKED_CARD))
        carousel.add_widget(layout)
        main.add_widget(carousel)
        self.add_widget(main)

    def _card_detail(self, display, card):
        CardDetail(card=card, display=display).open()        
