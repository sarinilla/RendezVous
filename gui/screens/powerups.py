import copy

from kivy.app import App
from kivy.properties import ObjectProperty, NumericProperty, ListProperty
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

from gui.components import CardDisplay, ToolTipDisplay


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
                layout.add_widget(CardSelect(card=card, callback=self._confirm_card, args=(card, popup)))
            carousel.add_widget(layout)
        popup.add_widget(carousel)
        popup.open()

    def _confirm_card(self, display, card, selection_popup):
        """Confirm the selected card for PowerupType.PLAY_CARD."""
        self.powerup = copy.deepcopy(self.powerup)  # divorce from other stored versions
        popup = Popup(title="%s: %s" % (self.powerup, card))
        layout = BoxLayout(orientation="vertical")
        self.powerup.value = str(card)
        if card.suit == SpecialSuit.SPECIAL:
            self.powerup.price = 50
        else:
            self.powerup.price = card.value * 5
        layout.add_widget(Label(text="Are you sure you would like to purchase this card for %s wink%s?"
                                     % (self.powerup.price, "s" if self.powerup.price != 1 else ""),
                                valign="middle", halign="center"))
        layout.add_widget(ToolTipDisplay(card=card, size_hint=(1, 5)))
        buttons = BoxLayout()
        buttons.add_widget(Widget())
        buttons.add_widget(Button(text="YES", on_release=lambda x: self.purchase(popup, selection_popup)))
        buttons.add_widget(Button(text="no", on_release=popup.dismiss))
        buttons.add_widget(Widget())
        layout.add_widget(buttons)
        popup.add_widget(layout)
        popup.open()

    def _confirm_purchase(self):
        """Ask the user to confirm the purchase."""
        app = App.get_running_app()
        popup = Popup(title=str(self.powerup),
                      size_hint=(1, .5))
        layout = BoxLayout(orientation="vertical")
        layout.add_widget(Label(text="Are you sure you would like to purchase this powerup for %s wink%s?"
                                     % (self.powerup.price, "s" if self.powerup.price != 1 else ""),
                                valign="middle", halign="center"))
        buttons = BoxLayout()
        buttons.add_widget(Widget())
        buttons.add_widget(Button(text="YES", on_release=lambda x: self.purchase(popup)))
        buttons.add_widget(Button(text="no", on_release=popup.dismiss))
        buttons.add_widget(Widget())
        layout.add_widget(buttons)
        popup.add_widget(layout)
        popup.open()

    def purchase(self, *popups):
        """Charge the currency and finalize the purchase."""
        for popup in popups:
            popup.dismiss()
        if App.get_running_app().purchase_powerup(self.powerup):
            self.count += 1

    
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
