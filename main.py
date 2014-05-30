from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from deck import DeckDefinition, Deck, Card

__version__ = '0.0.2'


class CardDisplay(Widget):

    card = ObjectProperty(Card("Default", 0, None))


class DeckDraw(FloatLayout):

    last_card = ObjectProperty(Card(" ", 0, None))

    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)
        self.deck = Deck(DeckDefinition())

    def on_touch_down(self, touch):
        self.last_card = self.deck.draw()
        self.add_widget(CardDisplay(card=self.last_card, pos=touch.pos))
        #new_card.center = touch.pos
        


class RendezVousApp(App):
    pass

if __name__ in ("__main__", "__android__"):
    RendezVousApp().run()
