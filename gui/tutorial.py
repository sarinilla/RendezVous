from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.properties import StringProperty, ObjectProperty, NumericProperty
from kivy.properties import BooleanProperty, ListProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout


from gui.components import RoundCounter, ScoreDisplay, ToolTipDisplay
from gui.components import HandDisplay, BoardDisplay


class SpeechBubble(Label):

    """Display a speech bubble with word-by-word text."""

    full_text = StringProperty()

    def __init__(self, **kwargs):
        Label.__init__(self, markup=True, valign="top", halign="left", **kwargs)
        self.bind(size=self.setter('text_size'))
        Clock.schedule_once(self._draw)

    def _draw(self, *args):
        with self.canvas.before:
            Color(0, 0, 0, .75)
            Rectangle(size=(self.size[0]+20, self.size[1]+20),
                      pos=(self.pos[0]-10, self.pos[1]-10))

    def on_full_text(self, *args):
        Clock.unschedule(self._next_word)
        self.words_left = self.full_text.split()
        self.text = self.words_left.pop(0)
        Clock.schedule_interval(self._next_word, 0.4)

    def _next_word(self, *args):
        if not self.words_left:
            Clock.unschedule(self._next_word)
            return
        self.text += ' ' + self.words_left.pop(0)


class TutorialDealer(Widget):

    """Display a dealer image with a speech bubble."""

    dealer_index = NumericProperty()
    text = ListProperty()
    reverse = BooleanProperty(False)
    callback = ObjectProperty()

    def __init__(self, **kwargs):
        Widget.__init__(self, **kwargs)
        self.layout = BoxLayout()
        self.dealer = Widget()
        Clock.schedule_once(self._show_dealer)
        self.bubble = SpeechBubble(full_text=self.text.pop(0),
                                   size_hint=(.3, .6),
                                   pos_hint={'top': 1})
        if self.reverse:
            self.layout.add_widget(self.bubble)
            self.layout.add_widget(self.dealer)
        else:
            self.layout.add_widget(self.dealer)
            self.layout.add_widget(self.bubble)
        self.add_widget(self.layout)
        self.bind(size=self.layout.setter('size'), pos=self.layout.setter('pos'))

    def _show_dealer(self, *args):
        with self.dealer.canvas:
            Color(1, 1, 1, 1)
            Rectangle(texture=App.get_running_app().get_dealer_texture(
                                    self.dealer_index, 0),
                      size=(min(self.dealer.size[0], self.dealer.size[1]),
                            min(self.dealer.size[0], self.dealer.size[1])),
                      pos=self.dealer.pos)

    def on_touch_up(self, touch):
        self._next_text()
        return True

    def _next_text(self):
        """Advance the text in the speech bubble.
        If no more text, then send a call for the next screen.
        """
        if self.bubble.words_left:
            self.bubble.words_left = []
            self.bubble.text = self.bubble.full_text
            return
        try:
            self.bubble.full_text = self.text.pop(0)
        except IndexError:
            if self.callback is not None:
                self.callback()

class TutorialScreen(Screen):
    
    """Provides common features for Tutorial Screens."""

    next_tutorial = None

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        Clock.schedule_once(self._make_displays)
        # ^^ scheduled so that self.manager is set

    def _make_displays(self, *args):
        """Prepare the display areas."""
        self.gameboard = BoardDisplay(
            board=self.manager.main.gameboard.board,
            size_hint=(4, 1))
        self.round_counter = RoundCounter(
            round_number=self.manager.game.round,
            max_round=self.manager.main.round_counter.max_round,
            size_hint=(1, .075))
        self.scoreboard = ScoreDisplay(
            scoreboard=self.manager.main.scoreboard.scoreboard,
            size_hint=(1, .4))
        self.tooltip = ToolTipDisplay(size_hint=(1, .5))
        self.hand_display = HandDisplay(
            hand=self.manager.main.hand_display.hand,
            size_hint=(1, .3))
        self._layout()

    def _layout(self, *args):
        """Lay out the display."""
        self.float = FloatLayout()
        self.main = main = BoxLayout(orientation="vertical")
        layout = BoxLayout()
        layout.add_widget(self.gameboard)
        self.sidebar = sidebar = BoxLayout(orientation="vertical")
        sidebar.add_widget(self.round_counter)
        sidebar.add_widget(self.scoreboard)
        sidebar.add_widget(self.tooltip)
        layout.add_widget(sidebar)
        main.add_widget(layout)
        main.add_widget(self.hand_display)
        self.float.add_widget(main)
        self.add_widget(self.float)
        Clock.schedule_once(self.draw_tutorial)

    def _fade(self, component):
        """Make the given component fade into the background."""
        with component.canvas:
            Color(0, 0, 0, .75)
            Rectangle(size=component.size, pos=component.pos)

    def _highlight(self, component):
        """Fade all but the given component."""
        for c in (self.gameboard, self.round_counter, self.scoreboard,
                  self.tooltip, self.hand_display):
            if c is not component:
                self._fade(c)

    def draw_tutorial(self, *args):
        """Draw additional tutorial items."""
        pass

    def update(self):
        """Prepare the screen to be shown."""
        self.gameboard.update()
        self.hand_display.update()

    def advance(self, *args):
        """Advance to the next tutorial screen."""
        if self.next_tutorial is None:
            self.manager.switcher('home')
        else:
            self.manager.switch_to(self.next_tutorial())
        self.manager.remove_widget(self)


    def all_cards_selected(self):
        return False

    def next_round(self, num, game_over):
        return False

    def card_touched(self):
        """Don't allow card touches during text playback."""
        return True


class TutorialActionItemScreen(TutorialScreen):

    """Show the normal game screen, with a text bar across the top."""

    action_item = StringProperty()

    def draw_tutorial(self, *args):
        self.action_prompt = Label(text='[b]%s[/b]' % self.action_item.upper(),
                                   markup=True,
                                   valign="middle", halign="center",
                                   size_hint=(.75, .2),
                                   pos_hint={'x':0, 'y':.8})
        self.float.add_widget(self.action_prompt)

    def on_action_item(self, *args):
        self.action_prompt.text = self.action_item

    def card_touched(self):
        """Allow card touches to progress normally."""
        return False


##  Begin Tutorial Screens (in reverse order)  ##


class TutorialFinishGame(TutorialActionItemScreen):

    action_item = "Play on!"


class TutorialSpecialCardDragged(TutorialScreen):

    text = ["There are many different types of special cards.",
            "The best cards are unlocked by completing RendezVous Achievements.",
            "When you unlock a custom deck, it will come with its own unique Special Cards!"]

    next_tutorial = TutorialFinishGame

    def draw_tutorial(self, *args):
        """Show the dealer text."""
        self._fade(self.main)
        self.float.add_widget(TutorialDealer(dealer_index=3,
                                             text=self.text,
                                             size_hint=(.8, .8),
                                             pos=(0, 0),
                                             callback=self.advance))


class TutorialSpecialCardDrag(TutorialActionItemScreen):

    action_item = "Drag the special card below the scoreboard"
    next_tutorial = TutorialSpecialCardDragged
    ready = False

    def draw_tutorial(self, *args):
        with self.tooltip.canvas.before:
            Color(0, 0, 1, .75)
            Rectangle(size=self.tooltip.size, pos=self.tooltip.pos)
        self._fade(self.gameboard)
        self._fade(self.round_counter)
        self._fade(self.scoreboard)
        self.tooltip.bind(card=self._dragged)
        super(TutorialSpecialCardDrag, self).draw_tutorial(*args)
        
    def _dragged(self, *args):
        self.ready = True

    def card_touched(self):
        if self.ready:
            self.advance()
        return True


class TutorialSpecialCard(TutorialScreen):

    text = ["[b]Introducing Special Cards[/b]",
            "In addition to the five normal suits, you will sometimes get special cards in your hand.",
            "These can only be played when certain conditions are met.",
            "Many of them have the power to affect the other cards you play, or even the dealer's cards.",
            "You drew a special card!",
            "Drag your new special card onto the tooltip display below the scoreboard to read about what it does and how to use it."]

    next_tutorial = TutorialSpecialCardDrag

    def draw_tutorial(self, *args):
        """Plant a special card and show dealer text."""
        self._highlight(self.hand_display)
        special = self.manager.plant_special()
        self.text[4] = self.text[4].replace("special", special.name)
        self.float.add_widget(TutorialDealer(dealer_index=3,
                                             text=self.text,
                                             size_hint=(.8, .8),
                                             pos_hint={'x':.1, 'y':0},
                                             callback=self.advance))


class TutorialPlayAFew(TutorialActionItemScreen):

    action_item = "Play a few rounds!"

    next_tutorial = TutorialSpecialCard

    def draw_tutorial(self, *args):
        """Leave the tooltip area faded."""
        self._fade(self.tooltip)
        self.gameboard.next_round_prompted()
        super(TutorialPlayAFew, self).draw_tutorial(*args)

    def next_round(self, num, game_over):
        if num == 11:
            self.advance()
            return True
        return False


class TutorialScoreboard(TutorialScreen):

    text = ["Your score in each suit is shown on the left side of the scoreboard.",
            "The dealer's score is to the right.",
            "After 20 rounds, the winner is the one leading in the most suits."]

    next_tutorial = TutorialPlayAFew
    
    def draw_tutorial(self, *args):
        """Show the dealer text."""
        self._highlight(self.scoreboard)
        self.float.add_widget(TutorialDealer(dealer_index=2,
                                             text=self.text,
                                             size_hint=(.8, .8),
                                             callback=self.advance))


class TutorialScoringHighlights(TutorialScreen):

    text = ["As the round is scored, the highlighting will help you see who won each match-up."]

    next_tutorial = TutorialScoreboard
    
    def draw_tutorial(self, *args):
        """Show the dealer text."""
        self._highlight(self.gameboard)
        self.manager._reset_scoring()
        self.manager._score(then_prompt=False)
        self.float.add_widget(TutorialDealer(dealer_index=2,
                                             reverse=True,
                                             text=self.text,
                                             size_hint=(.8, .8),
                                             pos_hint={'x':.2, 'y':0},
                                             callback=self.advance))


class TutorialScoringReplay(TutorialScreen):

    text = ["A win earns you 10 points in the suit you played, and 10 points in the dealer's suit.",
            "A loss costs you 10 points in your suit only."]

    next_tutorial = TutorialScoringHighlights
    
    def draw_tutorial(self, *args):
        """Replay the scoring sequence behind the dealer text."""
        self._highlight(self.scoreboard)
        self.float.add_widget(TutorialDealer(dealer_index=2,
                                             text=self.text,
                                             size_hint=(.8, .8),
                                             pos=(0, 0),
                                             callback=self.advance))

    def advance(self, *args):
        """Only advance when the sequence is complete."""
        if not self.manager._in_progress:
            super(TutorialScoringReplay, self).advance(*args)


class TutorialScoring(TutorialScreen):

    text = ["There are five suits in the deck, and you are scored in each suit."]

    next_tutorial = TutorialScoringReplay
    
    def draw_tutorial(self, *args):
        """Replay the scoring sequence behind the dealer text."""
        self._highlight(self.scoreboard)
        self.float.add_widget(TutorialDealer(dealer_index=2,
                                             text=self.text,
                                             size_hint=(.8, .8),
                                             pos=(0, 0),
                                             callback=self.advance))


class TutorialDealerPlay(TutorialScreen):

    text = ["Each card you play is compared against the card directly above it to determine your score.",
            "Green highlights are the match winners, and red highlights are the losers.",
            "If the cards tie, then neither one is highlighted."]

    next_tutorial = TutorialScoring
    
    def draw_tutorial(self, *args):
        """Play the scoring sequence behind the dealer text."""
        self._highlight(self.gameboard)
        self.manager._score(then_prompt=False)
        self.float.add_widget(TutorialDealer(dealer_index=1,
                                             reverse=True,
                                             text=self.text,
                                             size_hint=(.8, .8),
                                             pos_hint={'x':.2, 'y':0},
                                             callback=self.advance))

    def advance(self, *args):
        """Only advance when the sequence is complete."""
        if not self.manager._in_progress:
            super(TutorialDealerPlay, self).advance(*args)


class TutorialDealerTurn(TutorialScreen):

    text = ["[b]My turn![/b]",
            "I have a hand of 10 cards, just like you.",
            "Each round, I will pick four cards to play against yours."]
    
    next_tutorial = TutorialDealerPlay
    
    def draw_tutorial(self, *args):
        """Show the dealer text while playing in the background."""
        self._highlight(self.gameboard)
        self.manager._play_dealer(then_score=False)
        self.float.add_widget(TutorialDealer(dealer_index=1,
                                             reverse=True,
                                             text=self.text,
                                             size_hint=(.8, .8),
                                             pos_hint={'right': 1},
                                             callback=self.advance))

    def advance(self, *args):
        """Only advance when the play is complete."""
        if not self.manager._in_progress:
            super(TutorialDealerTurn, self).advance(*args)


class TutorialPickingCards(TutorialActionItemScreen):

    action_item = "Select 4 cards"
    next_tutorial = TutorialDealerTurn

    def all_cards_selected(self, *args):
        self.advance()
        return True  # don't play the dealer's cards yet!
    

class TutorialPickCards(TutorialScreen):

    text = ["Your hand is displayed below.",
            "Each round, you will pick 4 cards to play.",
            "After you play, your hand will be refilled to 10 cards."]

    next_tutorial = TutorialPickingCards
    
    def draw_tutorial(self, *args):
        """Highlight the hand and show the welcome text."""
        self._highlight(self.hand_display)
        self.float.add_widget(TutorialDealer(dealer_index=0,
                                             text=self.text,
                                             size_hint=(.8, .8),
                                             pos=(0, 0),
                                             callback=self.advance))


class FirstTutorialScreen(TutorialScreen):

    """Starting point for the tutorial."""

    text = ["[b]Welcome to RendezVous![/b]",
            "This tutorial will walk you through your first game, introducing key concepts along the way.",
            "RendezVous is easy to play, but you will find the strategies to be endless!"]

    next_tutorial = TutorialPickCards
    
    def draw_tutorial(self, *args):
        """Cover the game screen items and show the welcome text."""
        self._fade(self.main)
        self.float.add_widget(TutorialDealer(dealer_index=0,
                                             text=self.text,
                                             size_hint=(.8, .8),
                                             pos=(0, 0),
                                             callback=self.advance))

