from kivy.app import App
from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.stacklayout import StackLayout

from gui.components import PowerupIcon

from rendezvous.powerups import Powerup


class UsablePowerupIcon(PowerupIcon):

    def on_touch_up(self, touch):
        """Use the powerup."""
        if not self.collide_point(*touch.pos): return
        App.get_running_app().root.use_powerup(self.powerup)


class PowerupTray(ModalView):

    """Displays Powerup icons for use during the game."""

    def __init__(self, **kwargs):
        ModalView.__init__(self, size_hint=(.15, 1), pos_hint={'right': 1},
                           **kwargs)
        app = App.get_running_app()
        scroller = ScrollView(do_scroll_x=False)
        layout = StackLayout(padding=[dp(10)], size_hint_y=None)
        layout.height = layout.width * len(app.powerups.purchased)
        for powerup in app.powerups.purchased:
            if isinstance(powerup, Powerup):
                layout.add_widget(UsablePowerupIcon(powerup=powerup,
                                                    size_hint=(1, None)))
        scroller.add_widget(layout)
        self.add_widget(scroller)
            

class PowerupsAvailable:

    """Abstract parent class to enable powerups on a game screen."""

    def open_tray(self):
        self.powerup_tray = PowerupTray()
        self.powerup_tray.open()

    def close_tray(self):
        try:
            self.powerup_tray.dismiss()
        except: pass

    def on_touch_down(self, touch):
        if super(PowerupsAvailable, self).on_touch_down(touch):
            if 'card' in dir(touch) and touch.card is not None:
                return True
        if touch.sx > .75:
            touch.start = touch.sx, touch.sy
            touch.push(attrs=["start"])

    def on_touch_up(self, touch):
        if 'start' in dir(touch):
            move_x, move_y = touch.sx - touch.start[0], touch.sy - touch.start[1]
            if (move_x < 0 and move_y > -0.05 and move_y < 0.05):
                self.open_tray()
        else:
            super(PowerupsAvailable, self).on_touch_up(touch)

    def update(self):
        self.close_tray()
