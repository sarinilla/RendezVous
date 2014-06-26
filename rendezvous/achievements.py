import os
import re
import warnings


from rendezvous import AchieveType, AchievementSyntaxWarning, FileReader
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
          self.count      -- number of games or cards that must match
          self.alignment  -- from Alignment
          self.suit       -- suit name or from SpecialSuit
          self.operator   -- from Operator (only < or >=)
          self.value      -- SpecialValue.WIN/LOSE or numeric
          
        Also generates the description if needed.
        
        """
        code = code_string.upper()
        def remove_caps(string):
            """Return the given string with its original capitalization."""
            i = code.index(string)
            return code_string[i:i+len(string)]

        # Statistics Achievements
        match = re.match("(PLAY|WIN|STREAK)\s*(\d+)\s*(\w*)", code)
        if match is not None:
            if match.group(1) == "PLAY": 
                self.type = AchieveType.PLAY
            elif match.group(1) == "WIN":
                self.type = AchieveType.WIN
            else: #if match.group(1) == "STREAK":
                self.type = AchieveType.STREAK
            self.count = int(match.group(2))
            if match.group(3):
                self.suit = remove_caps(match.group(3))
            else:
                self.suit = SpecialSuit.ANY

        # Round Achievements
        elif code.startswith("USE") or code.startswith("WAIT"):
            match = re.match("(USE|WAIT)\s*(\d*)\s*(FRIENDLY|ENEMY)?\s*(.*)", code)
            self.type = (AchieveType.USE if match.group(1) == "USE"
                         else AchieveType.WAIT)
            
            try:
                self.count = int(match.group(2))
            except ValueError:
                self.count = 1
                
            if "ENEMY" in code:
                self.alignment = Alignment.ENEMY
            else:
                self.alignment = Alignment.FRIENDLY

            self.suit = remove_caps(match.group(4))
            if not self.suit:
                self.suit = SpecialSuit.ANY

        # Score Achievements
        else:
            self.type = AchieveType.SCORE
            
            self.count = 1
            if "ONLY" in code:
                self.count = 0
            
            if "ENEMY" in code:
                self.alignment = Alignment.ENEMY
            else:
                self.alignment = Alignment.FRIENDLY
                
            if "<" in code:
                self.operator = Operator.LESS_THAN
            elif "=" in code and ">" not in code:
                self.operator = Operator.EXACTLY
            else:
                self.operator = Operator.AT_LEAST
                
            self.suit = SpecialSuit.TOTAL
            self.value = None  # easy parsing of double suits
            if "EACH" in code:
                self.suit = SpecialSuit.EACH
            elif "ANY" in code:
                self.suit = SpecialSuit.ANY
            elif "ONE" in code:
                self.suit = SpecialSuit.ONE
            else:
                keywords = '(PLAY|WIN|STREAK|\d|ENEMY|FRIENDLY|<|>|=|ONLY|EACH|ANY|ONE|TOTAL|WIN|LOSE|\s)*'
                operators = '(<|>|=|\s)*'
                match = re.match(keywords + '(\w*)' + operators + "(\w*)" + keywords + "$", code)
                if match:
                    if match.group(2):
                        self.suit = remove_caps(match.group(2))
                        if match.group(4):
                            self.value = remove_caps(match.group(4))
                    elif match.group(4):
                        self.suit = remove_caps(match.group(4))
                        
            match = re.search('(\d+)', code)
            if match is not None and self.value is None:
                self.value = int(match.group(1))
            elif 'LOSE' in code:
                self.value = SpecialValue.LOSE
            elif 'WIN' in code or self.value is None:
                self.value = SpecialValue.WIN
                
        # Auto-generate description
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

        def suitindex(suit):
            """Translate a SUIT#."""
            if not suit.upper().startswith("SUIT"):
                return suit
            try:
                i = int(suit[4:])
            except ValueError:
                return suit
            if i == 1:
                return "first suit"
            elif i == 2:
                return "second suit"
            elif i == 3:
                return "third suit"
            else:
                return "%sth suit" % i

        def statsuit():
            """Translate self.suit for a Statistics Achievement."""
            if self.suit == SpecialSuit.ANY:
                return ""
            elif self.suit.upper().startswith("SUIT"):
                return " in the %s" % suitindex(self.suit)
            else:
                return " with %s" % self.suit
            
        def align():
            """Translate self.alignment."""
            if self.alignment == Alignment.FRIENDLY:
                return "your"
            return "the dealer's"
            
        def operator():
            """Translate self.operator."""
            if self.operator == Operator.LESS_THAN:
                return "less than"
            elif self.operator == Operator.EXACTLY:
                return "exactly"
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
            elif self.count == 0:
                return "only %s" % self.suit
            else:
                return self.suit
            
        # Statistics Achievements
        if self.type == AchieveType.PLAY:
            return "Play %s of RendezVous%s." % (games(), statsuit())
        elif self.type == AchieveType.WIN:
            return "Win at least %s of RendezVous%s." % (games(), statsuit())
        elif self.type == AchieveType.STREAK:
            return "Win %s of RendezVous in a row%s." % (games(), statsuit())

        # Round Achievements:
        elif self.type == AchieveType.USE:
            play = ("Play" if self.alignment == Alignment.FRIENDLY
                    else "Have the dealer play")
            card = ("card" if self.suit == SpecialSuit.ANY
                    else "%s card" % self.suit)
            if self.count == 1:
                return "%s the %s." % (play, card)
            else:
                return ("%s at least %s %ss."
                        % (play, self.count, card))
        elif self.type == AchieveType.WAIT:
            hold = ("Hold" if self.alignment == Alignment.ENEMY
                    else "Have the dealer hold")
            oalign = ("the dealer's" if self.alignment == Alignment.ENEMY
                      else "your")
            card = ("card" if self.suit == SpecialSuit.ANY
                    else "%s card" % self.suit)
            if self.count == 1:
                return "%s %s %s." % (hold, oalign, card)
            else:
                return ("%s at least %s of %s %ss."
                        % (hold, self.count, oalign, card))
        
        # Score-based Achievements
        elif self.value == SpecialValue.WIN:
            return "Win a game in %s." % suit()
        elif self.value == SpecialValue.LOSE:
            return "Lose a game in %s." % suit()
            
        elif self.suit == SpecialSuit.TOTAL:
            return ("Finish a game with %s total score %s %s."
                    % (align(), operator(), self.value))
        try:
            if self.suit.upper().startswith("SUIT"):
                return ("Finish a game with %s %s score %s %s."
                        % (align(), suitindex(self.suit),
                           operator(), int(self.value)))
            return ("Finish a game with %s score %s %s in %s." 
                    % (align(), operator(), int(self.value), suit()))
        except ValueError:  # string for self.value
            return ("Finish a game with %s %s score %s that of %s %s."
                    % (align(), suitindex(self.suit), operator(),
                       align(), suitindex(self.value)))
        
    def check(self, score, player_index, stats):
        """Return whether this Achievement has been reached."""
        if self.type == None or AchieveType.per_round(self.type):
            return False

        substats = stats.base
        if self.suit in stats.decks:
            substats = stats.decks[self.suit]
        elif self.suit in stats.suits:
            substats = stats.suits[self.suit]
        if self.type == AchieveType.PLAY:
            return substats.played >= self.count
        elif self.type == AchieveType.WIN:
            return substats.wins >= self.count
        elif self.type == AchieveType.STREAK:
            return substats.win_streak >= self.count
            
        if self.suit == SpecialSuit.EACH:
            for i, pscore in enumerate(score[player_index]):
                if not self._check(pscore, score[player_index-1][i],
                                   self._get_target(score, player_index)):
                    return False
            return True
        elif self.suit == SpecialSuit.ANY:
            for i, pscore in enumerate(score[player_index]):
                if self._check(pscore, score[player_index-1][i],
                               self._get_target(score, player_index)):
                    return True
            return False
        elif self.suit == SpecialSuit.ONE:
            found = False
            for i, pscore in enumerate(score[player_index]):
                if self._check(pscore, score[player_index-1][i],
                               self._get_target(score, player_index)):
                    if found: return False
                    found = True
            return found
        elif self.suit == SpecialSuit.TOTAL:
            if self.value in (SpecialValue.WIN, SpecialValue.LOSE):
                return self._check(score.wins(player_index),
                                   score.wins(player_index-1),
                                   self.value)
            return self._check(score.total(player_index), 
                               score.total(player_index-1),
                               self._get_target(score, player_index))
        else:  # single suit
            index = -1
            if self.suit in score.suits:
                index = score.suits.index(self.suit)
                if not self._check(score[player_index][index], 
                                   score[player_index-1][index],
                                   self._get_target(score, player_index)):
                    return False
            elif self.suit.upper().startswith("SUIT"):
                index = int(self.suit[4:]) - 1
                if not self._check(score[player_index][index], 
                                   score[player_index-1][index],
                                   self._get_target(score, player_index)):
                    return False
            if self.count > 0:  # not ONLY?
                return True
            for i, suit in enumerate(score.suits):
                if i == index: continue
                if self._check(score[player_index][i],
                               score[player_index-1][i],
                               self._get_target(score, player_index)):
                    return False
            return True

    def check_round(self, board, player_index):
        """Return whether this Achievement has been reached."""
        if self.type == None or not AchieveType.per_round(self.type):
            return False
        side = player_index
        if self.alignment == Alignment.ENEMY:
            side -= 1
        count = 0
        for i, card in enumerate(board[side]):
            if (self.suit == SpecialSuit.ANY or
                card.suit.upper() == self.suit.upper() or
                card.name.upper() == self.suit.upper()):
                if self.type == AchieveType.USE or board._wait[side][i]:
                    count += 1
                    if count >= self.count:
                        return True
        return False

    def _get_target(self, score, player_index):
        try:
            return int(self.value)
        except ValueError:
            pass
        player = player_index
        if self.alignment == Alignment.ENEMY:
            player -= 1
        elif self.value.upper().startswith("SUIT"):
            return score[player][int(self.value[4:]) - 1]
        else:
            return score[player][score.suits.index(self.value)]
    
    def _check(self, pscore, dscore, target):
        """Return whether these scores meet the requirements."""
        if self.value == SpecialValue.WIN:
            return pscore > dscore
        elif self.value == SpecialValue.LOSE:
            return pscore < dscore
        
        score = pscore if self.alignment == Alignment.FRIENDLY else dscore        
        if self.operator == Operator.LESS_THAN:
            return score < target
        elif self.operator == Operator.EXACTLY:
            return score == target
        return score >= target
    
class AchievementList:
    """List of available and accomplished Achievements.
    
    Attributes:
      available  -- list of all Achievements
      achieved   -- list of those the player has earned
      image_file -- grid of Achievement icons
      deck_image_file -- deck-specific version of image_file
      
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

        Statistic-based Requirements can optionally be followed by the name
        of a deck (as given in the filenames, not as per the [DECK-NAME] tag)
        or a suit.
          
      Score Requirements:
        * Alignment: FRIENDLY or ENEMY (default: FRIENDLY)
        * Suit: by name, or one of the following:
          - EACH -- must meet the requirements in every suit
          - ANY  -- must meet the requirements in at least one suit
          - ONE  -- must meet the requirements in exactly one suit
          - TOTAL (default) -- total score must meet the requirements
          - ONLY suit_name -- must meet the requirements only in the given suit
        * Operator: < or >= or == (default: >=)
        * Value:
          - numerical score -- must be equal to this score
          - suit name -- must be equal to the score in this suit
          - SUIT# where # is an index 1-5 -- as above
          - WIN (default) -- must beat the dealer in this suit
          - LOSE -- dealer must beat the player in this suit

      Round Requirements:
        * Command:
          - USE  -- play the given card or combination
          - WAIT -- hold the given card or combination to the next round
        * Number of cards that must meet the requirements in a single round
          (default: 1)
        * Alignment: FRIENDLY or ENEMY (default: FRIENDLY)
        * Card Type:
          - suit name (e.g. "Boyfriend")
          - suit name + value (e.g. "Boyfriend 10")
          - name of special card (e.g. "Perfume")
      
      
    Accomplished Achievements File Format:  Unlocked.txt
    
      Note: This file is created as needed to store the player's data.
    
      [ACH-NAME]Name of Achievement
      
    """
    
    def __init__(self, player_file=None, deck="Standard"):
        self._base_available_file = os.path.join("data", "Achievements.txt")
        self.image_file = os.path.join("data", "Achievements.png")
        self._base_available = []
        self._read_available(self._base_available, self._base_available_file)
        self.load_deck(deck)
        if player_file is None:
            self._unlocked_file = os.path.join("player", "unlocked.txt")
        else: self._unlocked_file = player_file
        self._read_unlocked()

    @property
    def available(self):
        """Return the full list of available Achievements."""
        return self._deck_available + self._base_available
        
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
        
    def check_round(self, board, player_index):
        """Return list of Achievements newly reached in this round."""
        reached = []
        for achievement in self.available:
            if achievement not in self.achieved:
                if achievement.check_round(board, player_index):
                    reached.append(self.achieve(achievement))
        return reached

    def deck_specific(self, achievement):
        """Return boolean indicating whether achievement is deck-specific."""
        return achievement in self._deck_available

    def get_achievement_texture(self, achievement):
        """Return (L, B, W, H) rectangle for the given Achievement."""
        try:
            index = self._base_available.index(achievement)
        except ValueError:
            index = self._deck_available.index(achievement)
        return (128 * int(index / 8), 1024 - 128 * (index % 8 + 1), 128, 128)

    def load_deck(self, deck_base):
        """Read the deck-specific Achievements."""
        self._deck_available_file = os.path.join("data", "decks", str(deck_base) + "Achievements.txt")
        self.deck_image_file = os.path.join("data", "decks", str(deck_base) + "Achievements.png")
        self._deck_available = []
        self._read_available(self._deck_available, self._deck_available_file)
        
    def _read_available(self, array, filename):
        """Populate self.available with all available Achievements."""
        name = description = code = ""
        for (tag, value) in FileReader(filename):
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
                array.append(Achievement(name, description, value, code))
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
        for (tag, value) in FileReader(self._unlocked_file):
            if tag == "ACH-NAME":
                self.achieved.append(value)
            else:
                warnings.warn("Unknown tag in unlock file: %s" % tag,
                              AchievementSyntaxWarning)
