import os

from functools import partial
from kivy.clock import Clock
from kivy.app import App
from kivy.properties import ObjectProperty, ListProperty
from kivy.properties import StringProperty, NumericProperty
from kivy.core.image import Image
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.carousel import Carousel
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.loader import Loader

from rendezvous import GameSettings, SpecialSuit, EffectType
from rendezvous.deck import DeckDefinition, Deck, Card
from rendezvous.gameplay import Hand, Gameboard, Scoreboard, RendezVousGame
from rendezvous.statistics import Statistics
from rendezvous.achievements import AchievementList, Achievement


__version__ = '0.3.5'


# Readability constants for the two players
DEALER = 0
PLAYER = 1

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
        if self.collide_point(*touch.pos):
            App.get_running_app().root.card_touched(self)

    def highlight(self, color):
        if color is None:
            self.color = BLANK
        else:
            self.color = color
        self.canvas.ask_update()


class SuitDisplay(BoxLayout):

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

    """Display a hand of cards."""
    
    hand = ObjectProperty()
    slots = ListProperty()

    def __init__(self, **kwargs):
        """Set up the CardDisplays."""
        BoxLayout.__init__(self, **kwargs)
        for card in self.hand:
            display = CardDisplay(card=card)
            self.slots.append(display)
            self.add_widget(display)
        self._played = []

    def update(self):
        """Update each card in the display."""
        for i, card in enumerate(self.hand):
            self.slots[i].card = None  # always force update
            self.slots[i].card = card

    def get(self, card_display):
        """Take and return the card from the given display."""
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

    """Show the 4x2 Gameboard."""
    
    board = ObjectProperty()
    slots = []

    def __init__(self, **kwargs):
        """Set up the CardDisplays."""
        BoxLayout.__init__(self, orientation="vertical", **kwargs)
        for i in range(len(self.board)):  # for card in board iterates all sides
            side = self.board[i]
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
        card = card_display.card
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
                                                             callback=callback),
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
        if self.board[player][index].suit != SpecialSuit.SPECIAL:
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
    rows = []

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, orientation="vertical", **kwargs)
        for i, suit in enumerate(self.scoreboard.suits):
            display = SuitDisplay(suit=suit,
                                  pscore=self.scoreboard[PLAYER][i],
                                  dscore=self.scoreboard[DEALER][i])
            self.rows.append(display)
            self.add_widget(display)

    def update(self):
        """Update the display scales."""
        for i, display in enumerate(self.rows):
            display.pscore = self.scoreboard[PLAYER][i]
            display.dscore = self.scoreboard[DEALER][i]


## RendezVous Game ##

class GameScreen(Screen):
    
    """Displays the game in progress.

    Attributes:
      gameboard     -- displays the Gameboard
      round_counter -- displays the current round
      scoreboard    -- displays the Scoreboard
      hand_display  -- displays the player's Hand
      tooltip       -- displays the details on one card

    """

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)

        # Prepare the display areas
        game = kwargs["game"]
        self.gameboard = BoardDisplay(board=game.board,
                                      size_hint=(4, 1))
        self.round_counter = RoundCounter(round_number=1,
                                          max_round=GameSettings.NUM_ROUNDS,
                                          size_hint=(1, .075))
        self.scoreboard = ScoreDisplay(scoreboard=game.score,
                                       size_hint=(1, .4))
        self.tooltip = ToolTipDisplay(size_hint=(1, .5))
        self.hand_display = HandDisplay(hand=game.players[PLAYER],
                                        size_hint=(1, .3))

        # Lay out the display
        main = BoxLayout(orientation="vertical")
        layout = BoxLayout()
        layout.add_widget(self.gameboard)
        sidebar = BoxLayout(orientation="vertical")
        sidebar.add_widget(self.round_counter)
        sidebar.add_widget(self.scoreboard)
        sidebar.add_widget(self.tooltip)
        layout.add_widget(sidebar)
        main.add_widget(layout)
        main.add_widget(self.hand_display)
        self.add_widget(main)


class RendezVousWidget(ScreenManager):

    """Arrange the screen - hand at the bottom, gameboard, score, etc.

    Attributes:
      game        -- behind-the-scenes RendezVousGame
      achieved    -- Achievements earned during the game
      dealer_play -- cards picked out for the dealer
      main        -- primary screen for gameplay

    """

    def __init__(self, **kwargs):
        """Arrange the widgets."""
        ScreenManager.__init__(self, transition=FadeTransition(), **kwargs)
        app = kwargs["app"]

        # Prepare internal storage
        self.game = RendezVousGame(deck=app.loaded_deck,
                                   achievements=app.achievements)
        self.game.new_game()
        self._cards_played = []  # hand indices played so far
        self.achieved = []
        self.dealer_play = None

        # Prepare the screens
        self.main = GameScreen(game=self.game, name='main')
        self.add_widget(self.main)

    def card_touched(self, card_display):
        """Handle a touch to a displayed card."""
        if card_display.card is None: return
        if self.dealer_play is None:
            self.dealer_play = self.game.players[DEALER].AI_hard(
                                    DEALER, self.game.board, self.game.score)
        if self.game.board.is_full(PLAYER): return  # not during scoring!
        
        loc = card_display.parent
        if loc is self.main.hand_display:
            card = self.main.hand_display.get(card_display)
            self.main.gameboard.place_card(card)
            if self.game.board.is_full(PLAYER):
                if self.main.gameboard.validate() == []:

                    self.main.hand_display.confirm()
                    self.main.gameboard.play_dealer(self.dealer_play,
                                                    callback=self._specials)
                    for card in self.dealer_play:
                        self.game.players[DEALER].remove(card)
                    self.dealer_play = None
                    
        elif loc.parent is self.main.gameboard:
            card = self.main.gameboard.remove_card(card_display)
            self.main.hand_display.return_card(card)

    def _specials(self):
        """Apply all specials."""
        self.main.gameboard.apply_specials(self.game, self.main.hand_display,
                                           self._score)

    def _score(self):
        """Score the round."""
        self.main.gameboard.score_round(self.main.scoreboard,
                                        callback=self._next_round)

    def _next_round(self):
        """Clear the board for the next round."""
        game_over = self.game.next_round()
        if game_over:
            self.achieved = App.get_running_app().record_score(self.game.score)
            self._winner = WinnerScreen(self.game.score, self.achieved,
                                        name='winner')
            self.switch_to(self._winner)
            return
        self.main.round_counter.round_number = self.game.round
        self.main.gameboard.highlight(None)
        self.main.gameboard.update()
        self.main.hand_display.update()

    def play_again(self):
        """Start a new game."""
        self.game.new_game()
        self.achieved = []
        self.main.gameboard.highlight(None)
        self.main.gameboard.update()
        self.main.hand_display.update()
        self.main.scoreboard.update()
        self.main.round_counter.round = 1
        self.current = 'main'
        self.remove_widget(self._winner)


## Win/Lose Screen ##

class AchievementDisplay(BoxLayout):

    """Show an Achievement earned this game."""

    achievement = ObjectProperty(Achievement(' '))


class UnlockDisplay(BoxLayout):

    """Show an Achievement with an unlocked SpecialCard."""
    
    DUMMY_CARD = Card(" ", 0)
    DUMMY_CARD.name = " "
    DUMMY_CARD.description = " "

    achievement = ObjectProperty(Achievement(' '))
    reward = ObjectProperty(DUMMY_CARD, allownone=True)


class FinalScoreDisplay(BoxLayout):

    """Display the winner/loser announcement and final score."""

    score = ObjectProperty()

    def get_win_text(self):
        pscore = self.score.total(PLAYER)
        dscore = self.score.total(DEALER)
        if pscore > dscore:
            return "YOU WIN!" 
        elif pscore == dscore:
            return "It's a draw!"
        else:
            return "Dealer won."


class WinnerScreen(Screen):

    """Displays the winner/loser announcement [and an unlock]."""

    def __init__(self, score, achieved=None, **kwargs):
        Screen.__init__(self, **kwargs)
    
        self.ids.carousel.add_widget(FinalScoreDisplay(score=score))
        deck = App.get_running_app().loaded_deck
        for achievement in achieved:
            if achievement.reward is None:
                ach = AchievementDisplay(achievement=achievement)
                self.ids.carousel.add_widget(ach)
                continue
            unlock = UnlockDisplay(achievement=achievement,
                                   reward=deck.get_special(achievement.reward))
            self.ids.carousel.add_widget(unlock)
        if achieved:
            self.ids.carousel.index = 1


## Meta Data and App Info ##

class RendezVousApp(App):

    """Main RendezVous App, with deck loaded."""
    
    deck_texture = ObjectProperty()

    def _image_loaded(self, loader):
        """Update the deck image when it's finished loading."""
        if loader.image.texture:
            self.deck_texture = loader.image.texture

    def _achievements_loaded(self, loader):
        if loader.image.texture:
            self.achievement_texture = loader.image.texture

    def build(self):
        """Load the deck image and create the RendezVousWidget."""
        self.icon = os.path.join("data", "RVlogo.ico")
        user_dir = self.user_data_dir
        if not os.path.isdir(user_dir):
            user_dir = "player"
        self.statistics = Statistics(os.path.join(user_dir, "stats.txt"))
        self.achievements = AchievementList(os.path.join(user_dir, "unlocked.txt"))
        #self.achievement_texture = Image(self.achievements.image_file).texture
        loader = Loader.image(self.achievements.image_file)
        loader.bind(on_load=self._achievements_loaded)
        self.loaded_deck = DeckDefinition()
        loader = Loader.image(self.loaded_deck.img_file)
        loader.bind(on_load=self._image_loaded)
        self.deck_texture = Image(self.loaded_deck.img_file).texture
        return RendezVousWidget(app=self)
        
    def record_score(self, score):
        """Update meta-data at the end of each game."""
        self.statistics.record_game(score, PLAYER)
        return self.achievements.check(score, PLAYER, self.statistics)

    def get_texture(self, card):
        """Return the appropriate texture to display."""
        if card is None or card.name is " ":
            #return Texture.create()
            region = self.loaded_deck.get_back_texture()
        else:
            region = self.loaded_deck.get_card_texture(card)
        return self.deck_texture.get_region(*region)

    def get_suit_texture(self, suit):
        """Return the appropriate texture to display."""
        if suit:
            region = self.loaded_deck.get_suit_texture(suit)
            return self.deck_texture.get_region(*region)
        else:
            return Image(os.path.join("data", "RVlogo.png")).texture
            
    def get_achievement_texture(self, achievement):
        """Return the appropriate texture to display."""
        region = self.achievements.get_achievement_texture(achievement)
        return self.achievement_texture.get_region(*region)
        
    def on_pause(self):
        return True
    def on_resume(self):
        pass


if __name__ == '__main__':
    RendezVousApp().run()
