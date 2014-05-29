from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, ListProperty, ReferenceListProperty
from deck import Deck, Card

class CardDisplay(BoxLayout):

    card = ObjectProperty(Card("Default", 0))

    
class BoardDisplay(BoxLayout):
    board1 = ListProperty([Card("Player1", i+1) for i in range(4)])
    board2 = ListProperty([Card("Player2", i+1) for i in range(4)])
    board = ReferenceListProperty(board1, board2)


class RendezVousApp(App):
    pass

if __name__ in ("__main__", "__android__"):
    RendezVousApp().run()
