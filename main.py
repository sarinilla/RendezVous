import os

from kivy.app import App
from kivy.core.image import Image
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty

from rendezvous.deck import DeckDefinition, Deck, Card

__version__ = '0.0.3'


class CardDisplay(Widget):

    card = ObjectProperty(Card(" ", 0))
    texture = None

    def __init__(self, **kwargs):
        self.deck = kwargs["deck"]
        self.img = kwargs["img"]
        Widget.__init__(self, **kwargs)

    def on_card(self, instance, event):
        self.texture = self.img.get_region(*self.deck.get_card_texture(self.card))


class DeckDraw(FloatLayout):

    last_card = ObjectProperty(Card(" ", 0))

    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)
        self.deck = Deck(DeckDefinition())
        self.deck_image = Image(self.deck.definition.img_file).texture

    def on_touch_down(self, touch):
        self.last_card = self.deck.draw()
        self.add_widget(CardDisplay(card=self.last_card,
                                    deck=self.deck.definition,
                                    img=self.deck_image,
                                    pos=touch.pos))        


class RendezVousApp(App):
    def build(self):
        self.icon = os.path.join("data", "RVlogo.ico")

if __name__ in ("__main__", "__android__"):
    RendezVousApp().run()
