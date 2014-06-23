import os

class Statistics:

    """Track player statistics.
    
    Attributes:
      wins       -- total number of games won
      played     -- total number of games played
      win_streak -- current number of games won in a row
      suits      -- { 'name' : (wins, losses, draws) }
      
    Methods:
      record_game -- note the end of a game
      
    """
    
    def __init__(self, filename=None):
        self.wins = 0
        self.played = 0
        self.win_streak = 0
        self.suits = {}
        self._load(filename)
    
    def record_game(self, score, player_index):
        """Note the end of a game."""
        self.played += 1
        if score.total(player_index) > score.total(player_index-1):
            self.wins += 1
            self.win_streak += 1
        else:
            self.win_streak = 0
        for i, suit in enumerate(score.suits):
            try:
                suit_win, suit_loss, suit_draw = self.suits[suit]
            except KeyError:
                suit_win, suit_loss, suit_draw = 0, 0, 0
            psuit = score.scores[player_index][i]
            dsuit = score.scores[player_index-1][i]
            if psuit > dsuit:
                suit_win += 1
            elif psuit < dsuit:
                suit_loss += 1
            else:
                suit_draw += 1
            self.suits[suit] = (suit_win, suit_loss, suit_draw)
        self._save()
        
    def _load(self, filename):
        if filename is None:
            filename = os.path.join("player", "stats.txt")
        self.filename = filename
        if not os.path.isfile(filename):
            return
        f = open(filename, 'r')
        try:
            self.wins = int(f.readline().strip())
            self.played = int(f.readline().strip())
            self.win_streak = int(f.readline().strip())
            for line in f.readlines():
                match = re.match('(.+):(\d+),(\d+),(\d+)', line)
                if match is not None:
                    self.suits[match.group(1)] = (int(match.group(2)),
                                                  int(match.group(3)),
                                                  int(match.group(4)))
        finally:
            f.close()
            
    def _save(self):
        f = open(self.filename, 'w')
        try:
            f.write("%s\n%s\n%s\n" % (self.wins, self.played, self.win_streak))
            for suit, (wins, losses, draws) in self.suits.items():
                f.write("%s:%s,%s,%s\n" % (suit, wins, losses, draws))
        finally:
            f.close()
    
