from kivy.app import App
from kivy.uix.settings import SettingsWithNoMenu
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.actionbar import ActionBar

class SettingsScreen(Screen):

    """Display the settings with an ActionBar."""

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        layout = BoxLayout(orientation="vertical")
        layout.add_widget(ActionBar(size_hint=(1, .125)))
        settings = SettingsWithNoMenu(size_hint=(1, .875))
        App.get_running_app().build_settings(settings)
        layout.add_widget(settings)
        self.add_widget(layout)
