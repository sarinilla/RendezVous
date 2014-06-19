import os
import copy

from kivy.clock import Clock
from kivy.app import App
from kivy.core.image import Image
from kivy.graphics.texture import Texture
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.loader import Loader

from rendezvous import GameSettings
from rendezvous.deck import DeckDefinition, Card
from rendezvous.gameplay import RendezVousGame
from rendezvous.statistics import Statistics
from rendezvous.achievements import AchievementList

from gui import DEALER, PLAYER
from gui.components import BLANK, DARKEN
from gui.screens.game import GameScreen, WinnerScreen
from gui.screens.tutorial import MainBoardTutorial, SidebarTutorial, TooltipTutorial


__version__ = '0.4.1'


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
            app = kwargs['app']
        except KeyError:
            app = App.get_running_app()

        # Prepare internal storage
        self.game = RendezVousGame(deck=app.loaded_deck,
                                   achievements=app.achievements)
        self.game.new_game()
        self._cards_played = []    #: hand indices played so far
        self.achieved = []         #: Achievements earned this game
        self.dealer_play = None    #: cards the dealer will play
        self._in_progress = False  #: currently scoring a round?

        # Prepare the screens
        self.main = GameScreen(game=self.game, name='main')
        self.add_widget(self.main)

        # Prepare the tutorial (if needed)
        if app.achievements.achieved == []:
            self.switch_to(MainBoardTutorial(game=self.game,
                                             name='tutorial-hand'))
            self.current_screen.tutorial.title = "Welcome to RendezVous!"
            self.current_screen.tutorial.text = "This tutorial will walk you through your first game, introducing key concepts along the way. RendezVous is easy to play, but you will find the strategies to be endless!\n\nYour hand is displayed below. Each round, you will pick 4 cards to play, then your hand will be refilled to 10 again. Go ahead and pick your first four cards now.\n\n(Higher values are better!)"
            self.current_screen.tutorial.footer = "SELECT 4 CARDS BELOW"

        self._play_player()
            

    def card_touched(self, card_display):
        """Handle a touch to a displayed card."""
        if self._in_progress: return
        if card_display.card is None: return
        if self.dealer_play is None:
            self.dealer_play = self.game.players[DEALER].AI_hard(
                                    DEALER, self.game.board, self.game.score)
        if self.current == 'tutorial-tooltip':
            for slot in self.current_screen.hand_display.slots:
                slot.highlight(BLANK)
        
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
        card = self.current_screen.hand_display.get(card_or_display)
        print("... hand confirmed %s" % card)
        self.current_screen.gameboard.place_card(card, index)
        if self.game.board.is_full(PLAYER):
                print("... board full:", [[str(c) for c in self.game.board[0]],
                                          [str(c) for c in self.game.board[1]]])
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

    def _play_player(self):
        print("dealer hand:", [str(c) for c in self.game.players[DEALER].cards])
        self.dealer_play = self.game.players[DEALER].AI_hard(
                                    DEALER, self.game.board, self.game.score)
        print("dealer picked", [str(c) for c in self.dealer_play])
        print("player hand:", [str(c) for c in self.game.players[PLAYER].cards])
        player_play = self.game.players[PLAYER].AI_hard(PLAYER,
                                                        self.game.board,
                                                        self.game.score)
        print("player picked", [str(c) for c in player_play])
        for card in player_play:
            print("... placing %s" % card)
            self._place_on_board(card)

    def _play_dealer(self):
        """Place the dealer's selected cards on the board."""
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
                                                  timer=0.1)
        for card in self.dealer_play:
            self.game.players[DEALER].remove(card)
        self.dealer_play = None
        
    def _specials(self):
        """Apply all specials."""
        #if self.current == 'tutorial-board':
        #    self._in_progress = False
        #    return  # until continue is pressed
        self.current_screen.gameboard.apply_specials(self.game,
                    self.current_screen.hand_display, self._score, 0.1)

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
                callback=self.next_round,
                timer=0.1)

    def replay_scoring(self):
        """Replay the scoring sequence at the user's request."""
        self.game.score.scores = self._backup_score
        for card in self.game.board:
            card.reset()
        self.current_screen.gameboard.highlight(BLANK)
        self.current_screen.gameboard.update()
        self.current_screen.scoreboard.update()
        Clock.schedule_once(lambda dt: self._specials(), GameSettings.SPEED)

    def next_round(self):
        """Clear the board for the next round."""
        print("new score", self.game.score.scores)
        #if self.current == 'tutorial-score':
        #    self.switch_to(TooltipTutorial(game=self.game,
        #                                   name='tutorial-continue'))
        #    self.current_screen.tutorial.title = "The Scoreboard"
        #    self.current_screen.tutorial.text= "Your score in each suit is shown above, to the left. The dealer's score is to the right.\n\nAfter %s rounds, the winner is the one leading in the most suits." % GameSettings.NUM_ROUNDS
        #    self.current_screen.tutorial.footer = "Play a few rounds!"
        app = App.get_running_app()
        game_over = self.game.next_round()
        if game_over:
            self.achieved += app.record_score(self.game.score)
            self._winner = WinnerScreen(self.game.score, self.achieved,
                                        name='winner')
            self.switch_to(self._winner)
            print("GAME OVER", self.game.score.scores)
            Clock.schedule_once(lambda dt: self.play_again(), 0.1)
            return
        elif self.game.board.is_full(PLAYER):
            print("(already full) dealer hand:", [str(c) for c in self.game.players[DEALER].cards])
            self.dealer_play = self.game.players[DEALER].AI_hard(
                                    DEALER, self.game.board, self.game.score)
            print("dealer picked", [str(c) for c in self.dealer_play])
            self._play_dealer()
            return

        if self.current == 'tutorial-continue' and self.game.round >= 10:
            special = app.loaded_deck.get_special('Perfume')
            self.game.players[PLAYER].cards[8] = special
            app.achievements.achieved.append("Tutorial")
            self.game.players[PLAYER].deck.shuffle()
            self.switch_to(MainBoardTutorial(game=self.game,
                                             name='tutorial-tooltip'))
            self.current_screen.tutorial.title = "Introducing Special Cards"
            self.current_screen.tutorial.text = "In addition to the five normal suits, you will sometimes get special cards in your hand. These can only be played when certain conditions are met, but they have the power to affect the other cards you play, or even the dealer's cards.\n\nYou drew a PERFUME card! This will raise the value of any Girlfriends you play alongside it. Drag your Perfume card onto the tooltip display below the scoreboard to read about what it does and how to use it.\n\nThere are many different types of special cards. The best cards are unlocked by completing RendezVous Achievements - and when you download a custom deck, it will come with its own unique Special Cards!"
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
        self._play_player()

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
        self._play_player()


class RendezVousApp(App):

    """Main RendezVous App, with deck loaded."""
    
    deck_texture = ObjectProperty()

    def __init__(self, **kwargs):
        """Load the deck image and create the RendezVousWidget."""
        App.__init__(self, **kwargs)
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

    def _image_loaded(self, loader):
        """Update the deck image when it's finished loading."""
        if loader.image.texture:
            self.deck_texture = loader.image.texture

    def _achievements_loaded(self, loader):
        if loader.image.texture:
            self.achievement_texture = loader.image.texture

    def build(self):
        return RendezVousWidget(app=self)
        
    def record_score(self, score):
        """Update meta-data at the end of each game."""
        self.statistics.record_game(score, PLAYER)
        return self.achievements.check(score, PLAYER, self.statistics)

    def get_texture(self, card):
        """Return the appropriate texture to display."""
        if card is None or card.name is " ":
            return Texture.create()
            #region = self.loaded_deck.get_back_texture()
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

    def get_dealer_texture(self, *args):
        """Return the appropriate dealer texture to display."""
        region = self.loaded_deck.get_dealer_texture(*args)
        return self.deck_texture.get_region(*region)
            
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
