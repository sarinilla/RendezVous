import os

from kivy.app import App
from kivy.metrics import dp
from kivy.compat import text_type
from kivy.core.window import Window
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.uix.settings import SettingNumeric, SettingSpacer, SettingOptions
from kivy.uix.settings import SettingItem
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

from rendezvous import GameSettings


class SliderPopup(Popup):
    """Popup for the SettingSlider."""
    setting = ObjectProperty()
    value = NumericProperty()

class SettingSlider(SettingNumeric):

    """Use a slider to select a decimal value."""

    popup = ObjectProperty(None, allownone=True)
    slider = ObjectProperty(None)
 
    def on_panel(self, instance, value):
        if value is None:
            return
        self.bind(on_release=self._create_popup)

    def _dismiss(self, *largs):
        if self.popup:
            self.popup.dismiss()
        self.popup = None
 
    def _validate(self):
        self.value = text_type(round(self.popup.ids.slider.value, 2))
        self._dismiss()
            
    def _create_popup(self, instance):
        """Modified from SettingString's popup."""
        # create popup layout
        self.popup = SliderPopup(title=self.title, setting=self,
                                 value=float(self.value),
                                 size=(min(0.95 * Window.width, dp(500)), dp(250)))
        self.popup.open()


class SettingAIDifficulty(SettingOptions):

    """Extend SettingOptions to use a numerical representation of AI."""

    options = ["Dumb Luck", "Artificial Intelligence", "Brilliantly Evil"]

    def _set_option(self, instance):
        self.value = text_type(self.options.index(instance.text)+1)
        self.popup.dismiss()


class SettingButton(SettingItem):

    """Touch it to trigger an action (via on_config_change)."""

    def on_release(self):
        if self.value == "1":
            self.value = "2"
        else:
            self.value = "1"


class BackgroundDisplay(BoxLayout):

    """Display one available background image."""

    filename = StringProperty()
    popup = ObjectProperty()

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            App.get_running_app().purchase_background(self.filename, self.popup)
            return True
        super(BackgroundDisplay, self).on_touch_up(touch)


class BackgroundPicker(SettingItem):

    """Select a game background from the loaded catalog."""

    def on_release(self):
        popup = Popup(title="Select a Background")
        self.scroller = ScrollView(do_scroll_x=False)
        self.grid = GridLayout(cols=3, size_hint_y=None)
        for filename in sorted(os.listdir(os.path.join("data", "backgrounds"))):
            filename = os.path.basename(filename)
            self.grid.add_widget(BackgroundDisplay(filename=filename,
                                                   popup=popup))
        self.scroller.bind(size=self._resize)
        self.scroller.add_widget(self.grid)
        popup.add_widget(self.scroller)
        popup.open()

    def _resize(self, *args):
        self.grid.size = (self.scroller.size[0],
                    self.scroller.size[0] / 3 * (len(self.grid.children) / 3))
