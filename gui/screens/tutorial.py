from kivy.factory import Factory
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout

from rendezvous import GameSettings

from gui import PLAYER
from gui.components import RoundCounter, ScoreDisplay, ToolTipDisplay
from gui.components import CardDisplay, HandDisplay, BoardDisplay


class _Tutorial:

    """Provides common features for Tutorial Screens."""

    button = ObjectProperty(allownone=True)

    def on_button(self, *args):
        """Add a button after the fact.  (Call ONCE only!)"""
        if self.button is not None:
            self.button.size_hint = (1, .04)
            self.tutorial.add_widget(self.button)

    def __getattr__(self, name):
        """Refer unused display areas to the primary GameScreen."""
        return getattr(self.manager.main, name)


class MainBoardTutorial(Screen, _Tutorial):
    
    """Extends GameScreen to show tutorial content instead of the main board.

    Properties:
      tutorial.title  -- bold text at the top of the screen
      tutorial.text   -- main tutorial text
      tutorial.footer -- additional line in bold at the bottom
      button          -- button to add at the bottom (or None)

    """

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)

        # Prepare the display areas
        game = kwargs["game"]
        self.tutorial = Factory.TutorialDisplay(size_hint=(4, 1))
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
        layout.add_widget(self.tutorial)
        sidebar = BoxLayout(orientation="vertical")
        sidebar.add_widget(self.round_counter)
        sidebar.add_widget(self.scoreboard)
        sidebar.add_widget(self.tooltip)
        layout.add_widget(sidebar)
        main.add_widget(layout)
        main.add_widget(self.hand_display)
        self.add_widget(main)


class SidebarTutorial(Screen, _Tutorial):
    
    """Extends GameScreen to show tutorial content on the right sidebar.

    Properties:
      tutorial.title  -- bold text at the top of the screen
      tutorial.text   -- main tutorial text
      tutorial.footer -- additional line in bold at the bottom
      button          -- button to add at the bottom (or None)

    """

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)

        # Prepare the display areas
        game = kwargs["game"]
        self.gameboard = BoardDisplay(board=game.board,
                                      size_hint=(4, 1))
        self.tutorial = Factory.TutorialDisplay(size_hint=(1, 1))
        self.hand_display = HandDisplay(hand=game.players[PLAYER],
                                        size_hint=(1, .3))

        # Lay out the display
        main = BoxLayout(orientation="vertical")
        layout = BoxLayout()
        layout.add_widget(self.gameboard)
        sidebar = BoxLayout(orientation="vertical")
        sidebar.add_widget(self.tutorial)
        layout.add_widget(sidebar)
        main.add_widget(layout)
        main.add_widget(self.hand_display)
        self.add_widget(main)


class TooltipTutorial(Screen, _Tutorial):
    
    """Extends GameScreen to show tutorial content below the score.

    Properties:
      tutorial.title  -- bold text at the top of the screen
      tutorial.text   -- main tutorial text
      tutorial.footer -- additional line in bold at the bottom
      button          -- button to add at the bottom (or None)

    """

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)

        # Prepare the display areas
        game = kwargs["game"]
        self.gameboard = BoardDisplay(board=game.board,
                                      size_hint=(4, 1))
        self.round_counter = RoundCounter(round_number=1,
                                          max_round=GameSettings.NUM_ROUNDS,
                                          size_hint=(1, .15))
        self.scoreboard = ScoreDisplay(scoreboard=game.score,
                                       size_hint=(1, .8))
        self.tutorial = Factory.TutorialDisplay(size_hint=(1, 1))
        self.hand_display = HandDisplay(hand=game.players[PLAYER],
                                        size_hint=(1, .3))

        # Lay out the display
        main = BoxLayout(orientation="vertical")
        layout = BoxLayout()
        layout.add_widget(self.gameboard)
        sidebar = BoxLayout(orientation="vertical")
        sidebar.add_widget(self.round_counter)
        sidebar.add_widget(self.scoreboard)
        sidebar.add_widget(self.tutorial)
        layout.add_widget(sidebar)
        main.add_widget(layout)
        main.add_widget(self.hand_display)
        self.add_widget(main)
