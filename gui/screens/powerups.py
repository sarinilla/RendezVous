import copy

from kivy.app import App
from kivy.properties import ObjectProperty, NumericProperty, ListProperty
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.actionbar import ActionBar
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.carousel import Carousel

from rendezvous import PowerupType, SpecialSuit

from gui.components import CardDisplay, ToolTipDisplay, PowerupIcon


class CardSelect(CardDisplay):

    """CardDisplay with a specific callback on touch."""

    callback = ObjectProperty()
    args = ListProperty([])

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            if self.callback is not None:
                self.callback(self, *self.args)
                return True
        return super(CardDisplay, self).on_touch_up(touch)


class ConfirmationPopup(Popup):

    """Confirm a purchase, and select the quantity."""

    powerup = ObjectProperty()
    item_name = StringProperty("powerup")
    currency = StringProperty("wink")
    info = ObjectProperty()
    popup_chain = ListProperty()
    callback = ObjectProperty()
    count = NumericProperty(1)

    def __init__(self, **kwargs):
        Popup.__init__(self, **kwargs)
        if self.info is not None:
            self.ids.main.add_widget(self.info, 2)

    def purchase(self, *args):
        """Charge the currency and finalize the purchase."""
        self.dismiss()
        for popup in self.popup_chain:
            popup.dismiss()
        if App.get_running_app().purchase_powerup(self.powerup, self.count):
            if self.callback is not None:
                self.callback(self.count)

    def update_count(self):
        self.count = self.ids.counter.value


class PowerupDisplay(BoxLayout):

    """Display one Powerup with its details for purchase."""

    powerup = ObjectProperty()
    count = NumericProperty()

    def on_touch_down(self, touch):
        """Make sure we don't grab drag touches."""
        if self.collide_point(*touch.pos):
            touch.start = self
            touch.push(attrs=["start"])

    def on_touch_up(self, touch):
        """Display a purchase confirmation."""
        if super(BoxLayout, self).on_touch_up(touch): return
        if not self.collide_point(*touch.pos): return
        if 'start' in dir(touch) and touch.start is self:
            if self.powerup.type == PowerupType.PLAY_CARD:
                self._choose_card()
            else:
                self._confirm_purchase()

    def _choose_card(self):
        """Select a card to purchase for PowerupType.PLAY_CARD."""
        app = App.get_running_app()
        popup = Popup(title=str(self.powerup))
        carousel = Carousel(direction='right')
        deck = list(app.loaded_deck.cards(app.achievements))
        for i in range(0, len(deck), 10):
            layout = GridLayout(rows=2)
            for card in deck[i:i+10]:
                layout.add_widget(CardSelect(card=card,
                                             callback=self._confirm_card,
                                             args=(card, popup)))
            carousel.add_widget(layout)
        popup.add_widget(carousel)
        popup.open()

    def _confirm_card(self, display, card, selection_popup):
        """Confirm the selected card for PowerupType.PLAY_CARD."""
        self.powerup = copy.deepcopy(self.powerup)  # divorce from other stored versions
        self.powerup.value = str(card)
        if card.suit == SpecialSuit.SPECIAL:
            self.powerup.price = 50
        else:
            self.powerup.price = card.value * 5
        popup = ConfirmationPopup(title="%s: %s" % (self.powerup, card),
                                  item_name="card", powerup=self.powerup,
                                  popup_chain=[selection_popup],
                                  info=ToolTipDisplay(card=card, size_hint=(1, 3)),
                                  callback=self._increment,
                                  size_hint=(1, .75))
        popup.open()

    def _confirm_purchase(self):
        """Ask the user to confirm the purchase."""
        popup = ConfirmationPopup(title=str(self.powerup),
                                  powerup=self.powerup,
                                  callback=self._increment,
                                  size_hint=(1, .5))
        popup.open()

    def _increment(self, count=1):
        self.count += count

    
class PowerupScreen(Screen):

    """Display the full list of available achievements."""

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.app = App.get_running_app()

        layout = BoxLayout(orientation="vertical")
        layout.add_widget(ActionBar(size_hint=(1, .125)))
        scroller = ScrollView(do_scroll_x=False)
        self.main = main = GridLayout(cols=1, size_hint_y=None)
        main.bind(minimum_height=main.setter('height'))
        for powerup in self.app.powerups:
            main.add_widget(PowerupDisplay(powerup=powerup,
                                    count=self.app.powerups.count(powerup)))
        scroller.add_widget(main)
        layout.add_widget(scroller)
        self.add_widget(layout)

    def update(self):
        for display in self.main.children:
            try:
                display.count = self.app.powerups.count(display.powerup)
            except AttributeError:
                pass
