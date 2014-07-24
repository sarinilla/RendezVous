import copy

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from kivy.properties import StringProperty, ObjectProperty, NumericProperty
from kivy.properties import BooleanProperty, ListProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout

from gui import PLAYER, DEALER
from gui.components import RED, GREEN
from gui.components import RoundCounter, ScoreDisplay, ToolTipDisplay
from gui.components import HandDisplay, BoardDisplay
from gui.screens.winner import WinnerScreen
from gui.powerups import PowerupsAvailable


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

    def finish(self):
        Clock.unschedule(self._next_word)
        self.text = self.full_text
        self.words_left = []


class DealerImage(Widget):

    """Display a dealer image."""

    dealer_index = NumericProperty()

    def __init__(self, **kwargs):
        Widget.__init__(self, **kwargs)
        app = App.get_running_app()
        with self.canvas:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(texture=app.get_dealer_texture(self.dealer_index, 0),
                                  size=self.size, pos=self.pos)
        self.bind(size=self._place_rect, pos=self._place_rect)

    def _place_rect(self, *args):
        self.rect.size = min(*self.size), min(*self.size)
        self.rect.pos = self.pos


class ScreenWithDealer(Screen):

    """Allows a dealer with a speech bubble to pop up over the screen content.

    Requires a FloatLayout called self.float!

    """
    
    text = []

    def __init__(self, **kwargs):
        """Separate instance text from class storage."""
        self.text = copy.deepcopy(self.text)
        super(ScreenWithDealer, self).__init__(**kwargs)

    def show_dealer(self, dealer_index, reverse=False, offset=(0, 0),
                    start=None, animate=True):
        if start is None:
            start = (-500, 0) if not reverse else (self.size[0] + 500, 0)
        self.dealer = DealerImage(dealer_index=dealer_index,
                                  size_hint=(.5, .8),
                                  pos=start)
        self.float.add_widget(self.dealer)
        target_x = self.size[0] / 2 if reverse else 0
        if animate:
            anim = Animation(x=offset[0] + target_x, y=offset[1])
            anim.bind(on_complete=lambda *a: self._show_speech(reverse))
            anim.start(self.dealer)
        else:
            self.dealer.pos = (offset[0] + target_x, offset[1])
            Clock.schedule_once(lambda *a: self._show_speech(reverse))

    def _show_speech(self, reverse):
        if self.text == []: return
        delta_x = self.dealer.width if not reverse else -self.dealer.width * 3 / 5
        self.bubble = SpeechBubble(full_text=self.text.pop(0),
                                   size_hint=(.3, .4),
                                   pos=(self.dealer.pos[0] + delta_x,
                                        self.dealer.pos[1] + self.dealer.height / 2))
        self.float.add_widget(self.bubble)

    def on_touch_up(self, touch):
        try: self.bubble
        except AttributeError:
            return True
        if self.bubble.words_left != []:
            self.bubble.finish()
        elif self.text != []:
            self.bubble.full_text = self.text.pop(0)
        else:
            self.advance()
        

class GameTutorialScreen(Screen):
    
    """Provides common features for Tutorial Screens."""

    next_tutorial = None

    def __init__(self, **kwargs):
        super(GameTutorialScreen, self).__init__(**kwargs)
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

    def scoring_complete(self):
        return False

    def next_round(self, num, game_over):
        return False

    def card_touched(self):
        """Don't allow card touches during text playback."""
        return True


class TutorialScreen(GameTutorialScreen, ScreenWithDealer):
    pass


class TutorialActionItemScreen(GameTutorialScreen):

    """Show the normal game screen, with a text bar across the top."""

    action_item = StringProperty()

    def draw_tutorial(self, *args):
        self.action_prompt = Label(text='[b]%s[/b]' % self.action_item.upper(),
                                   markup=True,
                                   valign="middle", halign="center",
                                   size_hint=(.8, .1),
                                   pos_hint={'x':0, 'y':.85})
        self.float.add_widget(self.action_prompt)
        Clock.schedule_once(self._draw_background)

    def _draw_background(self, *args):
        with self.action_prompt.canvas.before:
            Color(0, 0, 0, .75)
            Rectangle(size=self.action_prompt.size,
                      pos=self.action_prompt.pos)

    def on_action_item(self, *args):
        try:
            self.action_prompt.text = '[b]%s[/b]' % self.action_item.upper()
        except AttributeError:
            pass  # might not be set up yet...

    def card_touched(self):
        """Allow card touches to progress normally."""
        return False


class AnalyzeScore:

    """Provides methods for analyzing the current score.

    Requires access to the ScoreDisplay as self.scoreboard!

    """

    def result(self):
        """Return the current gap in winning suits (player's - dealer's)."""
        return (len(self.scoreboard.scoreboard.wins(PLAYER)) -
                len(self.scoreboard.scoreboard.wins(DEALER)))

    def _lead(self, suit_index):
        """Return the current score gap for the suit (player's - dealer's)."""
        return (self.scoreboard.scoreboard.scores[PLAYER][suit_index] -
                self.scoreboard.scoreboard.scores[DEALER][suit_index])
    
    def closest_win(self):
        """Return the (suit, lead) of the narrowest current win."""
        best = (None, None)
        for i, suit in enumerate(self.scoreboard.scoreboard.suits):
            lead = self._lead(i)
            if lead <= 0: continue
            if best[1] is None or lead < best[1]:
                best = (suit, lead)
        return best

    def best_win(self):
        """Return the (suit, lead) of the strongest current win."""
        best = (None, None)
        for i, suit in enumerate(self.scoreboard.scoreboard.suits):
            lead = self._lead(i)
            if lead <= 0: continue
            if best[1] is None or lead > best[1]:
                best = (suit, lead)
        return best

    def worst_loss(self):
        """Return the (suit, lead) of the strongest current loss."""
        best = (None, None)
        for i, suit in enumerate(self.scoreboard.scoreboard.suits):
            lead = self._lead(i)
            if lead >= 0: continue
            if best[1] is None or lead < best[1]:
                best = (suit, lead)
        return best

    def closest_loss(self):
        """Return the (suit, lead) of the closest current loss."""
        best = (None, None)
        for i, suit in enumerate(self.scoreboard.scoreboard.suits):
            lead = self._lead(i)
            if lead >= 0: continue
            if best[1] is None or lead > best[1]:
                best = (suit, lead)
        return best

    def tied_suit(self):
        """Return the name of a tied suit."""
        for i, suit in enumerate(self.scoreboard.scoreboard.suits):
            if self._lead(i) == 0:
                return suit
        return None
            


##  Begin Tutorial Screens (in reverse order)  ##


class TutorialGameOver(WinnerScreen, ScreenWithDealer):

    # text is auto-filled

    def __init__(self, **kwargs):
        """Generate text and display it."""
        super(TutorialGameOver, self).__init__(**kwargs)
        self.float = self.ids.float  # rename for ScreenWithDealer
        self._analyze()
        Clock.schedule_once(lambda *a: self.show_dealer(dealer_index=1, reverse=True))

    def advance(self, *args):
        self.float.remove_widget(self.dealer)
        self.float.remove_widget(self.bubble)
        # stay on this screen

    def _analyze(self):

        """Generate text based on the final score."""

        # Win/lose/draw
        pwins = len(self.score.wins(PLAYER))
        dwins = len(self.score.wins(DEALER))
        if pwins > dwins:
            self.text.append("Aww, you beat me!")
        elif pwins < dwins:
            self.text.append("Gotcha this time!")
        else:
            self.text.append("Ooh, we tied!")

        # Comment on winks earned
        if pwins > dwins:
            self.text.append("You earned %s winks for this game - one for each suit, plus one more for winning the game!" % (pwins + 1))
        elif pwins > 0:
            self.text.append("You earned %s winks for this game - one for each suit you won.")
        else:
            self.text.append("You didn't win any suits this game, so you didn't earn any winks this time - keep trying!")
            self.text.append("If you would like to repeat the tutorial, you can access it any time from the Settings icon!")

        # Comment on kisses earned
        kisses = len(self.achieved) if self.achieved is not None else 0
        if kisses > 0:
            self.text.extend(["You earned %s kisses for unlocking Achievements during the game!" % kisses,
                              "You can use your kisses to unlock backgrounds, or even new decks to play with.",
                              "Swipe left and right to look through your Achievements, or to see the final score."])
        else:
            self.text.extend(["You didn't unlock any new Achievements this time.",
                              "You can use the Achievements icon on the home screen to view all of the goals you can shoot for!",
                              "Achievements grant you kisses, which you can use to unlock backgrounds, or even new decks to play with."])


class TutorialFinishGame(PowerupsAvailable, TutorialActionItemScreen):

    action_item = "Finish it up!"

    def draw_tutorial(self, *args):
        """Update powerups in use."""
        self._update_powerups()
        super(TutorialFinishGame, self).draw_tutorial(*args)

    # manager will advance automatically when the game's over!


class TutorialEndGame(TutorialScreen, AnalyzeScore):

    text = ["Your time is almost up - only a few rounds left in this game!",
            "Take a look at your suit scores and see what you can do to improve your odds.",
            "Remember, you have to win more suits than your opponent does in order to win the game!",
            "You will earn extra winks for winning even more suits."]
            #Score-specific text will be added dynamically

    next_tutorial = TutorialFinishGame

    def draw_tutorial(self, *args):
        """Show dealer text with additional lines."""
        self._highlight(self.scoreboard)
        self._analyze_score()
        self.show_dealer(dealer_index=4)

    def _analyze_score(self):

        """Provide specific guidance for the current situation."""

        # Win/lose/draw
        result = self.result()
        if result > 0:
            self.text.append("Great work - you are winning so far!")
        elif result < 0:
            self.text.append("Uh-oh, right now you are losing...")
        else:
            self.text.append("Looks like you're tied right now.")

        # Look for a close win
        close_win = self.closest_win()
        if result >= 0 and close_win[0] is not None:
            if close_win[1] < 50:
                self.text.append("Be careful not to lose points in the %s suit so you can hold your lead!" % close_win[0])

        # Look for a suit to target
        close_loss = self.closest_loss()
        contested = self.tied_suit()
        target = close_loss[0]
        if target is None or close_loss[1] < -30:
            target = contested
        if target is None:
            target = close_win[0]

        # Look for a suit to sacrifice
        sacrifice = self.worst_loss()
        if sacrifice[1] is None or sacrifice[1] > -30:
            sacrifice = self.best_win()
            if sacrifice[1] is not None and sacrifice[1] < 60:
                sacrifice = (None, None)

        # Suggest the sacrifice and/or target
        if sacrifice[0] is not None and target is not None:
            self.text.append("You might consider sacrificing points in the %s suit to gain an advantage in %s." % (sacrifice[0], target))
        elif target is not None:
            self.text.append("See if you can use your special cards to catch up in the %s suit!" % target)
                                


class TutorialPlayToEndgame(PowerupsAvailable, TutorialActionItemScreen):

    action_item = "Play on!"

    next_tutorial = TutorialEndGame

    def draw_tutorial(self, *args):
        """Update powerups in use."""
        self._update_powerups()
        super(TutorialPlayToEndgame, self).draw_tutorial(*args)

    def next_round(self, num, game_over):
        """Move forward after round 15."""
        if num == 16:
            self.advance()
            return True
        return False


class TutorialPowerupsDone(TutorialScreen):

    text = ["Great work!",
            "After the game, you can click the Powerups icon on the home screen to browse all of the powerups available.",
            "You might have to save up a while to make a purchase..."]

    next_tutorial = TutorialPlayToEndgame

    def draw_tutorial(self, *args):
        """Show the dealer text."""
        self._fade(self.main)
        self.show_dealer(dealer_index=3, reverse=True)


class TutorialDragPowerups(PowerupsAvailable, TutorialActionItemScreen):

    action_item = "Swipe from the right"

    next_tutorial = TutorialPowerupsDone

    def draw_tutorial(self, *args):
        """Watch for a powerup to be used."""
        self._update_powerups()
        self.manager.bind(powerups_in_use=self.advance)
        self.gameboard.next_round_prompted()
        super(TutorialDragPowerups, self).draw_tutorial(*args)

    def advance(self, *args):
        """Don't try to advance twice (on powerup cleanup)."""
        if self.manager is None: return
        super(TutorialDragPowerups, self).advance(*args)
        

class TutorialPowerups(TutorialScreen):

    text = ["[b]Powerups[/b] are another way to press your advantage.",
            "You can buy powerups using the winks you earn at the end of a game.",
            "I’ve given you a simple [b]Super Buff[/b] powerup to get you started.",
            "This powerup will raise the value of each card you play by 2 points.",
            "Swipe from the right to open your powerup tray and put it to use!"]

    next_tutorial = TutorialDragPowerups

    def draw_tutorial(self, *args):
        """Award the powerup and explain it."""
        self.manager.app.powerups.purchase("Super Buff")
        self._fade(self.main)
        self.show_dealer(dealer_index=3, reverse=True)


class TutorialPlayWithSpecials(TutorialActionItemScreen):

    action_item = "Play on, using special cards to your advantage..."

    next_tutorial = TutorialPowerups

    def next_round(self, num, game_over):
        """Move forward after round 10."""
        if num == 11:
            self.advance()
            return True
        return False


class TutorialSpecialCardDragged(TutorialScreen):

    text = ["There are many different types of special cards.",
            "The best cards are unlocked by completing RendezVous Achievements.",
            "When you unlock a custom deck, it will come with its own unique Special Cards!"]

    next_tutorial = TutorialPlayWithSpecials

    def draw_tutorial(self, *args):
        """Show the dealer text."""
        self._fade(self.main)
        self.show_dealer(dealer_index=2)


class TutorialSpecialCardDrag(TutorialActionItemScreen):

    action_item = "Drag the special card below the scoreboard"
    next_tutorial = TutorialSpecialCardDragged
    ready = False

    def draw_tutorial(self, *args):
        """Highlight the tooltip area blue."""
        with self.tooltip.canvas.before:
            Color(0, 0, 1, .75)
            Rectangle(size=self.tooltip.size, pos=self.tooltip.pos)
        self._fade(self.gameboard)
        self._fade(self.round_counter)
        self._fade(self.scoreboard)
        self.tooltip.bind(card=self._dragged)
        super(TutorialSpecialCardDrag, self).draw_tutorial(*args)
        
    def _dragged(self, *args):
        """Ready to move forward as soon as the card is dragged."""
        self.ready = True

    def card_touched(self):
        """Move forward on the first touch after dragging the card up."""
        if self.ready:
            self.advance()
        return True


class TutorialSpecialCard(TutorialScreen):

    text = ["[b]Special cards[/b] will sometimes show up alongside the five normal suits.",
            "These can only be played when certain conditions are met.",
            "Many of them have the power to affect the other cards you play, or even the dealer's cards.",
            "You drew the [b]special[/b] card!",
            "Drag your new special card onto the tooltip display below the scoreboard to read about what it does and how to use it."]

    next_tutorial = TutorialSpecialCardDrag

    def draw_tutorial(self, *args):
        """Plant a special card and show dealer text."""
        self._highlight(self.hand_display)
        special = self.manager.plant_special()
        self.text[3] = self.text[3].replace("special", special.name)
        self.show_dealer(dealer_index=2)


class TutorialPlayAFew(TutorialActionItemScreen):

    action_item = StringProperty("Play a few rounds!")

    next_tutorial = TutorialSpecialCard

    def draw_tutorial(self, *args):
        """Leave the tooltip area faded."""
        self._fade(self.tooltip)
        self.gameboard.next_round_prompted()
        super(TutorialPlayAFew, self).draw_tutorial(*args)

    def next_round(self, num, game_over):
        """Move forward after round 5."""
        if num == 6:
            self.advance()
            return True
        else:
            self.action_item = "Pick your cards..."
        return False

    def scoring_complete(self, *args):
        won, lost = 0, 0
        for slot in self.gameboard.slots[PLAYER]:
            if slot.color == GREEN: won += 1
            elif slot.color == RED: lost += 1
        if won > 0 and lost > 0:
            self.action_item = "You won %s match%s and lost %s." % (won, "es" if won > 1 else "", lost)
        elif won > 0:
            self.action_item = "Yay! You won %s match%s!" % (won, "es" if won > 1 else "")
        elif lost > 0:
            self.action_item = "Oops, you lost %s match%s..." % (lost, "es" if lost > 1 else "")
        else:
            self.action_item = "It's a tie!"
        return False
    

class TutorialScoreboard(TutorialScreen):

    text = ["Your score in each suit is shown on the left side of the scoreboard.",
            "The dealer's score is to the right.",
            "After 20 rounds, the winner is the one leading in the most suits."]

    next_tutorial = TutorialPlayAFew
    
    def draw_tutorial(self, *args):
        """Show the dealer text."""
        self._highlight(self.scoreboard)
        self.manager._reset_scoring()
        for i in range(4):
            self.gameboard._score_match(self.scoreboard,
                                        self.scoreboard.scoreboard, i)
        self.show_dealer(dealer_index=0, start=(self.size[0]/2, 0))


class TutorialScoringHighlights(TutorialScreen):

    text = ["As the round is scored, the highlighting will help you see who won each match-up."]

    next_tutorial = TutorialScoreboard
    
    def draw_tutorial(self, *args):
        """Show the dealer text."""
        self._highlight(self.gameboard)
        self.manager._reset_scoring()
        self.manager._score(then_prompt=False)
        self.show_dealer(dealer_index=0, reverse=True, start=(0, 0))


class TutorialScoringReplay(TutorialScreen):

    text = ["A win earns you 10 points in the suit you played, and 10 points in the dealer's suit.",
            "A loss costs you 10 points in your suit only."]

    next_tutorial = TutorialScoringHighlights
    
    def draw_tutorial(self, *args):
        """Replay the scoring sequence behind the dealer text."""
        self._highlight(self.scoreboard)
        self.manager._reset_scoring()
        for i in range(4):
            self.gameboard._score_match(self.scoreboard,
                                        self.scoreboard.scoreboard, i)
        self.show_dealer(dealer_index=0, animate=False)

    def advance(self, *args):
        """Only advance when the sequence is complete."""
        if not self.manager._in_progress:
            super(TutorialScoringReplay, self).advance(*args)


class TutorialScoring(TutorialScreen):

    text = ["There are five suits in the deck, and you are scored in each suit."]

    next_tutorial = TutorialScoringReplay
    
    def draw_tutorial(self, *args):
        """Show the dealer text."""
        self._highlight(self.scoreboard)
        self.manager._reset_scoring()
        for i in range(4):
            self.gameboard._score_match(self.scoreboard,
                                        self.scoreboard.scoreboard, i)
        self.show_dealer(dealer_index=0)


class TutorialMatches(TutorialScreen):

    # text is dynamically generated

    next_tutorial = TutorialScoring

    def draw_tutorial(self, *args):
        """Generate text based on matches won/lost."""
        self._highlight(self.gameboard)
        self.manager._reset_scoring()
        for i in range(4):
            self.gameboard._score_match(self.scoreboard,
                                        self.scoreboard.scoreboard, i)
        self._count_matches()
        self.show_dealer(dealer_index=1, reverse=True, animate=False)

    def _count_matches(self):
        """Use the colors to count matches."""
        won, lost = 0, 0
        for slot in self.gameboard.slots[PLAYER]:
            if slot.color == GREEN:
                won += 1
            elif slot.color == RED:
                lost += 1
        if won > lost:
            self.text.append("Well done, you beat me in %s out of 4 matches!" % won)
            self.text.append("Let's see if you can keep it up...")
        elif lost > won:
            if won > 0:
                self.text.append("Hoo, well, at least you won %s match%s..." % (won, "es" if won > 1 else ""))
            else:
                self.text.append("Looks like I got you this round!")
                self.text.append("We'll see if I can keep it up...")
        else:
            self.text.append("Huh.  Looks like we tied this round!")


class TutorialDealerPlay(TutorialScreen):

    text = ["Each card you play is compared against the card directly above it to determine your score.",
            "Green highlights are the match winners, and red highlights are the losers.",
            "If the cards tie, then neither one is highlighted."]

    next_tutorial = TutorialMatches
    
    def draw_tutorial(self, *args):
        """Play the scoring sequence behind the dealer text."""
        self._highlight(self.gameboard)
        self.manager._score(then_prompt=False)
        self.show_dealer(dealer_index=1, reverse=True, animate=False)

    def advance(self, *args):
        """Only advance when the sequence is complete."""
        if not self.manager._in_progress:
            super(TutorialDealerPlay, self).advance(*args)


class TutorialDealerTurn(TutorialScreen):

    text = ["I have a hand of 10 cards, just like you.",
            "Each round, I will pick four cards to play against yours."]
    
    next_tutorial = TutorialDealerPlay
    
    def draw_tutorial(self, *args):
        """Show the dealer text while playing in the background."""
        self._highlight(self.gameboard)
        self.manager._play_dealer(then_score=False)
        self.show_dealer(dealer_index=1, reverse=True, animate=False)

    def advance(self, *args):
        """Only advance when the play is complete."""
        if not self.manager._in_progress:
            super(TutorialDealerTurn, self).advance(*args)


class TutorialDealerAnnounce(TutorialScreen):

    text = ["[b]My turn![/b]"]
    
    next_tutorial = TutorialDealerTurn
    
    def draw_tutorial(self, *args):
        """Show the dealer text while playing in the background."""
        self._highlight(self.gameboard)
        self.show_dealer(dealer_index=1, reverse=True)


class TutorialPickingCards(TutorialActionItemScreen):

    action_item = "Select 4 cards"
    next_tutorial = TutorialDealerAnnounce

    def all_cards_selected(self, *args):
        """Move forward after all four cards are selected."""
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
        self.show_dealer(dealer_index=0, animate=False)


class FirstTutorialScreen(TutorialScreen):

    """Starting point for the tutorial."""

    text = ["[b]Welcome to RendezVous![/b]",
            "This tutorial will walk you through your first game, introducing key concepts along the way.",
            "RendezVous is easy to play, but you will find the strategies to be endless!"]

    next_tutorial = TutorialPickCards
    
    def draw_tutorial(self, *args):
        """Cover the game screen items and show the welcome text."""
        self._fade(self.main)
        self.show_dealer(dealer_index=0)
