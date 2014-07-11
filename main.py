import os
import copy

from kivy.clock import Clock
from kivy.app import App
from kivy.config import Config
from kivy.core.image import Image
from kivy.graphics.texture import Texture
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, FadeTransition, Screen
from kivy.uix.settings import SettingBoolean, SettingsWithNoMenu
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.loader import Loader

from rendezvous import GameSettings, Currency, PowerupType, SpecialSuit
from rendezvous.deck import DeckDefinition, Card, DeckCatalog, DeckCatalogEntry
from rendezvous.gameplay import RendezVousGame
from rendezvous.statistics import Statistics
from rendezvous.achievements import AchievementList
from rendezvous.powerups import Powerups

from gui import DEALER, PLAYER
from gui.components import BLANK, DARKEN
from gui.components import ConfirmPopup
from gui.screens.home import HomeScreen
from gui.screens.game import GameScreen, RoundAchievementScreen
from gui.screens.tutorial import MainBoardTutorial, SidebarTutorial, TooltipTutorial
from gui.screens.winner import WinnerScreen
from gui.settings import SettingSlider, SettingAIDifficulty
from gui.screens.settings import SettingsScreen
from gui.screens.deck import DeckCatalogScreen
from gui.screens.cards import DeckEditScreen
from gui.screens.statistics import StatisticsScreen
from gui.screens.achievements import AchievementsScreen
from gui.screens.powerups import PowerupScreen


__version__ = '0.6.5'


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
        try:
            self.app = kwargs['app']
        except KeyError:
            self.app = App.get_running_app()

        # Prepare internal storage
        self.game = RendezVousGame(deck=self.app.loaded_deck,
                                   achievements=self.app.achievements)
        self.game.new_game()
        self._cards_played = []         #: hand indices played so far
        self.achieved = []              #: Achievements earned this game
        self.dealer_play = None         #: cards the dealer will play
        self._in_progress = False       #: currently scoring a round?
        self._end_of_round = False      #: currently paused after scoring?
        self.powerup_next_click = None  #: applies on the next card select
        self.powerups_in_use = []       #: applied this round

        # Prepare the screens
        self.home = HomeScreen(name='home')
        self.add_widget(self.home)
        self.main = GameScreen(game=self.game, name='main')
        self.add_widget(self.main)
        self.achieve = AchievementsScreen(achievements=self.app.achievements,
                                          name='achieve')
        self.add_widget(self.achieve)
        self.add_widget(SettingsScreen(name='settings'))
        self.decks = DeckCatalogScreen(catalog=self.app.deck_catalog,
                                       name='decks')
        self.add_widget(self.decks)
        self.add_widget(PowerupScreen(name='powerups'))
        # 'stats' and 'cards' will be generated new on each view

        # Prepare the tutorial (if needed)
        if self.app.achievements.achieved == []:
            self.switch_to(MainBoardTutorial(game=self.game,
                                             name='tutorial-hand'))
            self.current_screen.tutorial.title = "Welcome to RendezVous!"
            self.current_screen.tutorial.text = "This tutorial will walk you through your first game, introducing key concepts along the way. RendezVous is easy to play, but you will find the strategies to be endless!\n\nYour hand is displayed below. Each round, you will pick 4 cards to play, then your hand will be refilled to 10 again. Go ahead and pick your first four cards now.\n\n(Higher values are better!)"
            self.current_screen.tutorial.footer = "SELECT 4 CARDS BELOW"

    def rebuild_decks(self):
        """Rebuild the deck catalog screen (e.g. after catalog update)."""
        self.remove_widget(self.decks)
        self.decks = DeckCatalogScreen(catalog=self.app.deck_catalog,
                                       name='decks')
        self.add_widget(self.decks)

    def switcher(self, screen):
        """Handle a request to switch screens."""
        if isinstance(screen, Screen):
            screen = screen.name

        # Switching FROM something important?
        if self.current == 'cards':
            for hand in self.game.players:
                hand.deck.shuffle()
                if not hand.deck._cards:
                    return
                for card in hand:
                    if str(card) in hand.deck.definition.blocked_cards:
                        hand.remove(card)
                hand.refill()
        elif self.current == 'settings':
            self.app._save_sd_config()
        elif self.current == 'main':
            self.main.close_tray()

        # Switching TO something important?
        if (screen == 'main' and self.game.round == 0):
                self.play_again()
                return
        # ... screens that depend on a loaded texture
        elif screen == 'achieve' and self.app.deck_achievement_texture is None:
            return
        elif screen == 'powerups' and self.app.powerups_texture is None:
            return
        # ... screens that are generated fresh each time
        elif screen == 'stats':
            try: self.remove_widget(self.stats)
            except AttributeError: pass
            self.stats = StatisticsScreen(statistics=self.app.statistics,
                                          name='stats')
            self.switch_to(self.stats)
            return
        elif screen == 'cards':
            try: self.remove_widget(self.cards)
            except AttributeError: pass
            self.cards = DeckEditScreen(definition=self.app.loaded_deck,
                                        name='cards')
            self.switch_to(self.cards)
            return

        # Switch & auto-update
        self.current = screen
        try: self.current_screen.update()
        except AttributeError: pass

    def update_achievements(self):
        # Rebuild achievements screen from scratch
        self.remove_widget(self.achieve)
        self.achieve = AchievementsScreen(achievements=self.app.achievements,
                                          name='achieve')
        self.add_widget(self.achieve)
        if self.current == 'achieve':
            self.current = 'home'
            self.current = 'achieve'

    def cant_play(self):
        """Prompt the user to confirm that s/he can't play."""
        if self._in_progress: return
        if self._end_of_round:
            cont = self.current_screen.gameboard.next_round_prompted()
            if not cont:
                return
        popup = ConfirmPopup(title='Stuck?', callback=self._cant_play)
        popup.open()

    def _cant_play(self, popup):
        """Player is declared unable to make a move."""
        popup.dismiss()
        for slot in self.current_screen.gameboard.slots[PLAYER]:
            self.card_touched(slot)  # return to hand
        self.game.players[PLAYER].cant_play(PLAYER, self.game.score)
        self.current_screen.gameboard.update()
        self.current_screen.hand_display.update()
        self.current_screen.scoreboard.update()

    def use_powerup(self, powerup):
        self.main.close_tray()

        # Only certain ones can be used between rounds
        if powerup.type == PowerupType.WAIT_CARD:
            self.powerup_next_click = powerup
            return
        elif powerup.type == PowerupType.REPLAY_TURN:
            if self._end_of_round:
                self.app.powerups.use(powerup)
                self.replay_turn()
            return
        elif self._end_of_round:
            cont = self.main.gameboard.next_round_prompted()
            if not cont: return False

        # Some are consumed on the next click
        if powerup.type in (PowerupType.FLUSH_CARD, PowerupType.UNWAIT_CARD):
            self.powerup_next_click = powerup
            return

        # Some are used right away and done with
        self.app.powerups.use(powerup)
        if powerup.type == PowerupType.FLUSH_HAND:
            for slot in self.current_screen.gameboard.slots[PLAYER]:
                self.card_touched(slot)  # return to hand
            self.main.gameboard.update()
            self.game.players[PLAYER].flush()
            self.main.hand_display.update()
            return

        # Some require more action later
        self.powerups_in_use.append(powerup)
        if powerup.type == PowerupType.SHOW_DEALER_HAND:
            self.main.gameboard.show_dealer_hand(self.game.players[DEALER])
        elif powerup.type == PowerupType.SHOW_DEALER_PLAY:
            if self.dealer_play is None:
                self._get_dealer_play()
            self._play_dealer(then_score=False)
        elif powerup.type == PowerupType.SWITCH_PLAY:
            self.switch_hands()
            self._get_dealer_play()

        # Some powerups' only action is later
        #elif powerup.type in (PowerupType.GLOBAL_BUFF,
        #                      PowerupType.GLOBAL_DEBUFF):
        #    pass

    def next_click_for_powerup(self, card_display):
        """See if this is a powerup selection; return True to consume click."""
        if self.powerup_next_click is None:
            return False
        powerup = self.powerup_next_click
        self.powerup_next_click = None
        
        if powerup.type == PowerupType.WAIT_CARD:
            if card_display.parent.parent == self.main.gameboard:
                if card_display.card is not None and not card_display.waited:
                    card_display.waited = True
                    p, i = self.main.gameboard.find(card_display)
                    self.game.board._wait[p][i] = True
                    self.app.powerups.use(powerup)
                    return True
        elif powerup.type == PowerupType.FLUSH_CARD:
            if card_display.card is None: return False
            try:
                i = self.main.hand_display.slots.index(card_display)
            except ValueError:
                return False
            self.game.players[PLAYER].pop(i)
            self.game.players[PLAYER].refill()
            self.main.hand_display.update()
            self.app.powerups.use(powerup)
            return True
        elif powerup.type == PowerupType.UNWAIT_CARD:
            if card_display.waited:
                card_display.waited = False
                card_display.card = None
                p, i = self.main.gameboard.find(card_display)
                self.game.board._wait[p][i] = False
                self.game.board.board[p][i] = None
                self.app.powerups.use(powerup)
                return True
        return False

    def prescore_powerups(self):
        """Provide any necessary powerup boosts before scoring begins."""
        for powerup in reversed(self.powerups_in_use):
            if powerup.type == PowerupType.SWITCH_PLAY:
                self.switch_hands()
                self.dealer_play = None  # too soon!
                self.powerups_in_use.remove(powerup)
                self.main.hand_display.update()
                self.main.gameboard.update()
            elif powerup.type == PowerupType.GLOBAL_BUFF:
                for card in self.game.board[PLAYER]:
                    if card.suit != SpecialSuit.SPECIAL:
                        card.value += powerup.value
                self.main.gameboard.update()
            elif powerup.type == PowerupType.GLOBAL_DEBUFF:
                for card in self.game.board[DEALER]:
                    if card.suit != SpecialSuit.SPECIAL:
                        card.value -= powerup.value
                self.main.gameboard.update()

    def cleanup_powerups(self):
        """Provide any cleanup action for Powerups at the end of a round."""
        for powerup in self.powerups_in_use:
            if powerup.type == PowerupType.SHOW_DEALER_HAND:
                self.main.gameboard.hide_dealer_hand()
        self.powerups_in_use = []

    def switch_hands(self):
        """Switch hands with the dealer."""
        self.game.players[PLAYER], self.game.players[DEALER] = self.game.players[DEALER], self.game.players[PLAYER]
        self.game.board.board[PLAYER], self.game.board.board[DEALER] = self.game.board.board[DEALER], self.game.board.board[PLAYER]
        self.game.board._wait[PLAYER], self.game.board._wait[DEALER] = self.game.board._wait[DEALER], self.game.board._wait[PLAYER]
        self.main.hand_display.hand = self.game.players[PLAYER]
        try:
            self.main.gameboard.dealer_hand.hand = self.game.players[DEALER]
        except: pass
        self.main.hand_display.update()
        self.main.gameboard.update()
        self._get_dealer_play()
        
    def is_game_screen(self):
        return self.current == 'main' or self.current.startswith('tutorial')

    def card_touched(self, card_display):
        """Handle a touch to a displayed card."""
        if self._in_progress: return
        if self.current == 'tutorial-tooltip':
            for slot in self.current_screen.hand_display.slots:
                slot.highlight(BLANK)
        elif not self.is_game_screen():
            return
        if self.game.round == 0:  # game over!
            return

        if self.next_click_for_powerup(card_display):
            return
        loc = card_display.parent
        if self._end_of_round:
            if loc is self.current_screen.hand_display:
                cont = self.current_screen.gameboard.next_round_prompted()
                if not cont:
                    return
                # if not blocked, then go ahead and play this card also!

            elif loc.parent is self.current_screen.gameboard:
                self.current_screen.gameboard.rescore_prompted()
                return
            
        if card_display.card is None: return
        
        if loc is self.current_screen.hand_display:
            self._place_on_board(card_display)
                    
        elif loc.parent is self.current_screen.gameboard:
            self._remove_from_board(card_display)

    def card_dropped(self, card_display, card):
        """Allow dropping cards onto EMPTY board slots, or arranging hand.

        Arguments:
          card_display -- CardDisplay receiving the dropped card
          card -- Card in the display that was dragged originally

        """
        self.powerup_next_click = None
        # No dragging during scoring (except to tooltip; handled separately)
        if self._in_progress: return
        elif not self.is_game_screen():
            return
        
        # Only drag actual cards (no empty slots)
        if card is None: return

        # Auto-continue on the first play after scoring
        if self._end_of_round:
            cont = self.current_screen.gameboard.next_round_prompted()
            if not cont:
                return

        # Dropping onto the gameboard?
        loc = card_display.parent
        if loc.parent is self.current_screen.gameboard:

            # Never drop onto enemy slots (or held slots)
            if card_display not in self.current_screen.gameboard.slots[PLAYER]:
                return
            board_index = self.current_screen.gameboard.slots[PLAYER].index(card_display)
            if self.game.board._wait[PLAYER][board_index]:
                return

            # See if it's coming from the board as well (and not held)
            from_index = None
            for i, slot in enumerate(self.current_screen.gameboard.slots[PLAYER]):
                if slot.card is card:
                    from_index = i
                    if self.game.board._wait[PLAYER][from_index]:
                        return
                    break

            # Dropping onto a filled slot?
            if card_display.card is not None:

                # Allow swapping played cards
                if from_index is not None:
                    self.current_screen.gameboard.swap(from_index, board_index)
                    return

                # Or remove it
                self._remove_from_board(card_display)

            # Relocate on the board
            if from_index is not None:
                from_display = self.current_screen.gameboard.slots[PLAYER][from_index]
                self.current_screen.gameboard.remove_card(from_display)
                self.current_screen.gameboard.place_card(card, board_index)

            # Place into slot from hand
            elif card in self.game.players[PLAYER].cards:
                try:  # might still be a duplicate...
                    self._place_on_board(card, board_index)
                except ValueError:
                    return

        # Dropping onto player's hand?
        elif loc is self.current_screen.hand_display:
            hand_index = self.current_screen.hand_display.slots.index(card_display)

            # From the board (not held)
            if loc.is_played(card):
                for slot in self.current_screen.gameboard.slots[PLAYER]:
                    if slot.card is card:
                        self._remove_from_board(slot)
                if card_display.card is not card:
                    self.current_screen.hand_display.swap(card, card_display)

            # Or swap cards in hand
            elif card in self.game.players[PLAYER]:
                loc.swap(card_display, card)

    def _place_on_board(self, card_or_display, index=None):
        """Place a card on the board from the hand."""
        if self.dealer_play is None:
            self._get_dealer_play()
        if not self.game.board.is_full(PLAYER):
            card = self.current_screen.hand_display.get(card_or_display)
            self.current_screen.gameboard.place_card(card, index)
        if self.game.board.is_full(PLAYER):
                failures = self.current_screen.gameboard.validate()
                for fcard in failures:
                    self.current_screen.hand_display.return_card(fcard)
                if failures == []:
                    self._in_progress = True
                    self.current_screen.hand_display.confirm()
                    self._play_dealer()

    def _remove_from_board(self, card_display):
        """Return a card from the board to the hand."""
        if card_display not in self.current_screen.gameboard.slots[PLAYER]:
            return
        index = self.current_screen.gameboard.slots[PLAYER].index(card_display)
        if self.game.board._wait[PLAYER][index]: return
        card = self.current_screen.gameboard.remove_card(card_display)
        self.current_screen.hand_display.return_card(card)

    def _get_dealer_play(self):
        if GameSettings.AI_DIFFICULTY == 1:
            self.dealer_play = self.game.players[DEALER].AI_easy(
                                    DEALER, self.game.board, self.game.score)
        else:
            self.dealer_play = self.game.players[DEALER].AI_hard(
                                    DEALER, self.game.board, self.game.score)

    def _play_dealer(self, then_score=True):
        """Place the dealer's selected cards on the board."""
        if GameSettings.AI_DIFFICULTY == 3:
            for powerup in self.powerups_in_use:
                if powerup.type == PowerupType.SHOW_DEALER_PLAY:
                    break
            else:
                self._get_dealer_play()
        if self.current == 'tutorial-hand':
            self.switch_to(SidebarTutorial(game=self.game,
                                           name='tutorial-board'))
            self.current_screen.tutorial.title = "Now it's the\ndealer's turn!"
            self.current_screen.tutorial.text = "The dealer has a hand of 10 cards, just like you, and will select four cards to play against yours each round.\n\nEach card you play is compared against the card directly above it to determine your score."
            self.current_screen.button = Button(text="Continue")
            self.current_screen.button.bind(on_press=self.score_tutorial)
        elif self.current == 'tutorial-tooltip':
            self.switch_to(GameScreen(game=self.game,
                                      name='tutorial-done'))
        callback = self._specials if then_score else None
        self.current_screen.gameboard.play_dealer(self.dealer_play,
                                                  callback=callback,
                                                  timer=GameSettings.SPEED)
        for card in self.dealer_play:
            self.game.players[DEALER].remove(card)
        self.dealer_play = None
        self._backup_score = copy.deepcopy(self.game.score.scores)
        self._backup_waits = copy.deepcopy(self.game.board._wait)
        
    def _specials(self):
        """Apply all specials."""
        self.prescore_powerups()
        self.game.board.clear_wait()
        if self.current == 'tutorial-board':
            self._in_progress = False
            return  # until continue is pressed
        self.current_screen.gameboard.apply_specials(self.game,
                    self.current_screen.hand_display, self._score,
                    GameSettings.SPEED)

    def score_tutorial(self, *args):
        """Continue with scoring from tutorial-board."""
        if self._in_progress: return
        self._in_progress = True
        self.switch_to(SidebarTutorial(game=self.game, name='tutorial-score'))
        self.current_screen.tutorial.title = "Scoring"
        self.current_screen.tutorial.text = "There are five suits in the deck, and you are scored in each suit.\n\nA win earns you 10 points in the suit you played, and 10 points in the dealer's suit. A loss costs you 10 points in your suit only.\n\nAs the round is scored, the highlighting will help you see who won each match-up."
        self._score()

    def _score(self):
        """Score the round."""
        self.current_screen.gameboard.score_round(
                self.current_screen.scoreboard,
                callback=self.prompt_for_next_round,
                timer=GameSettings.SPEED)

    def replay_scoring(self):
        """Replay the scoring sequence at the user's request."""
        self._in_progress = True
        self.game.score.scores = self._backup_score
        for card in self.game.board:
            card.reset()
        self.current_screen.gameboard.highlight(BLANK)
        self.current_screen.gameboard.update()
        self.current_screen.scoreboard.update()
        Clock.schedule_once(lambda dt: self._specials(), GameSettings.SPEED)

    def replay_turn(self):
        """Replay the entire turn at the user's (powerup) request."""
        self.powerups_in_use = []
        self.game.board._wait = self._backup_waits
        self.game.score.scores = self._backup_score
        for i, hand in enumerate(self.game.players):
            waits = self.game.board._wait[i].count(True)
            hand.cards = hand.cards[:6-waits]
            for j, card in enumerate(self.game.board[i]):
                card.reset()
                if not self.game.board._wait[i][j]:
                    hand.cards.append(card)
                    self.game.board[i][j] = None
        self.main.hand_display.update()
        self.main.gameboard.highlight(BLANK)
        self.main.gameboard.update()
        self.main.scoreboard.update()
        self._get_dealer_play()

    def prompt_for_next_round(self):
        """Display the Replay and Continue buttons."""
        if self.game.round >= GameSettings.NUM_ROUNDS:
            self.current_screen.hand_display.empty()
        else:
            self.game.players[PLAYER].refill()
            self.current_screen.hand_display.update()
        self._in_progress = False
        self._end_of_round = True
        self.current_screen.gameboard.prompt_for_next_round()

    def next_round(self):
        """Clear the board for the next round. Return whether to continue."""
        self.cleanup_powerups()
        if self.current == 'tutorial-score':
            self.switch_to(TooltipTutorial(game=self.game,
                                           name='tutorial-continue'))
            self.current_screen.tutorial.title = "The Scoreboard"
            self.current_screen.tutorial.text= "Your score in each suit is shown above, to the left. The dealer's score is to the right.\n\nAfter %s rounds, the winner is the one leading in the most suits." % GameSettings.NUM_ROUNDS
            self.current_screen.tutorial.footer = "Play a few rounds!"
        self.achieved += self.app.record_round(self.game.board)
        game_over = self.game.next_round()
        if game_over:
            self.achieved += self.app.record_score(self.game.score)
            self._winner = WinnerScreen(self.game.score, self.achieved,
                                        name='winner')
            self.switch_to(self._winner)
            self.achieved = []
            self.game.round = 0  # mark GAME OVER to trigger replay
            return False
        elif self.game.board.is_full(PLAYER):
            self.current_screen.gameboard.highlight(BLANK)
            self.current_screen.gameboard.update()
            self._get_dealer_play()
            self._play_dealer()
            return False

        if self.current == 'tutorial-continue' and self.game.round >= 10:
            special = self.app.loaded_deck.specials[0]
            special = self.app.loaded_deck.get_special(special.name)  # copy
            self.game.players[PLAYER].cards[8] = special
            self.app.achievements.achieved.append("Tutorial")
            self.game.players[PLAYER].deck.shuffle()
            self.switch_to(MainBoardTutorial(game=self.game,
                                             name='tutorial-tooltip'))
            self.current_screen.tutorial.title = "Introducing Special Cards"
            self.current_screen.tutorial.text = "In addition to the five normal suits, you will sometimes get special cards in your hand. These can only be played when certain conditions are met, but they have the power to affect the other cards you play, or even the dealer's cards.\n\nYou drew a %s card! Drag your new special card onto the tooltip display below the scoreboard to read about what it does and how to use it.\n\nThere are many different types of special cards. The best cards are unlocked by completing RendezVous Achievements - and when you download a custom deck, it will come with its own unique Special Cards!" % special
            self.current_screen.tutorial.footer = "When you are ready to continue, select your 4 cards for this round."
            for slot in self.current_screen.hand_display.slots:
                slot.highlight(DARKEN)
            self.current_screen.hand_display.slots[8].highlight(BLANK)
        else:
            self.current_screen.gameboard.highlight(None)
            self.current_screen.gameboard.update()
        self.current_screen.round_counter.round_number = self.game.round
        self.current_screen.hand_display.update()
        self._in_progress = False
        self._end_of_round = False

        if self.achieved:
            self.switch_to(RoundAchievementScreen(self.achieved,
                                                  name='unlocks'))
            self.achieved = []
            return False
        return True

    def play_again(self):
        """Start a new game."""
        self.game.new_game()
        self.achieved = []
        self.main.gameboard.highlight(None)
        self.main.gameboard.update()
        self.main.hand_display.update()
        self.main.scoreboard.update()
        self.main.round_counter.round_number = 1
        self.current = 'main'
        self.remove_widget(self._winner)
        self._in_progress = False
        self._end_of_round = False


class RendezVousApp(App):

    """Main RendezVous App, with deck loaded."""

    loaded_deck = ObjectProperty()
    deck_texture = ObjectProperty(allownone=True)
    achievement_texture = ObjectProperty(allownone=True)
    powerups_texture = ObjectProperty(allownone=True)
    winks = ObjectProperty()
    kisses = ObjectProperty()

    def __init__(self, **kwargs):
        """Load the deck image and create the RendezVousWidget."""
        App.__init__(self, **kwargs)
        self._load_sd_config()
        self.icon = os.path.join("data", "RVlogo.ico")
        self.icon_png = os.path.join("data", "RVlogo.png")
        self.settings_cls = SettingsWithNoMenu
        user_dir = self.user_data_dir
        if not os.path.isdir(user_dir):
            user_dir = "player"
        self.deck_catalog = DeckCatalog(os.path.join(user_dir, "decks.txt"))
        if self.deck_catalog.purchased(GameSettings.CURRENT_DECK) is None:
            GameSettings.CURRENT_DECK = "Standard"
        self._preload_home_screen()
        self._load_currency(user_dir)
        self.statistics = Statistics(os.path.join(user_dir, "stats.txt"))
        self.achievements = AchievementList(os.path.join(user_dir, "unlocked.txt"))
        loader = Loader.image(self.achievements.image_file)
        loader.bind(on_load=self._achievements_loaded)
        self.powerups = Powerups(os.path.join(user_dir, "powerups.txt"))
        loader = Loader.image(self.powerups.image_file)
        loader.bind(on_load=self._powerups_loaded)
        self._loaded_decks = {}
        self.load_deck(GameSettings.CURRENT_DECK)

    def _load_sd_config(self):
        """Look for a saved config file if ours is gone."""
        local_config = "rendezvous.ini"
        sd_config = os.path.join(self.user_data_dir, "rendezvous.ini")
        if os.path.isfile(sd_config):
            import shutil
            shutil.copyfile(sd_config, local_config)

    def _save_sd_config(self):
        """Save the config file to the normal data location."""
        local_config = "rendezvous.ini"
        if not os.path.isfile(local_config): return
        if os.path.isdir(self.user_data_dir):
            sd_config = os.path.join(self.user_data_dir, "rendezvous.ini")
            import shutil
            shutil.copyfile(local_config, sd_config)
        
    def _preload_home_screen(self):
        """Prioritize loading of images for the home screen."""
        deck = self.deck_catalog[GameSettings.CURRENT_DECK]
        deck.hand_texture = Image(deck.hand).texture

    def _load_currency(self, directory=None):
        """Force a reload when needed."""
        if directory is not None:
            self.user_dir = directory
        self.winks = Currency('wink',
                     "In a secret rendezvous, a wink can tip your hand!",
                     self.user_dir)
        self.kisses = Currency('kiss',
                      "When lovers rendezvous, a simple kiss is priceless.",
                      self.user_dir)

    def _image_loaded(self, loader):
        """Update the deck image when it's finished loading."""
        if loader.image.texture:
            self.deck_texture = loader.image.texture

    def _achievements_loaded(self, loader):
        """Update the standard achievement image when it's finished loading."""
        if loader.image.texture:
            self.achievement_texture = loader.image.texture

    def _deck_achievements_loaded(self, loader):
        """Update the deck's achievement image when it's finished loading."""
        if loader.image.texture:
            self.deck_achievement_texture = loader.image.texture
            if self.root is not None:
                self.root.update_achievements()

    def _powerups_loaded(self, loader):
        """Update the powerups image when it's finished loading."""
        if loader.image.texture:
            self.powerups_texture = loader.image.texture

    def build(self):
        return RendezVousWidget(app=self)

    def load_deck(self, deck_base):
        """Prepare the given deck for play."""
        if self.loaded_deck is not None:

            # Don't reload the same deck
            if self.loaded_deck.base_filename == deck_base:
                return

            # Cache current deck's details
            current = self.loaded_deck.base_filename
            if current not in self._loaded_decks:
                self._loaded_decks[current] = {}
                self._loaded_decks[current]['deck'] = self.loaded_deck
                self._loaded_decks[current]['texture'] = self.deck_texture
                self._loaded_decks[current]['achtexture'] = self.deck_achievement_texture

        # Always update the Achievements from the files
        self.achievements.load_deck(deck_base)

        # Read from cache, if available
        GameSettings.CURRENT_DECK = deck_base
        if deck_base in self._loaded_decks:
            self.loaded_deck  = self._loaded_decks[deck_base]['deck']
            self.deck_texture = self._loaded_decks[deck_base]['texture']
            self.deck_achievement_texture = self._loaded_decks[deck_base]['achtexture']
            if self.root is not None:
                self.root.update_achievements()
            self._update_deck()
            return

        # Load the deck from scratch
        self._load_deck(deck_base)

    def _load_deck(self, deck_base):
        """Load the deck from its hard drive files."""
        self.loaded_deck = DeckDefinition(deck_base)
        self.deck_texture = None
        loader = Loader.image(self.loaded_deck.img_file)
        loader.bind(on_load=self._image_loaded)
        self.deck_achievement_texture = None
        if os.path.exists(self.achievements.deck_image_file):
            loader = Loader.image(self.achievements.deck_image_file)
            loader.bind(on_load=self._deck_achievements_loaded)
        else:
            self.deck_achievement_texture = Texture.create()
        self._update_deck()

    def _update_deck(self):
        """Update the game and screens to use the newly loaded deck."""
        def update_deck(screen):
            screen.gameboard.update()
            screen.hand_display.update()
            screen.scoreboard.update_suits()
            screen.tooltip.card = screen.tooltip.DUMMY_CARD
            
        if self.root:
            self.root.game.load_deck(self.loaded_deck)
            update_deck(self.root.main)
            if self.root.current[:7] == 'tutorial':
                update_deck(self.root.current_screen)

    def purchase_deck(self, deck_entry):
        """Confirm the purchase of the given deck."""
        popup = Popup(title=deck_entry.name,
                      size_hint=(1, .5))
        layout = BoxLayout(orientation="vertical")
        layout.add_widget(Label(text="Are you sure you would like to purchase this deck for 10 kisses?",
                                valign="middle", halign="center"))
        buttons = BoxLayout()
        buttons.add_widget(Widget())
        buttons.add_widget(Button(text="YES", on_release=lambda x: self._purchase_deck(deck_entry, popup)))
        buttons.add_widget(Button(text="no", on_release=popup.dismiss))
        buttons.add_widget(Widget())
        layout.add_widget(buttons)
        popup.add_widget(layout)
        popup.open()

    def _purchase_deck(self, deck_entry, popup):
        """Purchase and load the given deck."""
        popup.dismiss()
        if not self.kisses.purchase(deck_entry.name, 10):
            return
        self._load_currency()
        self.deck_catalog.purchase(deck_entry)
        self.load_deck(deck_entry.base_filename)
        self.root.switcher('home')
        
    def record_score(self, score):
        """Update meta-data at the end of each game."""
        self.statistics.record_game(self.loaded_deck.base_filename, score, PLAYER)
        self.winks.earn(len(score.wins(PLAYER)), "Win suits.")
        if len(score.wins(PLAYER)) > len(score.wins(DEALER)):
            self.winks.earn(1, "Win the game.")
        achieved = self.achievements.check(score, PLAYER, self.statistics)
        if achieved:
            self.kisses.earn(len(achieved), "Game achievement(s).")
        self._load_currency()
        return achieved

    def record_round(self, board):
        """Check for achievements at the end of each round."""
        achieved = self.achievements.check_round(board, PLAYER)
        if achieved:
            self.kisses.earn(len(achieved), "Round achievement(s).")
            self._load_currency()
        return achieved

    def purchase_powerup(self, powerup):
        """Attempt to purchase a powerup; return boolean success."""
        if not self.winks.purchase(powerup, powerup.price):
            return False
        self.powerups.purchase(powerup)
        self._load_currency()
        return True

    # Manage deck images

    def get_texture(self, card):
        """Return the appropriate texture to display."""
        try:
            if str(card) == "HIDDEN":
                region = self.loaded_deck.get_locked_texture()
            elif str(card) == "WAIT":
                region = self.loaded_deck.get_wait_texture()
            elif card is None or str(card) is " ":
                return Texture.create()
                #region = self.loaded_deck.get_back_texture()
            elif isinstance(card, DeckCatalogEntry):
                return card.texture
            elif isinstance(card, str):
                return self.get_texture(self.loaded_deck.get_special(card))
            else:
                region = self.loaded_deck.get_card_texture(card)
            return self.deck_texture.get_region(*region)
        except:
            return Texture.create()

    def get_suit_texture(self, suit):
        """Return the appropriate texture to display."""
        if suit == "WINK":
            return Image("atlas://gui/homescreen/wink").texture
        try:
            if suit:
                region = self.loaded_deck.get_suit_texture(suit)
                return self.deck_texture.get_region(*region)
            else:
                return Image(os.path.join("data", "RVlogo.png")).texture
        except:
            return Texture.create()
        
    def get_dealer_texture(self, *args):
        """Return the appropriate dealer texture to display."""
        try:
            region = self.loaded_deck.get_dealer_texture(*args)
            return self.deck_texture.get_region(*region)
        except:
            return Texture.create()
            
    def get_achievement_texture(self, achievement):
        """Return the appropriate texture to display."""
        if str(achievement) == "KISS":
            return Image("atlas://gui/homescreen/kiss").texture
        try:
            region = self.achievements.get_achievement_texture(achievement)
            if self.achievements.deck_specific(achievement):
                return self.deck_achievement_texture.get_region(*region)
            return self.achievement_texture.get_region(*region)
        except:
            return Texture.create()

    def get_powerup_texture(self, powerup):
        """Return the appropriate texture to display."""
        try:
            region = self.powerups.get_powerup_texture(powerup)
            return self.powerups_texture.get_region(*region)
        except:
            return Texture.create()


    # Allow automatic pause and resume when switching apps
    
    def on_pause(self):
        return True
    def on_resume(self):
        pass


    # Manage settings panel

    def get_application_config(self):
        """Share a config file with GameSettings."""
        return GameSettings.filename

    def build_config(self, config):
        """Automatically read the config file."""
        config.read(self.get_application_config())

    def on_config_change(self, config, section, key, value):
        """Handle special config cases."""
        key = key.upper()
        if key == 'NUM_ROUNDS':
            self.root.main.round_counter.max_round = int(value)
        elif key == 'SHOW_PRIVATE':
            self.root.rebuild_decks()

    def build_settings(self, settings):
        """Load the JSON file with settings details."""
        settings.on_config_change = lambda i, c, k, v: self.on_config_change(i, c, k, v)
        settings_file = os.path.join("gui", "settings.json")
        fp = open(settings_file, "r")
        try:
            settings.register_type('slider', SettingSlider)
            settings.register_type('customAI', SettingAIDifficulty)
            settings.add_json_panel('Game Settings', self.config,
                                    data="\n".join(fp.readlines()))
            if self.deck_catalog.private:
                settings.interface.current_panel.add_widget(
                    SettingBoolean(panel=settings.interface.current_panel,
                                   title="Show Private Decks",
                                   desc="Include private decks in the deck catalog.",
                                   section="DEFAULT",
                                   key="show_private"))
        finally:
            fp.close()

    # (ScreenManager handles custom settings display)
    def display_settings(self, settings):
        self.root.switcher('settings')
    def close_settings(self, *args):
        pass


if __name__ == '__main__':
    RendezVousApp().run()
