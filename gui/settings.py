from kivy.metrics import dp
from kivy.compat import text_type
from kivy.core.window import Window
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.settings import SettingNumeric, SettingSpacer
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

class SliderPopup(Popup):
    setting = ObjectProperty()
    value = NumericProperty()

class SettingSlider(SettingNumeric):

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
                                 value=self.value,
                                 size=(min(0.95 * Window.width, dp(500)), dp(250)))
        self.popup.open()
