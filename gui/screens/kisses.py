from kivy.uix.screenmanager import Screen
from kivy.uix.actionbar import ActionBar
from kivy.uix.boxlayout import BoxLayout

from gui.components import HomeButton


class KissesScreen(Screen):

    def __init__(self, **kwargs):
        super(KissesScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation="vertical")
        layout.add_widget(ActionBar(size_hint=(1, .125)))
        sideways = BoxLayout()
        sideways.add_widget(HomeButton(source="atlas://gui/homescreen/backgrounds",
                                       text_below="Backgrounds (5 kisses)",
                                       on_release=lambda *a: self.manager.switcher('backgrounds')))
        sideways.add_widget(HomeButton(source="atlas://gui/homescreen/decks",
                                       text_below="Decks (15 kisses)",
                                       on_release=lambda *a: self.manager.switcher('decks')))
        layout.add_widget(sideways)
        self.add_widget(layout)
