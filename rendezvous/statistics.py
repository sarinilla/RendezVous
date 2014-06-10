import os

class Statistics:

    """Track player statistics.
    
    Attributes:
      wins       -- total number of games won
      played     -- total number of games played
      win_streak -- current number of games won in a row
      
    Methods:
      record_game -- note the end of a game
      
    """
    
    def __init__(self, filename=None):
        self.wins = 0
        self.played = 0
        self.win_streak = 0
        self._load(filename)
    
    def record_game(self, score, player_index):
        """Note the end of a game."""
        self.played += 1
        if score.total(player_index) > score.total(player_index-1):
            self.wins += 1
            self.win_streak += 1
        else:
            self.win_streak = 0
        self._save()
        
    def _load(self, filename):
        if filename is None:
            filename = os.path.join("player", "stats.txt")
        self.filename = filename
        if not os.path.isfile(filename):
            return
        f = open(filename, 'r')
        try:
            self.wins, self.played, self.win_streak = [int(s.strip())
                                                       for s in f.readlines()]
        finally:
            f.close()
            
    def _save(self):
        f = open(self.filename, 'w')
        try:
            f.write("%s\n%s\n%s\n" % (self.wins, self.played, self.win_streak))
        finally:
            f.close()
    
