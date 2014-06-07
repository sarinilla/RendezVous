
from rendezvous import GameSettings, SpecialSuit, SpecialValue

class Hand:

    """Holds cards for a player's hand.

    Attributes:
      cards -- the current hand of Cards
      deck  -- the player's deck from which to draw

    Methods:
      refill -- bring the hand back up to its full count

    """

    def __init__(self, deck):
        self.deck = deck
        self.flush()

    def __len__(self):
        return GameSettings.CARDS_IN_HAND

    def __getitem__(self, key):
        return self.cards[key]

    def __iter__(self):
        return iter(self.cards)

    def refill(self):
        """Fill up to maximum capacity from the deck."""
        while len(self.cards) < GameSettings.CARDS_IN_HAND:
            self.cards.append(self.deck.draw())

    def choose_play(self):
        pass

    def flush(self):
        """Empty hand and refill from deck."""
        self.cards = []
        self.refill()


class Gameboard:

    """Manages the cards in play.

    Attributes:
      board -- 2D list of Cards [player][index]
      wait  -- 2D list of booleans marking Cards held to the next round

    """

    def __init__(self):
        self._clear_wait()
        self._clear_board()

    def __len__(self):
        return GameSettings.NUM_PLAYERS

    def __getitem__(self, key):
        return self.board[key]

    def __iter__(self):
        return iter(self.board[0] + self.board[1])

    def wait(self, player_index, card_index):
        """Hold the given card through the next round."""
        self._wait[player_index][card_index] = True

    def _clear_wait(self):
        """Clear all holds."""
        self._wait = [[False for i in range(GameSettings.CARDS_ON_BOARD)]
                      for i in range(GameSettings.NUM_PLAYERS)]

    def _clear_board(self):
        """Clear all cards from the board."""
        new_board = [[None for i in range(GameSettings.CARDS_ON_BOARD)]
                     for i in range(GameSettings.NUM_PLAYERS)]
        for (p, side) in enumerate(self._wait):
            for (c, hold) in enumerate(side):
                if hold:
                    new_board[p][c] = self.board[p][c]
        self.board = new_board

    def next_round(self):
        """Advance to the next round."""
        self._clear_board()
        self._clear_wait()

    def clear(self):
        """Reset the board for a new game."""
        self._clear_wait()
        self._clear_board()
        


class Scoreboard:

    """Tracks the score for the game.

    Attributes:
      score -- the current score by [player][suit]

    """

    def __init__(self, deck):
        self.suits = deck.suits
        self.zero()

    def __len__(self):
        return GameSettings.NUM_PLAYERS

    def __getitem__(self, key):
        return self.score[key]

    def __iter__(self):
        return iter(self.score[0] + self.score[1])

    def zero(self):
        """Zero the score for all players and suits."""
        self.score = [[0 for suit in self.suits]
                      for p in range(GameSettings.NUM_PLAYERS)]

    def score(self, board):
        """Score the board, adjusting each player's totals."""
        for i in range(GameSettings.CARDS_ON_BOARD):
            for p in range(GameSettings.NUM_PLAYERS):
                self._score_match(p, board[p][i], p-1, board[p-1][i])
                # wraps around when -1 is last player

    def _score_match(self, player, player_card, enemy, enemy_card):

        """Adjust player's score (only) based on the card matchup."""

        if SpecialValue.SPECIAL in (player_card.value, enemy_card.value):
            return
        
        elif (player_card.value in (SpecialValue.KISS, SpecialValue.WIN) or
                enemy_card.value in (SpecialValue.KISS, SpecialValue.LOSE)):
            self._win(player, player_card.suit)
            self._win(player, enemy_card.suit)

        elif (player_card.value == SpecialValue.LOSE or
                enemy_card.value == SpecialValue.WIN):
            self._lose(player, player_card.suit)
            
        elif player_card.value > enemy_card.value:
            self._win(player, player_card.suit)
            self._win(player, enemy_card.suit)

        elif player_card.value < enemy_card.value:
            self._lose(player, player_card.suit)

    def _win(self, player, suit, value=10):
        """Record a win for player in suit for value points (default: 10)."""
        if suit != SpecialSuit.SPECIAL:
            self.score[player][self.suits.index(suit)] += value

    def _lose(self, player, suit):
        """Record a loss for player in suit of 10 points."""
        self._win(player, suit, -10)
