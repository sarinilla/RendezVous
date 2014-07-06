from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.actionbar import ActionBar

from rendezvous.deck import Card


class DeckCardDisplay(BoxLayout):

    """Show a card and its details vertically."""

    card = ObjectProperty()


class DeckEditDisplay(ScrollView):

    """Display each (unlocked) card in the deck."""

    definition = ObjectProperty()

    LOCKED_CARD = Card(" ", 0)
    LOCKED_CARD.name = "HIDDEN"
    LOCKED_CARD.description = "Complete achievements to unlock additional cards."

    def __init__(self, **kwargs):
        ScrollView.__init__(self, **kwargs)
        count = 0
        for card in self.definition.cards(App.get_running_app().achievements):
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
