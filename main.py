import os
import copy
import random

from kivy.clock import Clock
from kivy.app import App
from kivy.config import Config
from kivy.core.image import Image
from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.properties import ObjectProperty, ListProperty
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, FadeTransition, Screen
from kivy.uix.settings import SettingBoolean, SettingsWithNoMenu, SettingTitle
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.carousel import Carousel
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
from gui.screens.winner import WinnerScreen
from gui.settings import SettingSlider, SettingAIDifficulty, SettingButton
from gui.settings import BackgroundPicker
from gui.screens.settings import SettingsScreen
from gui.screens.deck import DeckCatalogScreen
from gui.screens.cards import DeckEditScreen
from gui.screens.statistics import StatisticsScreen
from gui.screens.achievements import AchievementsScreen
from gui.screens.powerups import PowerupScreen, CardSelect
from gui.screens.backgrounds import BackgroundCategoryDisplay
from gui.screens.kisses import KissesScreen
from gui.tutorial import GameTutorialScreen, FirstTutorialScreen, TutorialGameOver


__version__ = '0.8.3'


class RendezVousWidget(ScreenManager):

    """Arrange the screen - hand at the bottom, gameboard, score, etc.

    Attributes:
      game        -- behind-the-scenes RendezVousGame
      achieved    -- Achievements earned during the game
      dealer_play -- cards picked out for the dealer
      main        -- primary screen for gameplay

    """

    powerup_next_click = ObjectProperty(allownone=True)
    powerups_in_use = ListProperty()

    def on_powerup_next_click(self, instance, value):
        self.current_screen.gameboard.show_next_click_powerup(value)

    def on_powerups_in_use(self, instance, value):
        self.current_screen.gameboard.show_active_powerups(value)

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
        self.backgrounds = BackgroundCategoryDisplay(name='backgrounds',
            player_file=os.path.join(self.app.user_dir, "backgrounds.txt"))
        self.add_widget(self.backgrounds)
        self.add_widget(KissesScreen(name='kisses'))
        # 'stats' and 'cards' will be generated new on each view

        # Prepare the tutorial (if needed)
        if self.app.achievements.achieved == []:
            self._start_tutorial()

    def _start_tutorial(self):
        for hand in self.game.players:
            hand.deck.suits_only()
            hand.flush()
        self.switch_to(FirstTutorialScreen(game=self.game))

    def plant_special(self):
        """Replace special cards in deck, and place one into the hand."""
        special = random.choice(self.app.loaded_deck.specials[:5])
        special = self.app.loaded_deck.get_special(special.name)  # copy
        self.game.players[PLAYER].cards[8] = special
        self.game.players[PLAYER].deck.shuffle()
        self.game.players[DEALER].deck.shuffle()
        self.current_screen.hand_display.update()
        for slot in self.current_screen.hand_display.slots:
            slot.highlight(DARKEN)
        self.current_screen.hand_display.slots[8].highlight(BLANK)
        return special

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
        elif self.current == 'settings' or self.current == 'decks':
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
        elif screen == 'backgrounds':
            self.remove_widget(self.backgrounds)
            self.backgrounds = BackgroundCategoryDisplay(name='backgrounds',
                player_file=os.path.join(self.app.user_dir, "backgrounds.txt"))
            self.add_widget(self.backgrounds)

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
        self.current_screen.close_tray()

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
            cont = self.current_screen.gameboard.next_round_prompted()
            if not cont: return False

        # Some are consumed on the next click
        if powerup.type in (PowerupType.FLUSH_CARD, PowerupType.UNWAIT_CARD):
            self.powerup_next_click = powerup
            return

        # One requires a secondary popup
        if powerup.type == PowerupType.PLAY_CARD:
            if isinstance(powerup.value, Card):
                self.current_screen.gameboard.place_card(powerup.value)
                self.app.powerups.use(powerup)
                if self.game.board.is_full(PLAYER):
                    self._finish_play()
            else:
                popup = Popup(title='Select a card to play:')
                carousel = Carousel(direction='right')
                cards = [self.app.loaded_deck.get_card(name)
                         for name in self.app.powerups.cards()]
                for i in range(0, len(cards), 10):
                    layout = GridLayout(rows=2)
                    for card in cards[i:i+10]:
                        def play_sleeve_card(display, powerup, card, popup):
                            popup.dismiss()
                            powerup = copy.deepcopy(powerup)
                            powerup.value = card
                            card.from_powerup = powerup.name
                            self.use_powerup(powerup)
                        layout.add_widget(CardSelect(card=card,
                                            callback=play_sleeve_card,
                                            args=(powerup, card, popup)))
                    for i in range(len(cards), i+10):
                        layout.add_widget(CardSelect(card=None))
                    carousel.add_widget(layout)
                popup.add_widget(carousel)
                popup.open()
            return

        # Some are used right away and done with
        self.app.powerups.use(powerup)
        if powerup.type == PowerupType.FLUSH_HAND:
            for slot in self.current_screen.gameboard.slots[PLAYER]:
                self.card_touched(slot)  # return to hand
            self.current_screen.gameboard.update()
            self.game.players[PLAYER].flush()
            self.current_screen.hand_display.update()
            return

        # Some require more action later
        self.powerups_in_use.append(powerup)
        if powerup.type == PowerupType.SHOW_DEALER_HAND:
            self.current_screen.gameboard.show_dealer_hand(self.game.players[DEALER])
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
            if self._on_gameboard(card_display):
                if card_display.card is not None and not card_display.waited:
                    card_display.waited = True
                    p, i = self.current_screen.gameboard.find(card_display)
                    self.game.board._wait[p][i] = True
                    self.app.powerups.use(powerup)
                    return True
        elif powerup.type == PowerupType.FLUSH_CARD:
            if card_display.card is None: return False
            try:
                i = self.current_screen.hand_display.slots.index(card_display)
            except ValueError:
                return False
            self.game.players[PLAYER].pop(i)
            self.game.players[PLAYER].refill()
            self.current_screen.hand_display.update()
            self.app.powerups.use(powerup)
            return True
        elif powerup.type == PowerupType.UNWAIT_CARD:
            if card_display.waited:
                card_display.waited = False
                card_display.card = None
                p, i = self.current_screen.gameboard.find(card_display)
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
                self.current_screen.hand_display.update()
                self.current_screen.gameboard.update()
            elif powerup.type == PowerupType.GLOBAL_BUFF:
                for card in self.game.board[PLAYER]:
                    if card.suit != SpecialSuit.SPECIAL:
                        card.value += powerup.value
                self.current_screen.gameboard.update()
            elif powerup.type == PowerupType.GLOBAL_DEBUFF:
                for card in self.game.board[DEALER]:
                    if card.suit != SpecialSuit.SPECIAL:
                        card.value -= powerup.value
                self.current_screen.gameboard.update()

    def cleanup_powerups(self):
        """Provide any cleanup action for Powerups at the end of a round."""
        for powerup in self.powerups_in_use:
            if powerup.type == PowerupType.SHOW_DEALER_HAND:
                self.current_screen.gameboard.hide_dealer_hand()
        self.powerups_in_use = []

    def switch_hands(self):
        """Switch hands with the dealer."""
        self.game.players[PLAYER], self.game.players[DEALER] = self.game.players[DEALER], self.game.players[PLAYER]
        self.game.board.board[PLAYER], self.game.board.board[DEALER] = self.game.board.board[DEALER], self.game.board.board[PLAYER]
        self.game.board._wait[PLAYER], self.game.board._wait[DEALER] = self.game.board._wait[DEALER], self.game.board._wait[PLAYER]
        self.current_screen.hand_display.hand = self.game.players[PLAYER]
        try:
            self.current_screen.gameboard.dealer_hand.hand = self.game.players[DEALER]
        except: pass
        self.current_screen.hand_display.update()
        self.current_screen.gameboard.update()
        self._get_dealer_play()
        
    def is_game_screen(self):
        return (self.current == 'main' or self._in_tutorial())

    def _in_tutorial(self):
        return isinstance(self.current_screen, GameTutorialScreen)

    def card_touched(self, card_display):
        """Handle a touch to a displayed card."""
        if self._in_progress: return
        if self._in_tutorial():
            if self.current_screen.card_touched(): return
        elif not self.is_game_screen():
            return
        if self.game.round == 0:  # game over!
            return

        if self.next_click_for_powerup(card_display):
            return
        if self._end_of_round:
            if self._in_hand(card_display):
                cont = self.current_screen.gameboard.next_round_prompted()
                if not cont:
                    return
                # if not blocked, then go ahead and play this card also!

            elif self._on_gameboard(card_display):
                self.current_screen.gameboard.rescore_prompted()
                return
            
        if card_display.card is None: return
        
        if self._in_hand(card_display):
            self._place_on_board(card_display)
                    
        elif self._on_gameboard(card_display):
            self._remove_from_board(card_display)

    def _on_gameboard(self, card_display):
        """Return whether this display is part of the gameboard."""
        for side in self.current_screen.gameboard.slots:
            if card_display in side:
                return True
        return False

    def _in_hand(self, card_display):
        """Return whether this display is part of the player's hand."""
        return card_display in self.current_screen.hand_display.slots

    def card_dropped(self, card_display, card):
        """Allow dropping cards onto EMPTY board slots, or arranging hand.

        Arguments:
          card_display -- CardDisplay receiving the dropped card
          card -- Card in the display that was dragged originally

        """
        self.powerup_next_click = None
        # No dragging during scoring (except to tooltip; handled separately)
        if self._in_progress: return
        elif self._in_tutorial():
            if self.current_screen.card_touched(): return
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
        if self._on_gameboard(card_display):

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
        elif self._in_hand(card_display):
            loc = self.current_screen.hand_display
            hand_index = loc.slots.index(card_display)

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
            self._finish_play()

    def _finish_play(self):
        """Validate the play and complete the round."""
        failures = self.current_screen.gameboard.validate()
        for fcard in failures:
            self._return_to_source(fcard)
        if failures == []:
            self._in_progress = True
            self.current_screen.hand_display.confirm()
            self._play_dealer()

    def _remove_from_board(self, card_display):
        """Return a card from the board to the hand (or powerup tray)."""
        if card_display not in self.current_screen.gameboard.slots[PLAYER]:
            return
        index = self.current_screen.gameboard.slots[PLAYER].index(card_display)
        if self.game.board._wait[PLAYER][index]: return
        card = self.current_screen.gameboard.remove_card(card_display)
        self._return_to_source(card)

    def _return_to_source(self, card):
        """Return a card previously played to its proper source."""
        if 'from_powerup' in dir(card):
            powerup = self.app.powerups.find(str(card.from_powerup))
            powerup.value = card
            self.app.powerups.purchase(powerup)
            powerup.value = None
        else:
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
        if self._in_tutorial():
            if self.current_screen.all_cards_selected(): return
        callback = self._specials if then_score else self._mark_ready
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
        self.current_screen.gameboard.apply_specials(self.game,
                    self.current_screen.hand_display, self._score,
                    GameSettings.SPEED)

    def _score(self, then_prompt=True):
        """Score the round."""
        self._in_progress = True
        callback = self.prompt_for_next_round if then_prompt else self._mark_ready
        self.current_screen.gameboard.score_round(
                self.current_screen.scoreboard,
                callback=callback,
                timer=GameSettings.SPEED)

    def _mark_ready(self):
        """Let watchers know we are ready to continue."""
        self._in_progress = False

    def _reset_scoring(self):
        """Reset for another round of scoring."""
        self.game.score.scores = copy.deepcopy(self._backup_score)
        for card in self.game.board:
            card.reset()
        self.current_screen.gameboard.highlight(BLANK)
        self.current_screen.gameboard.update()
        self.current_screen.scoreboard.update()

    def replay_scoring(self):
        """Replay the scoring sequence at the user's request."""
        self._in_progress = True
        self._reset_scoring()
        Clock.schedule_once(lambda dt: self._specials(), GameSettings.SPEED)

    def replay_turn(self):
        """Replay the entire turn at the user's (powerup) request."""
        self.powerups_in_use = []
        self.game.board._wait = copy.deepcopy(self._backup_waits)
        self.game.score.scores = copy.deepcopy(self._backup_score)
        for i, hand in enumerate(self.game.players):
            waits = self.game.board._wait[i].count(True)
            hand.cards = hand.cards[:6-waits]
            for j, card in enumerate(self.game.board[i]):
                card.reset()
                if not self.game.board._wait[i][j]:
                    hand.cards.append(card)
                    self.game.board[i][j] = None
        self.current_screen.hand_display.update()
        self.current_screen.gameboard.highlight(BLANK)
        self.current_screen.gameboard.update()
        self.current_screen.scoreboard.update()
        self._get_dealer_play()

    def prompt_for_next_round(self):
        """Display the Replay and Continue buttons."""
        if self._in_tutorial():
            self.current_screen.scoring_complete()
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
        self.achieved += self.app.record_round(self.game.board)
        game_over = self.game.next_round()
        self._in_progress = False
        self._end_of_round = False
        if self._in_tutorial():
            if self.current_screen.next_round(self.game.round, game_over):
                return
        if game_over:
            self.achieved += self.app.record_score(self.game.score)
            if self._in_tutorial():
                self._winner = TutorialGameOver(score=self.game.score,
                                                achieved=self.achieved,
                                                name='winner')
            else:
                self._winner = WinnerScreen(self.game.score,
                                            self.achieved,
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

        self.current_screen.gameboard.highlight(None)
        self.current_screen.gameboard.update()
        self.current_screen.round_counter.round_number = self.game.round
        self.current_screen.hand_display.update()

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
        self.main.hand_display._played = []
        self.main.hand_display.update()
        self.main.scoreboard.update()
        self.main.round_counter.round_number = 1
        self.current = 'main'
        self.remove_widget(self._winner)
        self._in_progress = False
        self._end_of_round = False

    def replay_tutorial(self):
        popup = Popup(title="Replay Tutorial?", size_hint=(1, .5))
        layout = BoxLayout(orientation="vertical")
        layout.add_widget(Label(text="Would you like to repeat the tutorial experience?",
                                valign="middle", halign="center"))
        if GameSettings.NUM_ROUNDS != 20:
            layout.add_widget(Label(text="[b]Number of Rounds[/b] will be reset to [b]20[/b].",
                                    markup=True,
                                    valign="middle", halign="center"))
        buttons = BoxLayout()
        buttons.add_widget(Widget())
        buttons.add_widget(Button(text="YES",
                                  on_release=lambda *a: self._replay_tutorial(popup)))
        buttons.add_widget(Button(text="no",
                                  on_release=popup.dismiss))
        buttons.add_widget(Widget())
        layout.add_widget(buttons)
        popup.add_widget(layout)
        popup.open()

    def _replay_tutorial(self, popup):
        popup.dismiss()
        GameSettings.NUM_ROUNDS = 20
        self.game.new_game()
        self.achieved = []
        self.dealer_play = None
        self._in_progress = False
        self._end_of_round = False
        self._start_tutorial()


class RendezVousApp(App):

    """Main RendezVous App, with deck loaded."""

    loaded_deck = ObjectProperty()
    background = ObjectProperty(allownone=True)
    background_catalog = ObjectProperty(allownone=True)
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
        self._loaded_decks = {}
        self.load_deck(GameSettings.CURRENT_DECK)
        self.load_background(GameSettings.BACKGROUND)
        loader = Loader.image(self.achievements.image_file)
        loader.bind(on_load=self._achievements_loaded)
        self.powerups = Powerups(os.path.join(user_dir, "powerups.txt"))
        loader = Loader.image(self.powerups.image_file)
        loader.bind(on_load=self._powerups_loaded)
        loader = Loader.image(os.path.join("data", "Backgrounds.png"))
        loader.bind(on_load=self._backgrounds_loaded)


    # Persistent configuration

    def _load_sd_config(self):
        """Look for a saved config file if ours is gone."""
        local_config = "rendezvous.ini"
        if os.path.isfile(local_config): return
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


    # Loading
        
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

    def _background_loaded(self, loader):
        """Update the background texture when it's finished loading."""
        if loader.image.texture:
            self.background = loader.image.texture

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

    def _backgrounds_loaded(self, loader):
        """Update the background catalog when it's finished loading."""
        if loader.image.texture:
            self.background_catalog = loader.image.texture

    def build(self):
        return RendezVousWidget(app=self)


    # Customization

    def load_background(self, filename):
        """Load the named background."""
        GameSettings.BACKGROUND = filename
        if not os.path.isfile(filename):
            filename = os.path.join("data", "backgrounds", filename)
        loader = Loader.image(filename)
        loader.bind(on_load=self._background_loaded)

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
            if self.root._in_tutorial():
                update_deck(self.root.current_screen)


    # Game Features

    def purchase_background(self, filename, index, popup_):
        """Confirm the purchase of the given background."""
        if filename in self.root.backgrounds.purchased:
            popup_.dismiss()
            return self.load_background(filename)
        
        popup = Popup(title=filename[3:-4] + " Background")
        preview = BoxLayout(orientation="vertical")
        with preview.canvas.before:
            Color(1, 1, 1, 1)
            self.pr = Rectangle(source=os.path.join("data", "backgrounds",
                                                    filename))
        def update_popup(instance, value):
            self.pr.pos = instance.pos
            self.pr.size = instance.size
        preview.bind(pos=update_popup, size=update_popup)
        
        layout = BoxLayout(orientation="vertical", size_hint=(5, 2))
        with layout.canvas.before:
            Color(0, 0, 0, .25)
            self.lr = Rectangle()
        def update_layout(instance, value):
            self.lr.pos = instance.pos
            self.lr.size = instance.size
        layout.bind(pos=update_layout, size=update_layout)
        
        layout.add_widget(Label(text="Are you sure you would like to purchase this background for 5 kisses?",
                                valign="middle", halign="center",
                                size_hint=(1, 4)))
        buttons = BoxLayout()
        buttons.add_widget(Widget())
        buttons.add_widget(Button(text="YES", on_release=lambda x: self._purchase_background(filename, index, (popup_, popup))))
        buttons.add_widget(Button(text="no", on_release=popup.dismiss))
        buttons.add_widget(Widget())
        layout.add_widget(buttons)
        sideways = BoxLayout()
        sideways.add_widget(Widget())
        sideways.add_widget(layout)
        sideways.add_widget(Widget())
        preview.add_widget(Widget())
        preview.add_widget(sideways)
        preview.add_widget(Widget())
        popup.add_widget(preview)
        popup.open()

    def _purchase_background(self, filename, index, popups):
        """Purchase and load the given background."""
        for popup in popups:
            popup.dismiss()
        if not self.kisses.purchase(filename[:-4], 5):
            return
        self._load_currency()
        self.root.backgrounds.purchase(filename, index)
        self.load_background(filename)

    def purchase_deck(self, deck_entry):
        """Confirm the purchase of the given deck."""
        popup = Popup(title=deck_entry.name,
                      size_hint=(1, .5))
        layout = BoxLayout(orientation="vertical")
        layout.add_widget(Label(text="Are you sure you would like to purchase this deck for 15 kisses?",
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
        if not self.kisses.purchase(deck_entry.name, 15):
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
            self.kisses.earn(len([a for a in achieved if a.reward is None]),
                             "Extra achievement rewards.")
        self._load_currency()
        return achieved

    def record_round(self, board):
        """Check for achievements at the end of each round."""
        achieved = self.achievements.check_round(board, PLAYER)
        if achieved:
            self.kisses.earn(len(achieved), "Round achievement(s).")
            self.kisses.earn(len([a for a in achieved if a.reward is None]),
                             "Extra achievement rewards.")
            self._load_currency()
        return achieved

    def purchase_powerup(self, powerup, count=1):
        """Attempt to purchase a powerup; return boolean success."""
        if not self.winks.purchase(powerup, powerup.price * count):
            return False
        self.powerups.purchase(powerup, count)
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

    def get_bg_thumbnail(self, index):
        """Return the appropriate region of the background catalog."""
        index = int(index)
        region = (102 * int((index-1) / 16),
                  1024 - 64 * (int((index-1) % 16) + 1), 101, 63)
        try:
            return self.background_catalog.get_region(*region)
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
        try: config.add_section('Resets')
        except: pass
        config.set('Resets', 'REPLAY_TUTORIAL', 0)

    def on_config_change(self, config, section, key, value):
        """Handle special config cases."""
        key = key.upper()
        if key == 'NUM_ROUNDS':
            self.root.main.round_counter.max_round = int(value)
        elif key == 'SHOW_PRIVATE':
            self.root.rebuild_decks()
        elif key == 'REPLAY_TUTORIAL':
            if self.root is not None:
                self.root.replay_tutorial()

    def build_settings(self, settings):
        """Load the JSON file with settings details."""
        settings.on_config_change = lambda i, c, k, v: self.on_config_change(i, c, k, v)
        settings_file = os.path.join("gui", "settings.json")
        fp = open(settings_file, "r")
        try:
            settings.register_type('slider', SettingSlider)
            settings.register_type('customAI', SettingAIDifficulty)
            settings.register_type('button', SettingButton)
            settings.register_type('background', BackgroundPicker)
            settings.add_json_panel('Game Settings', self.config,
                                    data="\n".join(fp.readlines()))
            if self.deck_catalog.private:
                settings.interface.current_panel.add_widget(
                    SettingTitle(title="Debugging"))
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
