from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty, ListProperty
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout

from rendezvous import SpecialSuit, EffectType
from rendezvous.deck import Card

from gui import PLAYER, DEALER


# Quick color constants
BLANK = [1, 1, 1, 1]
DARKEN = [1, 1, 1, .5]
WHITE = [1, 1, 1, 1]
GREEN = [.25, 1, .25, 1]
RED = [1, .25, .25, 1]
BLUE = [.25, .25, 1, 1]


## GUI Components ##

class CardDisplay(Widget):

    """Widget to show a single RendezVous card."""
    
    card = ObjectProperty(allownone=True)
    color = ListProperty(BLANK)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.card = self.card
            touch.push(attrs=["card"])

    def on_touch_up(self, touch):
        if not self.collide_point(*touch.pos):
            return
        if 'card' in dir(touch) and touch.card != self.card:
            App.get_running_app().root.card_dropped(self, touch.card)
        else:
            App.get_running_app().root.card_touched(self)

    def highlight(self, color):
        if color is None:
            self.color = BLANK
        else:
            self.color = color
        self.canvas.ask_update()


class SuitDisplay(Widget):

    """Display a suit icon."""

    suit = StringProperty()


class SuitScoreDisplay(BoxLayout):

    """Display the 2-player score in one suit."""

    suit = StringProperty()
    pscore = NumericProperty()
    dscore = NumericProperty()


class ToolTipDisplay(BoxLayout):

    """Display the details of a card."""

    DUMMY_CARD = Card(" ", 0)
    DUMMY_CARD.name = " "
    DUMMY_CARD.description = "Drag a card here for more information."

    card = ObjectProperty(DUMMY_CARD)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            if 'card' in dir(touch):
                touch.pop()
                if touch.card is not None:
                    self.card = touch.card


## Game Components ##

class RoundCounter(Label):

    """Display the round number."""

    round_number = NumericProperty()
    max_round = NumericProperty()
    

class HandDisplay(BoxLayout):

    """Display a hand of cards.

    Methods:
      update      -- refresh the full display
      get         -- remove and return the card from the given display
      return_card -- return the played card to the hand display
      confirm     -- pull the selected cards out of the Hand

    """
    
    hand = ObjectProperty()
    slots = ListProperty()

    def __init__(self, **kwargs):
        """Set up the CardDisplays."""
        BoxLayout.__init__(self, **kwargs)
        for card in self.hand:
            display = CardDisplay(card=card)
            self.slots.append(display)
            self.add_widget(display)
        for i in range(len(self.hand) - len(self.slots)): # not full now?
            display = CardDisplay(card=None)
            self.slots.append(display)
            self.add_widget(display)
        self._played = []

    def update(self):
        """Update each card in the display."""
        for i, card in enumerate(self.hand):
            self.slots[i].card = None  # always force update
            self.slots[i].card = card

    def _find_display(self, card):
        """Return the slot holding this card."""
        print("... ... seeking display for %s" % card)
        if isinstance(card, CardDisplay):
            print("... ... -> CardDisplay already")
            return card
        for slot in self.slots:
            if slot.card is card:
                print("... ... -> found in slot", self.slots.index(slot))
                return slot
        print("... ... -> not found!!")
        raise ValueError(str(card))

    def swap(self, card1, card2):
        """Swap the two cards in the hand."""
        def index(c):
            t = self._find_display(c)
            if t is None: return c
            return self.slots.index(t)
        c, d = index(card1), index(card2)
        if not (isinstance(c, int) and isinstance(d, int)): return
        if c >= len(self.hand.cards) or d >= len(self.hand.cards): return
        
        self.hand.cards[c], self.hand.cards[d] = self.hand.cards[d], self.hand.cards[c]
        self.slots[c].card , self.slots[d].card = self.slots[d].card , self.slots[c].card
        if c in self._played:
            self._played[self._played.index(c)] = d
        if d in self._played:
            self._played[self._played.index(d)] = c

    def get(self, card_display):
        """Take and return the card from the given display."""
        card_display = self._find_display(card_display)
        self._played.append(self.slots.index(card_display))
        card = card_display.card
        card_display.card = None
        return card

    def return_card(self, card):
        """Return the played card to the hand display."""
        for index in self._played:
            if self.hand[index] is card:
                self.slots[index].card = card
                self._played.remove(index)
                return

    def confirm(self):
        """Confirm the played cards and update the hand."""
        for index in sorted(self._played, reverse=True):
            self.hand.pop(index)
        self._played = []


class BoardDisplay(BoxLayout):

    """Show the 4x2 Gameboard.

    Methods:
      update         -- refresh the full display
      highlight      -- highlight every card on the board
      place_card     -- place and display the card on the board
      remove_card    -- remove card from the display and return it
      validate       -- remove and return a list of invalid cards
      pop            -- remove card at the given index and return it
      play_dealer    -- play all dealer cards with timing
      apply_specials -- apply all specials with timing and highlights
      score_round    -- score each match with timing and highlights

    """
    
    board = ObjectProperty()

    def __init__(self, **kwargs):
        """Set up the CardDisplays."""
        BoxLayout.__init__(self, orientation="vertical", **kwargs)
        self.slots = []
        for i in range(len(self.board)):  # for card in board iterates all sides
            layout = BoxLayout()
            side_slots = []
            for card in self.board[i]:
                display = CardDisplay(card=card)
                side_slots.append(display)
                layout.add_widget(display)
            self.slots.append(side_slots)
            self.add_widget(layout)

    def update(self):
        """Update the visual display."""
        for i in range(len(self.board)):
            for j, card in enumerate(self.board[i]):
                self.slots[i][j].card = None  # force update
                self.slots[i][j].card = card

    def highlight(self, color):
        """Update all highlight colors at once."""
        for side in self.slots:
            for display in side:
                display.highlight(color)

    def place_card(self, card, index=None, player=PLAYER):
        """Place the card on the board, including visually."""
        if index is None:
            index = self.board.play_cards(player, [card])[0]
        else:
            self.board[player][index] = card
        self.slots[player][index].card = card

    def remove_card(self, card_display):
        """Remove the card from the display and return it."""
        try:
            index = self.slots[PLAYER].index(card_display)
        except ValueError:
            return
        card = self.board[PLAYER][index]
        self.board[PLAYER][index] = None
        card_display.card = None
        return card

    def validate(self):
        """Remove and return a list of any invalid cards."""
        return [self.pop(i) for i in self.board.validate(self.board[PLAYER])]

    def pop(self, i):
        """Remove and return the specified card."""
        card = self.board[PLAYER][i]
        self.board[PLAYER][i] = None
        self.slots[PLAYER][i].card = None
        return card


    ## Auto-scoring (with breaks)

    def play_dealer(self, cards, callback=None, timer=1.0):
        """Automatically lay out the dealer's cards one by one."""
        self.board.play_cards(DEALER, cards)
        Clock.schedule_once(lambda t: self._play_next_dealer(callback=callback,
                                                             timer=timer))

    def _play_next_dealer(self, index=None, callback=None, timer=1.0):
        """Place the next dealer card on the board."""
        if index is None:
            index = 0
        else:
            index += 1
            if index >= len(self.board[0]):
                if callback is not None:
                    Clock.schedule_once(lambda dt:callback())
                return
        self.slots[DEALER][index].card = self.board[DEALER][index]
        Clock.schedule_once(lambda t: self._play_next_dealer(index=index,
                                                             callback=callback,
                                                             timer=timer),
                            timer)

    def apply_specials(self, game, hand_display, callback=None, timer=1.0):
        """Apply all special cards in play, one-by-one with highlighting."""
        self.highlight(DARKEN)
        Clock.schedule_once(lambda t: self._apply_special(game, hand_display,
                                                          callback=callback,
                                                          timer=timer), timer)

    def _apply_special(self, game, hand_display, player=None, index=None,
                       callback=None, timer=1.0):
        """Apply the next special card, column by column."""
        if index is None:
            player, index = 0, 0
        else:
            self.slots[player][index].highlight(DARKEN)
            player += 1
            if player >= len(self.board):
                player = 0
                index += 1
                if index >= len(self.board[0]):
                    Clock.schedule_once(lambda t: callback())
                    return
        next_slot = lambda t: self._apply_special(game, hand_display,
                                                  player=player, index=index,
                                                  callback=callback,
                                                  timer=timer)
        if (self.board[player][index] is None or
            self.board[player][index].suit != SpecialSuit.SPECIAL):
            Clock.schedule_once(next_slot)
            return
            
        self.slots[player][index].highlight(BLUE)
        game._apply(player, index)
        self.update()
        if (player == PLAYER and
            self.slots[player][index].card.effect.effect == EffectType.FLUSH):
            hand_display.update()
        Clock.schedule_once(next_slot, timer)

    def score_round(self, score_display, index=None, callback=None, timer=1.0):
        """Score the given match, or all of them, with highlighting."""
        if index is not None:
            self._score_match(score_display, score_display.scoreboard, index)
            Clock.schedule_once(lambda t: callback(), timer)
        Clock.schedule_once(lambda t: self._score_next_match(score_display,
                                                             callback=callback,
                                                             timer=timer))

    def _score_next_match(self, score_display, index=None,
                          callback=None, timer=1.0):
        """Highlight and score the next match of the round."""
        if index is None:
            index = 0
        else:
            index += 1
            if index >= len(self.board[0]):
                Clock.schedule_once(lambda t: callback())
                return
        self._score_match(score_display, score_display.scoreboard, index)
        Clock.schedule_once(lambda t: self._score_next_match(score_display,
                                                             index=index,
                                                             callback=callback,
                                                             timer=timer),
                            timer)

    def _score_match(self, score_display, score, index):
        """Highlight and score the given match."""
        for player in range(len(self.board)):
            result = score._score_match(player, self.board[player][index],
                                        player-1, self.board[player-1][index])
            self.slots[player][index].highlight([WHITE, GREEN, RED][result])
        score_display.update()
        

class ScoreDisplay(BoxLayout):

    """Show the score for each suit."""

    scoreboard = ObjectProperty()

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, orientation="vertical", **kwargs)
        self.rows = []
        for i, suit in enumerate(self.scoreboard.suits):
            display = SuitScoreDisplay(suit=suit,
                                       pscore=self.scoreboard[PLAYER][i],
                                       dscore=self.scoreboard[DEALER][i])
            self.rows.append(display)
            self.add_widget(display)

    def update(self):
        """Update the display scales."""
        for i, display in enumerate(self.rows):
            display.pscore = self.scoreboard[PLAYER][i]
            display.dscore = self.scoreboard[DEALER][i]


