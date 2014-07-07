import os
import re

from rendezvous import SpecialValue

class BaseStats(object):  # explicit subclass for 2.7 properties

    """Track statistics for a single deck or suit.
    
    Attributes:
      wins        -- total number of games won
      losses      -- total number of games lost
      played      -- total number of games played
      streak      -- current number of matching outcomes in a row
      streak_type -- SpecialValue indicating the outcome type
      best_streak -- record number of games won in a row

    Properties (calculated attributes):
      draws       -- total number of games tied
      win_streak  -- current number of games won in a row
      lose_streak -- current number of games lost in a row
      draw_streak -- current number of games tied in a row

    """

    def __init__(self, string=None):
        self.wins = 0
        self.losses = 0
        self.played = 0
        self.streak = 0
        self.streak_type = None
        self.best_streak = 0
        if string is not None:
            try:
                self._load(string)
            except:
                pass

    @property
    def draws(self):
        return self.played - self.wins - self.losses

    @property
    def win_streak(self):
        return self.streak if self.streak_type == SpecialValue.WIN else 0

    @win_streak.setter
    def win_streak(self, value):
        self.streak_type, self.streak = SpecialValue.WIN, value

    @property
    def lose_streak(self):
        return self.streak if self.streak_type == SpecialValue.LOSE else 0

    @lose_streak.setter
    def lose_streak(self, value):
        self.streak_type, self.streak = SpecialValue.LOSE, value

    @property
    def draw_streak(self):
        return self.streak if self.streak_type == SpecialValue.DRAW else 0

    @draw_streak.setter
    def draw_streak(self, value):
        self.streak_type, self.streak = SpecialValue.DRAW, value
    
    def __str__(self):
        return str((self.wins, self.losses, self.played,
                    self.streak, self.streak_type, self.best_streak))

    def __repr__(self):
        return str(self)

    def _load(self, string):
        values = tuple(int(v) for v in re.findall("[0-9]+", string))
        (self.wins, self.losses, self.played,
         self.streak, self.streak_type, self.best_streak) = values

    def record(self, player_score, dealer_score):
        """Record the end of a game."""
        if player_score > dealer_score:
            self.win()
        elif player_score < dealer_score:
            self.lose()
        else:
            self.draw()

    def win(self):
        """Record a win."""
        self.played += 1
        self.wins += 1
        self.win_streak += 1
        if self.win_streak > self.best_streak:
            self.best_streak = self.win_streak

    def lose(self):
        """Record a loss."""
        self.played += 1
        self.losses += 1
        self.lose_streak += 1

    def draw(self):
        """Record a draw."""
        self.played += 1
        self.draw_streak += 1
        

class Statistics:

    """Track player statistics.
    
    Attributes:
      base   -- BaseStats for games played/won/etc in general
      decks  -- { 'base_filename' : BaseStats for that deck }
      suits  -- { 'name' : BaseStats for that suit }
      
    Methods:
      record_game -- note the end of a game
      
    """
    
    def __init__(self, filename=None):
        self.base = BaseStats()
        self.decks = {}
        self.suits = {}
        self._load(filename)
    
    def record_game(self, deck_base, score, player_index):
        """Note the end of a game."""
        self.base.record(len(score.wins(player_index)),
                         len(score.wins(player_index-1)))
        if deck_base not in self.decks:
            self.decks[deck_base] = BaseStats()
        self.decks[deck_base].record(len(score.wins(player_index)),
                                     len(score.wins(player_index-1)))
        for i, suit in enumerate(score.suits):
            if suit not in self.suits:
                self.suits[suit] = BaseStats()
            self.suits[suit].record(score.scores[player_index][i],
                                    score.scores[player_index-1][i])
        self._save()
        
    def _load(self, filename):
        if filename is None:
            filename = os.path.join("player", "stats.txt")
        self.filename = filename
        if not os.path.isfile(filename):
            return
        f = open(filename, 'r')
        try:
            self.base = BaseStats(f.readline().strip())
            for line in f.readlines():
                match = re.match('(DECK|SUIT):(.+):(.+)', line.strip())
                if match is None: continue
                if match.group(1) == "DECK":
                    self.decks[match.group(2)] = BaseStats(match.group(3))
                else: #if match.group(1) == "SUIT":
                    self.suits[match.group(2)] = BaseStats(match.group(3))
        finally:
            f.close()
            
    def _save(self):
        f = open(self.filename, 'w')
        try:
            f.write("%s\n" % self.base)
            for deck, stats in self.decks.items():
                f.write("DECK:%s:%s\n" % (deck, stats))
            for suit, stats in self.suits.items():
                f.write("SUIT:%s:%s\n" % (suit, stats))
        finally:
            f.close()
    
