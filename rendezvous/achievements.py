import os
import re
import warnings


from rendezvous import AchieveType, AchievementSyntaxWarning, FileReader
from rendezvous import SpecialSuit, SpecialValue, Operator, Alignment


class AchievementCriterion:
    
    """A specific criterion that must be met to earn an Achievement.

    Attributes:
      type       -- one of the AchieveType enumerations
      count      -- number of games or cards that must meet the criterion
      alignment  -- one of the Alignment enumerations
      suit       -- name of a suit or deck, or from SpecialSuit
      operator   -- from Operator (< or >= or ==)
      value      -- value to compare the suit to, or from SpecialValue

    Note that not all attributes apply to all Achievement types.
      
    Methods:
      check       -- determine whether its been reached this game
      check_round -- determine whether its been reached this round

    """

    def __init__(self, code):
        self._parse_code(code)
        
    def _parse_code(self, code_string):
        """Parse the requirements for this Achievement."""
        code = code_string.upper()
        def remove_caps(string):
            """Return the given string with its original capitalization."""
            i = code.index(string)
            return code_string[i:i+len(string)]

        # Statistics Achievements
        match = re.match("(PLAY|WIN|LOSE|DRAW|STREAK)\s*(STREAK)?\s*(\d*)\s*(\w*)", code)
        if match is not None:
            if match.group(1) == "PLAY": 
                self.type = AchieveType.PLAY
            elif match.group(1) == "WIN":
                self.type = AchieveType.WIN
            elif match.group(1) == "LOSE":
                self.type = AchieveType.LOSE
            elif match.group(1) == "DRAW":
                self.type = AchieveType.DRAW
            else: #if match.group(1) == "STREAK":
                self.type = AchieveType.STREAK
                self.value = AchieveType.WIN

            if match.group(2):
                self.value = self.type
                self.type = AchieveType.STREAK

            self.count = 1
            if match.group(3):
                self.count = int(match.group(3))
            
            if match.group(4):
                self.suit = remove_caps(match.group(4))
            else:
                self.suit = SpecialSuit.ANY

        # Round Achievements
        elif code.startswith("USE") or code.startswith("WAIT"):
            match = re.match("(USE|WAIT)\s*(\d*)\s*(FRIENDLY|ENEMY)?\s*(.*?)\s*(([<>=]+)\s*(\d*))?\s*$", code)
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

            self.operator = Operator.AT_LEAST
            if match.group(6):
                if '<' in match.group(6):
                    self.operator = Operator.LESS_THAN
                elif '<' not in match.group(6):
                    self.operator = Operator.EXACTLY

            self.value = 0
            if match.group(7):
                self.value = int(match.group(7))



        # Score Achievements
        else:
            self.type = AchieveType.SCORE
            match = re.match('(FRIENDLY|ENEMY)?\s*(EACH|ANY|ONE|TOTAL|ONLY)?\s*(.*?)\s*([<>=]+)?\s*(WIN|LOSE|DRAW|SUIT\d+|\d+)\s*$', code)
            if match is None:
                match = re.match('(FRIENDLY|ENEMY)?\s*(EACH|ANY|ONE|TOTAL|ONLY)?\s*(.*?)\s*([<>=]+)\s*(WIN|LOSE|DRAW|SUIT\d+|\d+|.+)\s*$', code)
                if match is None:
                    match = re.match('(FRIENDLY|ENEMY)?\s*(EACH|ANY|ONE|TOTAL|ONLY)?\s*(.*?)(\s*)(\s*)$', code)
            
            self.alignment = Alignment.FRIENDLY
            if "ENEMY" == match.group(1):
                self.alignment = Alignment.ENEMY
                
            self.count = 1
            if "ONLY" == match.group(2):
                self.count = 0

            self.suit = SpecialSuit.TOTAL
            if match.group(2):
                self.suit = match.group(2)
                if self.suit == "EACH":
                    self.suit = SpecialSuit.EACH
                elif self.suit == "ANY":
                    self.suit = SpecialSuit.ANY
                elif self.suit == "ONE":
                    self.suit = SpecialSuit.ONE
                elif self.suit == "TOTAL":
                    self.suit = SpecialSuit.TOTAL
            if match.group(3):
                self.suit = match.group(3)
                if not self.suit.startswith("SUIT"):
                    self.suit = remove_caps(self.suit)
            
            self.operator = Operator.AT_LEAST
            if match.group(4):
                if "<" in match.group(4):
                    self.operator = Operator.LESS_THAN
                elif ">" not in match.group(4):
                    self.operator = Operator.EXACTLY

            self.value = SpecialValue.WIN
            if match.group(5):
                self.value = match.group(5)
                if self.value == 'WIN':
                    self.value = SpecialValue.WIN
                elif self.value == 'LOSE':
                    self.value = SpecialValue.LOSE
                elif self.value == 'DRAW':
                    self.value = SpecialValue.DRAW
                else:
                    self.value = remove_caps(self.value)
                try:
                    self.value = int(self.value)
                except ValueError:
                    pass
            
    def __str__(self):
        """Automatically generate a human-readable description."""
        return self.describe()

    def describe(self, secondary=False):
        """Automatically generate a human-readable description.

        Arguments:
          secondary -- True if the criterion is not the first in a list

        """
        
        def plural(number, string):
            """Return e.g. 'a game', 'an apple', '3 apples'."""
            if number == 1:
                if string[0] in "aeiou":
                    return "an %s" % string
                return "a %s" % string
            return "%s %ss" % (number, string)
            
        def games(count=self.count):
            """Translate self.count."""
            if not secondary:
                return plural(count, "game")
            elif count == 1:
                return "it"
            else:
                return "them"

        def RV():
            return " of RendezVous" if not secondary else ""

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
            
        def suit(include_alignment=False):
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
                return "only %s" % suitindex(self.suit)
            elif include_alignment:
                return "%s %s" % (align(), suitindex(self.suit))
            else:
                return suitindex(self.suit)

        def outcome(typ):
            """Translate WIN/LOSE/DRAW/PLAY."""
            string = (typ)
            if typ in (AchieveType.WIN, SpecialValue.WIN):
                string = "Win"
            elif typ in (AchieveType.LOSE, SpecialValue.LOSE):
                string = "Lose"
            elif typ in (AchieveType.DRAW, SpecialValue.DRAW):
                string = "Tie"
            elif typ == AchieveType.PLAY:
                string = "Play"
            return string.lower() if secondary else string
            
        # Statistics Achievements
        if self.type == AchieveType.STREAK:
            return ("%s %s%s in a row%s"
                    % (outcome(self.value), games(), RV(), statsuit()))
        elif AchieveType.stats(self.type):
            return ("%s %s%s%s"
                    % (outcome(self.type), games(), RV(), statsuit()))

        # Round Achievements:
        elif self.type == AchieveType.USE:
            play = ("Play" if self.alignment == Alignment.FRIENDLY
                    else "Have the dealer play")
            if secondary: play = play.lower()
            card = ("card" if self.suit == SpecialSuit.ANY
                    else "%s card" % self.suit)
            value = (" with a value %s %s" % (operator(), self.value)
                     if self.value > 0 else "")
            if self.count == 1:
                if self.value > 0:
                    return "%s a %s%s" % (play, card, value)
                return "%s the %s" % (play, card)
            else:
                return ("%s at least %s %ss%s"
                        % (play, self.count, card, value))
        elif self.type == AchieveType.WAIT:
            hold = ("Hold" if self.alignment == Alignment.ENEMY
                    else "Have the dealer hold")
            oalign = ("the dealer's" if self.alignment == Alignment.ENEMY
                      else "your")
            card = ("card" if self.suit == SpecialSuit.ANY
                    else "%s card" % self.suit)
            value = ("with a value %s %s" % (operator(), self.value)
                     if self.value > 0 else "")
            if self.count == 1:
                return "%s %s %s%s" % (hold, oalign, card, value)
            else:
                return ("%s at least %s of %s %ss%s"
                        % (hold, self.count, oalign, card, value))
        
        # Score-based Achievements
        elif self.value in SpecialValue.all():
            return "%s %s in %s" % (outcome(self.value), games(1), suit(True))
        
        elif self.suit == SpecialSuit.TOTAL:
            return ("%s %s with %s total score %s %s"
                    % (outcome("Finish"), games(1), align(),
                       operator(), self.value))
        try:
            self.value = int(self.value)
        except ValueError:  # string for self.value
            if self.suit in SpecialSuit.all():
                return ("%s %s with %s score in %s %s that of %s %s"
                        % (outcome("Finish"), games(1), align(), suit(),
                           operator(), align(), suitindex(self.value)))
            return ("%s %s with %s score %s that of %s %s"
                    % (outcome("Finish"), games(1), suit(True), operator(),
                       align(), suitindex(self.value)))
        else:  # value is integer
            if self.suit.upper().startswith("SUIT"):
                return ("%s %s with %s score %s %s"
                        % (outcome("Finish"), games(1), suit(True),
                           operator(), self.value))
            return ("%s %s with %s score %s %s in %s" 
                    % (outcome("Finish"), games(1), align(),
                       operator(), self.value, suit()))
        
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
        elif self.type == AchieveType.LOSE:
            return substats.losses >= self.count
        elif self.type == AchieveType.DRAW:
            return substats.draws >= self.count
        elif self.type == AchieveType.STREAK:
            if self.value == AchieveType.WIN:
                return substats.win_streak >= self.count
            elif self.value == AchieveType.LOSE:
                return substats.lose_streak >= self.count
            elif self.value == AchieveType.DRAW:
                return substats.draw_streak >= self.count
            
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
            if self.value in SpecialValue.all():
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
            if self.suit != SpecialSuit.ANY:
                if not (card.suit.upper() == self.suit.upper() or
                        card.name.upper() == self.suit.upper()):
                    continue
            if self.value > 0:
                if not self._check(card.value, card.value, self.value):
                    continue
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
        elif self.value == SpecialValue.DRAW:
            return pscore == dscore
        
        score = pscore if self.alignment == Alignment.FRIENDLY else dscore        
        if self.operator == Operator.LESS_THAN:
            return score < target
        elif self.operator == Operator.EXACTLY:
            return score == target
        return score >= target


class Achievement:
    """An accomplishment to shoot for while playing.
    
    Attributes:
      name        -- human-readable name of the Achievement
      description -- human-readable description of the requirements
      criteria    -- list of AchievementCriterion
      reward      -- name of the SpecialCard to unlock, or None
      
    Methods:
      check       -- determine whether this Achievement has been reached
      check_round -- determine whether its been reached this round
    
    """
    
    def __init__(self, name, description='', reward=None, code=''):
        self.name = name
        self.description = description
        self._override_description = self.description != ''
        self.reward = reward
        self.criteria = []
        if isinstance(code, list):
            for crit in code:
                self._parse_code(crit)
        elif code:
            self._parse_code(code)

    def __getattr__(self, name):
        """Allow easy (backwards-compatible) access to a single criterion."""
        if name == 'type':
            if not self.criteria:
                return None
            elif len(self.criteria) > 1:
                return AchieveType.MULTIPLE
        if self.criteria:
            return getattr(self.criteria[0], name)
        raise AttributeError(name)
        
    def __str__(self):
        return self.name
        
    def __repr__(self):
        return self.__class__.__name__ + repr((self.name, self.description,
                                               self.reward))
        
    def __eq__(self, other):
        return self.name == str(other)

    def _parse_code(self, code):
        """Parse the given code into a single criterion."""
        self.criteria.append(AchievementCriterion(code))
                
        # Auto-update description
        if not self._override_description:
            self.description = self._describe()
            
    def _describe(self):
        """Automatically generate a human-readable description."""
        if not self.criteria: return ""
        strings = [c.describe(i!=0) for i, c in enumerate(self.criteria)]
        if len(self.criteria) > 1:
            if AchieveType.per_round(self.criteria[0].type):
                strings[1] = "in the same round " + strings[1]
        return " and ".join(strings) + "."
        
    def check(self, score, player_index, stats):
        """Return whether this Achievement has been reached."""
        if not self.criteria:
            return False
        for crit in self.criteria:
            if not crit.check(score, player_index, stats):
                return False
        return True

    def check_round(self, board, player_index):
        """Return whether this Achievement has been reached."""
        if not self.criteria:
            return False
        for crit in self.criteria:
            if not crit.check_round(board, player_index):
                return False
        return True
    
class AchievementList(object):
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
      [ACH-CODE]Requirements for Achievement (one or more, see below)
      [ACH-REWARD]Name of Special Card
      
      If there is no unlockable Special Card associated with this
      Achievement, then the [ACH-REWARD] tag should be blank, like this:
      
      [ACH-REWARD]
      
      
    Requirement Code Syntax:
    
      The [ACH-CODE] tag should be given in the following format. If there
      is no requirement given, then the achievement cannot be automatically
      earned (i.e. it must be hard-coded somewhere as a special achievement)

      If multiple [ACH-CODE] tags are given, then all requirements must be
      met in the SAME round or game in order to earn the achievement.
      
      Statistic Requirements: 
        PLAY # -- play at least # games
        WIN #  -- win at least # games
        STREAK # -- win at least # games in a row
        LOSE # -- lose at least # games
        LOSE STREAK # -- lose at least # games in a row
        DRAW # -- tie at least # games
        DRAW STREAK # -- tie at least # games in a row

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
          - DRAW -- player and dealer must tie in this suit

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
          - value operator (e.g. "== 5")
      
      
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
            self._check_special()
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
        if reached:
            reached.extend(self._check_special())
        return reached
        
    def check_round(self, board, player_index):
        """Return list of Achievements newly reached in this round."""
        reached = []
        for achievement in self.available:
            if achievement not in self.achieved:
                if achievement.check_round(board, player_index):
                    reached.append(self.achieve(achievement))
        if reached:
            reached.extend(self._check_special())
        return reached

    def _check_special(self):
        """Check for the special Secret Rendezvous Achievement."""
        if "Secret RendezVous" in self.achieved:
            return []
        if "Standard" in self.deck_image_file:
            return []
        for achievement in self._deck_available:
            if achievement.reward is not None:
                if achievement not in self.achieved:
                    return []
        return [self["Secret RendezVous"]]

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
        try:
            self._read_available(self._deck_available, self._deck_available_file)
        except EnvironmentError:
            pass  # No file?  ok...
        
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
