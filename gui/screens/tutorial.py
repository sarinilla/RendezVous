from kivy.factory import Factory
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout

from rendezvous import GameSettings

from gui import PLAYER
from gui.components import RoundCounter, ScoreDisplay, ToolTipDisplay
from gui.components import CardDisplay, HandDisplay, BoardDisplay

class HandIntro(Screen):
    
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
        gameboard = Factory.HandIntroDisplay(size_hint=(4, 1))
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
        layout.add_widget(gameboard)
        sidebar = BoxLayout(orientation="vertical")
        sidebar.add_widget(self.round_counter)
        sidebar.add_widget(self.scoreboard)
        sidebar.add_widget(self.tooltip)
        layout.add_widget(sidebar)
        main.add_widget(layout)
        main.add_widget(self.hand_display)
        self.add_widget(main)


class BoardIntro(Screen):
    
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
        self.tooltip = Factory.BoardIntroDisplay(size_hint=(1, 1))
        #self.tooltip.ids.continue_btn.bind(on_press=self.manager.score_tutorial)
        self.hand_display = HandDisplay(hand=game.players[PLAYER],
                                        size_hint=(1, .3))

        # Lay out the display
        main = BoxLayout(orientation="vertical")
        layout = BoxLayout()
        layout.add_widget(self.gameboard)
        sidebar = BoxLayout(orientation="vertical")
        #sidebar.add_widget(self.round_counter)
        #sidebar.add_widget(self.scoreboard)
        sidebar.add_widget(self.tooltip)
        layout.add_widget(sidebar)
        main.add_widget(layout)
        main.add_widget(self.hand_display)
        self.add_widget(main)
        

class ScoreIntro(Screen):
    
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
        self.tooltip = Factory.ScoreIntroDisplay(size_hint=(1, 1))
        self.hand_display = HandDisplay(hand=game.players[PLAYER],
                                        size_hint=(1, .3))

        # Lay out the display
        main = BoxLayout(orientation="vertical")
        layout = BoxLayout()
        layout.add_widget(self.gameboard)
        sidebar = BoxLayout(orientation="vertical")
        #sidebar.add_widget(self.round_counter)
        #sidebar.add_widget(self.scoreboard)
        sidebar.add_widget(self.tooltip)
        layout.add_widget(sidebar)
        main.add_widget(layout)
        main.add_widget(self.hand_display)
        self.add_widget(main)


class PostScoringIntro(Screen):

    """Continue the game, with small instructions."""

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
        self.tooltip = Factory.PostScoringDisplay(size_hint=(1, .5))
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
        

class TooltipIntro(Screen):
    
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
        self.gameboard = Factory.TooltipIntroDisplay(size_hint=(4, 1))
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
