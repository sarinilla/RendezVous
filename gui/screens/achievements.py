from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView


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


class AchievementsScreen(Screen):
    
    """Displays the full list of available achievements.

    Includes standard Achievements as well as those for the current selected
    deck (if any).

    """

    def __init__(self, achievements, **kwargs):
        Screen.__init__(self, **kwargs)
        self.achievements = achievements

        scroller = ScrollView(do_scroll_x=False)
        self.main = main = GridLayout(cols=1, size_hint_y=None)
        main.bind(minimum_height=main.setter('height'))
        for achievement in achievements.available:
            main.add_widget(AchievementDisplay(achievement=achievement,
                                earned=(achievement in achievements.achieved)))
        scroller.add_widget(main)
        self.add_widget(scroller)

    def update(self):
        """Update the earned/unearned status of each displayed Achievement."""
        for display in self.main.children:
            try:
                display.earned = display.achievement in self.achievements.achieved
            except AttributeError:
                continue
