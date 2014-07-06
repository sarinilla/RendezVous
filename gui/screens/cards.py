from kivy.app import App
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.actionbar import ActionBar

from rendezvous.deck import Card


class DeckCardDisplay(BoxLayout):

    """Show a card and its details vertically."""

    card = ObjectProperty()
    blocked = BooleanProperty()

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, **kwargs)
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
        else:
            deck.blocked_cards.append(str(self.card))
        self.blocked = not self.blocked


class DeckEditDisplay(ScrollView):

    """Display each (unlocked) card in the deck."""

    definition = ObjectProperty()

    LOCKED_CARD = Card(" ", 0)
    LOCKED_CARD.name = "HIDDEN"
    LOCKED_CARD.description = "Complete achievements to unlock additional cards."

    def __init__(self, **kwargs):
        ScrollView.__init__(self, **kwargs)
        count = 0
        for card in self.definition.cards(App.get_running_app().achievements,
                                          use_blocks=False):
            self.ids.layout.add_widget(DeckCardDisplay(card=card))
            count += 1
        if count - 10 * len(self.definition.suits) < len(self.definition.specials):
            self.ids.layout.add_widget(DeckCardDisplay(card=self.LOCKED_CARD))


class DeckEditScreen(Screen):

    """Provide a means of exploring and deactivating cards in a deck."""

    definition = ObjectProperty()

    # Must add ActionBar from Python each time or its size is inconsistent
    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        main = BoxLayout(orientation="vertical")
        main.add_widget(ActionBar(size_hint=(1, .125)))
        main.add_widget(DeckEditDisplay(definition=self.definition))
        self.add_widget(main)
