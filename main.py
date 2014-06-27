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
from kivy.loader import Loader

from rendezvous import GameSettings
from rendezvous.deck import DeckDefinition, Card, DeckCatalog, DeckCatalogEntry
from rendezvous.gameplay import RendezVousGame
from rendezvous.statistics import Statistics
from rendezvous.achievements import AchievementList

from gui import DEALER, PLAYER
from gui.components import BLANK, DARKEN
from gui.screens.home import HomeScreen
from gui.screens.game import GameScreen, WinnerScreen
from gui.screens.tutorial import MainBoardTutorial, SidebarTutorial, TooltipTutorial
from gui.settings import SettingSlider, SettingAIDifficulty
from gui.screens.achievements import AchievementsScreen
from gui.screens.settings import SettingsScreen
from gui.screens.deck import DeckCatalogScreen
from gui.screens.statistics import StatisticsScreen


__version__ = '0.5.6'


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
        self._cards_played = []    #: hand indices played so far
        self.achieved = []         #: Achievements earned this game
        self.dealer_play = None    #: cards the dealer will play
        self._in_progress = False  #: currently scoring a round?
        self._end_of_round = False #: currently paused after scoring?

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
        # 'stats' will be generated new on each view

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
        if (screen == 'main' and self.game.round == 0):
                self.play_again()
                return
        elif screen == 'achieve' and self.app.deck_achievement_texture is None:
            return
        elif screen == 'stats':
            # Force update each time
            try: self.remove_widget(self.stats)
            except AttributeError: pass
            self.stats = StatisticsScreen(statistics=self.app.statistics,
                                          name='stats')
            self.switch_to(self.stats)
            return
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
        """Player is declared unable to make a move."""
        for slot in self.current_screen.gameboard.slots[PLAYER]:
            self.card_touched(slot)  # return to hand
        self.game.players[PLAYER].cant_play(PLAYER, self.game.score)
        self.current_screen.gameboard.update()
        self.current_screen.hand_display.update()
        self.current_screen.scoreboard.update()

    def card_touched(self, card_display):
        """Handle a touch to a displayed card."""
        if self._in_progress: return
        if self.current == 'tutorial-tooltip':
            for slot in self.current_screen.hand_display.slots:
                slot.highlight(BLANK)
                
        if self._end_of_round:
            cont = self.current_screen.gameboard.next_round_prompted()
            if not cont:
                return
            
        if card_display.card is None: return
        
        loc = card_display.parent
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
        # No dragging during scoring (except to tooltip; handled separately)
        if self._in_progress: return
        
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

    def _play_dealer(self):
        """Place the dealer's selected cards on the board."""
        if GameSettings.AI_DIFFICULTY == 3:
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
        self.current_screen.gameboard.play_dealer(self.dealer_play,
                                                  callback=self._specials,
                                                  timer=GameSettings.SPEED)
        for card in self.dealer_play:
            self.game.players[DEALER].remove(card)
        self.dealer_play = None
        
    def _specials(self):
        """Apply all specials."""
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
        self._backup_score = copy.deepcopy(self.game.score.scores)
        self.current_screen.gameboard.score_round(
                self.current_screen.scoreboard,
                callback=self.prompt_for_next_round,
                timer=GameSettings.SPEED)

    def replay_scoring(self):
        """Replay the scoring sequence at the user's request."""
        self.game.score.scores = self._backup_score
        for card in self.game.board:
            card.reset()
        self.current_screen.gameboard.highlight(BLANK)
        self.current_screen.gameboard.update()
        self.current_screen.scoreboard.update()
        Clock.schedule_once(lambda dt: self._specials(), GameSettings.SPEED)

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
            self.game.round = 0  # mark GAME OVER to trigger replay
            return False
        elif self.game.board.is_full(PLAYER):
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

    def __init__(self, **kwargs):
        """Load the deck image and create the RendezVousWidget."""
        App.__init__(self, **kwargs)
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
        self.statistics = Statistics(os.path.join(user_dir, "stats.txt"))
        self.achievements = AchievementList(os.path.join(user_dir, "unlocked.txt"))
        loader = Loader.image(self.achievements.image_file)
        loader.bind(on_load=self._achievements_loaded)
        self._loaded_decks = {}
        self.load_deck(GameSettings.CURRENT_DECK)

    def _preload_home_screen(self):
        """Prioritize loading of images for the home screen."""
        deck = self.deck_catalog[GameSettings.CURRENT_DECK]
        deck.hand_texture = Image(deck.hand).texture

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
        loader = Loader.image(self.achievements.deck_image_file)
        loader.bind(on_load=self._deck_achievements_loaded)
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
        """Purchase and load the given deck."""
        self.deck_catalog.purchase(deck_entry)
        self.load_deck(deck_entry.base_filename)
        self.root.switcher('home')
        
    def record_score(self, score):
        """Update meta-data at the end of each game."""
        self.statistics.record_game(self.loaded_deck.base_filename, score, PLAYER)
        return self.achievements.check(score, PLAYER, self.statistics)

    def record_round(self, board):
        """Check for achievements at the end of each round."""
        return self.achievements.check_round(board, PLAYER)


    # Manage deck images

    def get_texture(self, card):
        """Return the appropriate texture to display."""
        try:
            if card == "HIDDEN":
                region = self.loaded_deck.get_locked_texture()
            elif card == "WAIT":
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
        try:
            region = self.achievements.get_achievement_texture(achievement)
            if self.achievements.deck_specific(achievement):
                return self.deck_achievement_texture.get_region(*region)
            return self.achievement_texture.get_region(*region)
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
        elif key == 'FULLSCREEN':
            if value:
                Config.set('graphics', 'fullscreen', 'auto')
            else:
                Config.set('graphics', 'fullscreen', 0)
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
