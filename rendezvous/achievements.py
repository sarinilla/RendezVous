import os
import re
import warnings


from rendezvous import AchieveType, AchievementSyntaxWarning
from rendezvous import SpecialSuit, SpecialValue, Operator, Alignment


class Achievement:
    """An accomplishment to shoot for while playing.
    
    Attributes:
      name        -- human-readable name of the Achievement
      description -- human-readable description of the requirements
      reward      -- name of the SpecialCard to unlock, or None
      
    Methods:
      check       -- determine whether this Achievement has been reached
    
    """
    
    def __init__(self, name, description='', reward=None, code=''):
        self.name = name
        self.description = description
        self.reward = reward
        self.type = None
        if code:
            self._parse_code(code)
        
    def __str__(self):
        return self.name
        
    def __repr__(self):
        return self.__class__.__name__ + repr((self.name, self.description,
                                               self.reward))
        
    def __eq__(self, other):
        return self.name == str(other)
        
    def _parse_code(self, code_string):
        """Parse the requirements for this Achievement.
        
        Outputs:
          self.type       -- from AchieveType
          self.count      -- number of games that must meet the requirement
          self.alignment  -- from Alignment
          self.suit       -- suit name or from SpecialSuit
          self.operator   -- from Operator (only < or >=)
          self.value      -- SpecialValue.WIN/LOSE or numeric
          
        Also generates the description if needed.
        
        """
        
        code = code_string.upper()
        if "PLAY" == code[:4]: 
            self.type = AchieveType.PLAY
            self.count = int(code[5:])
        elif "WIN" == code[:3]: 
            self.type = AchieveType.WIN
            self.count = int(code[4:])
        elif "STREAK" == code[:6]:
            self.type = AchieveType.STREAK
            self.count = int(code[7:])
        else:
            self.type = AchieveType.SCORE
            self.count = 1
            
            if "ENEMY" in code:
                self.alignment = Alignment.ENEMY
            else:
                self.alignment = Alignment.FRIENDLY
                
            if "<" in code:
                self.operator = Operator.LESS_THAN
            else:
                self.operator = Operator.AT_LEAST
                
            self.suit = SpecialSuit.TOTAL
            if "EACH" in code:
                self.suit = SpecialSuit.EACH
            elif "ANY" in code:
                self.suit = SpecialSuit.ANY
            elif "ONE" in code:
                self.suit = SpecialSuit.ONE
            else:
                keywords = '(PLAY|WIN|STREAK|\d|ENEMY|FRIENDLY|<|>=|EACH|ANY|ONE|TOTAL|WIN|LOSE|\s)*'
                match = re.match(keywords + '(\w*?)' + keywords + "$", code)
                if match and match.group(2):
                    i = code.index(match.group(2))
                    self.suit = code_string[i:i+len(match.group(2))]
                        
            match = re.search('(\d+)', code)
            if match:
                self.value = int(match.group(1))
            elif 'LOSE' in code:
                self.value = SpecialValue.LOSE
            else:
                self.value = SpecialValue.WIN
                
        
        if not self.description:
            self.description = self._describe()
            
    def _describe(self):
    
        """Automatically generate a human-readable description."""
        
        def plural(number, string):
            """Return e.g. 'a game', 'an apple', '3 apples'."""
            if number == 1:
                if string[0] in "aeiou":
                    return "an %s" % string
                return "a %s" % string
            return "%s %ss" % (number, string)
            
        def games():
            """Translate self.count."""
            return plural(self.count, "game")
            
        def align():
            """Translate self.alignment."""
            if self.alignment == Alignment.FRIENDLY:
                return "your"
            return "the dealer's"
            
        def operator():
            """Translate self.operator."""
            if self.operator == Operator.LESS_THAN:
                return "less than"
            return "at least"
            
        def suit():
            """Translate self.suit."""
            if self.suit == SpecialSuit.EACH:
                return "every suit"
            elif self.suit == SpecialSuit.ANY:
                return "any suit"
            elif self.suit == SpecialSuit.ONE:
                return "exactly one suit"
            elif self.suit == SpecialSuit.TOTAL:
                return "overall score"
            else:
                return self.suit
            
        # Statistics Achievements
        if self.type == AchieveType.PLAY:
            return "Play %s of RendezVous." % games()
        elif self.type == AchieveType.WIN:
            return "Win at least %s of RendezVous." % games()
        elif self.type == AchieveType.STREAK:
            return "Win %s of RendezVous in a row."  % games()
        
        # Score-based Achievements
        elif self.value == SpecialValue.WIN:
            return "Win %s in %s." % (games(), suit())
        elif self.value == SpecialValue.LOSE:
            return "Lose %s in %s." % (games(), suit())
            
        elif self.suit == SpecialSuit.TOTAL:
            return ("Finish %s with %s total score %s %s."
                    % (games(), align(), operator(), self.value))
        else:
            return ("Finish %s with %s score %s %s in %s." 
                    % (games(), align(), operator(), self.value, suit()))
        
    def check(self, score, player_index, stats):
        """Return whether this Achievement has been reached."""
        if self.type == None:
            return False
        if self.type == AchieveType.PLAY:
            return stats.played >= self.count
        elif self.type == AchieveType.WIN:
            return stats.wins >= self.count
        elif self.type == AchieveType.STREAK:
            return stats.win_streak >= self.count
            
        if self.suit == SpecialSuit.EACH:
            for i, pscore in enumerate(score[player_index]):
                if not self._check(pscore, score[player_index-1][i]):
                    return False
            return True
        elif self.suit == SpecialSuit.ANY:
            for i, pscore in enumerate(score[player_index]):
                if self._check(pscore, score[player_index-1][i]):
                    return True
            return False
        elif self.suit == SpecialSuit.ONE:
            found = False
            for i, pscore in enumerate(score[player_index]):
                if self._check(pscore, score[player_index-1][i]):
                    if found: return False
                    found = True
            return found
        elif self.suit in score.suits:
            i = score.suits.index(self.suit)
            return self._check(score[player_index][i], 
                               score[player_index-1][i])
        else:  #if self.suit == SpecialSuit.TOTAL:
            return self._check(score.total(player_index), 
                               score.total(player_index-1))
    
    def _check(self, pscore, dscore):
        """Return whether these scores meet the requirements."""
        if self.value == SpecialValue.WIN:
            return pscore > dscore
        elif self.value == SpecialValue.LOSE:
            return pscore < dscore
        score = pscore if self.alignment == Alignment.FRIENDLY else dscore
        if self.operator == Operator.LESS_THAN:
            return score < self.value
        return score >= self.value
    
class AchievementList:
    """List of available and accomplished Achievements.
    
    Attributes:
      available  -- list of all Achievements
      achieved   -- list of those the player has earned
      image_file -- grid of Achievement icons
      
    Methods:
      unlocked  -- return whether the given SpecialCard has been unlocked
      achieve   -- mark the Achievement earned and return it
      check     -- return list of Achievements newly reached (or [])
      get_achievement_texture -- return (L, B, W, H) for the Achievement
      
    Available Achievements File Format:  Achievements.txt
    
      [ACH-NAME]Name of Achievement
      [ACH-DESC]Full readable description (optional)
      [ACH-CODE]Requirements for Achievement (optional, see below)
      [ACH-REWARD]Name of Special Card
      
      If there is no unlockable Special Card associated with this
      Achievement, then the [ACH-REWARD] tag should be blank, like this:
      
      [ACH-REWARD]
      
      
    Requirement Code Syntax:
    
      The [ACH-CODE] tag should be given in the following format. If there
      is no requirement given, then the achievement cannot be automatically
      earned (i.e. it must be hard-coded somewhere as a special achievement)
      
      Statistic Requirements: 
        PLAY # -- play at least # games
        WIN #  -- win at least # games
        STREAK # -- win at least # games in a row
          
      Score Requirements:
        * Alignment: FRIENDLY or ENEMY (default: FRIENDLY)
        * Suit: by name, or one of the following:
          - EACH -- must meet the requirements in every suit
          - ANY  -- must meet the requirements in at least one suit
          - ONE  -- must meet the requirements in exactly one suit
          - TOTAL (default) -- total score must meet the requirements
        * Operator: < or >= (default: >=)
        * Value: numerical score, or WIN or LOSE (default: WIN)
      
      
    Accomplished Achievements File Format:  Unlocked.txt
    
      Note: This file is created as needed to store the player's data.
    
      [ACH-NAME]Name of Achievement
      
    """
    
    def __init__(self, player_file=None):
        self._available_file = os.path.join("data", "Achievements.txt")
        self.image_file = os.path.join("data", "Achievements.png")
        self._read_available()
        if player_file is None:
            self._unlocked_file = os.path.join("player", "unlocked.txt")
        else: self._unlocked_file = player_file
        self._read_unlocked()
        
    def __len__(self):
        return len(self.available)
        
    def __getitem__(self, key):
        for achievement in self.available:
            if achievement.name == str(key):
                return achievement
                
    def __iter__(self):
        return iter(self.available)
        
    def unlocked(self, reward):
        """Return whether the given (or named) SpecialCard is unlocked.

        No rewards are unlocked until the first Achievement has been earned.

        """
        if self.achieved == []:
            return False  # beginner mode; no Specials
        for achievement in self.available:
            if achievement.reward == str(reward):  # str is name of SpecialCard
                return achievement in self.achieved
        return True  # default to unlocked if not a reward
        
    def achieve(self, achievement):
        """Unlock the selected achievement and return the Achievement."""
        achievement = self[achievement]  # find by name if needed
        if achievement not in self.achieved:
            self.achieved.append(achievement.name)
            try:
                f = open(self._unlocked_file, 'a')
                f.write('[ACH-NAME]%s\n' % achievement.name)
            finally:
                f.close()
        return achievement
        
    def check(self, score, player_index, stats):
        """Return list of Achievements newly reached in this game."""
        reached = []
        for achievement in self.available:
            if achievement not in self.achieved:
                if achievement.check(score, player_index, stats):
                    reached.append(self.achieve(achievement))
        return reached

    def get_achievement_texture(self, achievement):
        """Return (L, B, W, H) rectangle for the given Achievement."""
        index = self.available.index(achievement)
        return (128 * int(index / 8), 1024 - 128 * (index % 8 + 1), 128, 128)
        
    def _reader(self, filename):
        """Read a file and yield (tag, value) pairs."""
        file = open(filename, 'r')
        try:
            for line in file:
                if line == "\n":
                    continue
                match = re.search('\[(.*)\](.*)\n', line)
                if not match:
                    warnings.warn("Unexpected text in %s: %s" 
                                  % (filename, line),
                                  SyntaxWarning)
                    continue

                yield(match.group(1).upper(), match.group(2))
        finally:
            file.close()
        
    def _read_available(self):
        """Populate self.available with all available Achievements."""
        self.available = []
        reader = self._reader(self._available_file)
        name = description = code = ""
        for (tag, value) in reader:
            if tag == "ACH-NAME":
                name = value
            elif tag == "ACH-DESC":
                description = value
            elif tag == "ACH-CODE":
                code = value
            elif tag == "ACH-REWARD":
                if not (name and description + code):
                    warnings.warn("Incomplete achievement definition:\nName: %s\nDescription: %s\nCode: %s\nReward: %s" % (name, description, code, value), AchievementSyntaxWarning)
                if not value:
                    value = None
                self.available.append(Achievement(name, description, value, code))
                name = description = code = ""
            else:
                warnings.warn("Unknown tag in achievement file: %s" % tag,
                              AchievementSyntaxWarning)
    
    def _read_unlocked(self):
        """Populate self.achieved with the names of unlocked Achievements."""
        self.achieved = []
        if not os.path.isfile(self._unlocked_file):
            try:
                os.mkdir(os.path.dirname(self._unlocked_file))
            except OSError:
                pass
            f = open(self._unlocked_file, 'w')
            f.close()
        reader = self._reader(self._unlocked_file)
        for (tag, value) in reader:
            if tag == "ACH-NAME":
                self.achieved.append(value)
            else:
                warnings.warn("Unknown tag in unlock file: %s" % tag,
                              AchievementSyntaxWarning)
