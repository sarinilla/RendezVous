from kivy.app import App
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.actionbar import ActionBar
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.widget import Widget

from gui.screens.game import AchievementEarnedDisplay, UnlockDisplay


class AchievementDisplay(BoxLayout):

    """Displays one Achievement."""

    achievement = ObjectProperty()
    earned = BooleanProperty()

    def get_shading(self, earned):  # include earned for auto-binding
        """Return the RGBA color for the images."""
        if earned: return (1, 1, 1, 1)
        else: return (.25, .25, .25, 1)

    def get_backdrop(self, earned):  # include earned for auto-binding
        """Return the RGBA color for the backdrop."""
        if earned: return (0, 0, 0, 1)
        else: return (.25, .25, .25, 1)

    def get_card(self, earned):  # include earned for auto-binding
        """Return the name of the card to display (or "HIDDEN" or None)."""
        if self.achievement.reward is None:
            return None
        elif earned:
            return self.achievement.reward
        else:
            return "HIDDEN"

    def on_touch_down(self, touch):
        """Make sure we don't grab drag touches."""
        if self.collide_point(*touch.pos):
            touch.start = self
            touch.push(attrs=["start"])

    def on_touch_up(self, touch):
        """Display the Achievement screen on a touch."""
        if not self.earned: return
        if not self.collide_point(*touch.pos): return
        if 'start' in dir(touch) and touch.start is self:
            popup = Popup(title=str(self.achievement))
            layout = BoxLayout(orientation="vertical")
            if self.achievement.reward is None:
                layout.add_widget(AchievementEarnedDisplay(achievement=self.achievement))
            else:
                card = App.get_running_app().loaded_deck.get_special(self.achievement.reward)
                layout.add_widget(UnlockDisplay(achievement=self.achievement,
                                                reward=card))
            buttons = BoxLayout(size_hint=(1, .125))
            buttons.add_widget(Widget())
            buttons.add_widget(Button(text="OK", size_hint=(2, 1),
                                      on_release=popup.dismiss))
            buttons.add_widget(Widget())
            layout.add_widget(buttons)
            popup.add_widget(layout)
            popup.open()


class AchievementsScreen(Screen):
    
    """Displays the full list of available achievements.

    Includes standard Achievements as well as those for the current selected
    deck (if any).

    """

    def __init__(self, achievements, **kwargs):
        Screen.__init__(self, **kwargs)
        self.achievements = achievements

        layout = BoxLayout(orientation="vertical")
        layout.add_widget(ActionBar(size_hint=(1, .125)))
        scroller = ScrollView(do_scroll_x=False)
        self.main = main = GridLayout(cols=1, size_hint_y=None)
        main.bind(minimum_height=main.setter('height'))
        for achievement in achievements.available:
            main.add_widget(AchievementDisplay(achievement=achievement,
                                earned=(achievement in achievements.achieved)))
        scroller.add_widget(main)
        layout.add_widget(scroller)
        self.add_widget(layout)

    def update(self):
        """Update the earned/unearned status of each displayed Achievement."""
        for display in self.main.children:
            try:
                display.earned = display.achievement in self.achievements.achieved
            except AttributeError:
                continue
