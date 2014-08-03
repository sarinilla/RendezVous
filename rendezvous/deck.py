import os
import re
import random
import copy
import warnings

from rendezvous import DeckSyntaxWarning, MissingDeckError, FileReader
from rendezvous import Operator, SpecialSuit, SpecialValue, Alignment
from rendezvous import EffectType, GameSettings, TargetField
from rendezvous.specials import Requirement, Application, Effect


class Card:
    """A single standard RendezVous card.

    Attributes:
      name        -- a user-friendly name for the card
      description -- a user-friendly description of the card's purpose
      suit        -- the name of the card's suit
      value       -- the numerical value of the card

    Methods:
      apply       -- apply an Effect to this card

    """

    def __init__(self, suit, value):
        """Set name and description based on the suit and value combination."""
        self.name = "%s %s" % (suit, value)
        self.description = "A normal %s card with value %s." % (suit, value)
        self.suit = suit
        self.value = value
        self.original = (suit, value)

    def reset(self):
        """Undo the effects of all SpecialCards."""
        self.suit, self.value = self.original
        self.description = "A normal %s card with value %s." % self.original

    def __str__(self):
        """Return the name of the card."""
        return self.name

    def __repr__(self):
        """Return the initialization statement for this Card."""
        return self.__class__.__name__ + repr((self.suit, self.value))

    def __hash__(self):
        """Hash it up for standard and special."""
        return hash("%s %s" % (self.name, self.description))
    
    def __eq__(self, other):
        """Equality rests on both suit and value."""
        try:
            return self.suit == other.suit and self.value == other.value
        except AttributeError:
            return False

    def __lt__(self, other):
        """Compare by value only."""
        return self.value < other.value

    def apply(self, effect):
        
        """Apply the given effect to this card, and update the description."""
        
        if self.value == SpecialValue.KISS:
            return
        
        if effect.effect == EffectType.BUFF:
            if effect.value in SpecialValue.all():
                self.value = effect.value
                if effect.value == SpecialValue.WIN:
                    self.description += "  Winning!"
                elif effect.value == SpecialValue.LOSE:
                    self.description += "  Losing!"
            elif self.value in SpecialValue.all():
                return
            else:
                self.value += effect.value
                if effect.value >= 0:
                    self.description += "  Buffed to %s." % self.value
                else:
                    self.description += "  Debuffed to %s." % self.value

        elif effect.effect == EffectType.MULTIPLY:
            self.value = float(self.value) * effect.value
            if effect.value > 1: self.value = int(self.value + 0.99)
            else: self.value = int(self.value)
            if effect.value == 2:
                self.description += "  Doubled."
            elif effect.value == 3:
                self.description += "  Tripled."
            elif effect.value == 0.5:
                self.description += "  Halved."
            elif effect.value > 1:
                self.description += ("  Increased to %s%% (%s)."
                                     % (int(effect.value * 100), self.value))
            else:
                self.description += ("  Reduced to %s%% (%s)."
                                     % (int(effect.value * 100), self.value))
            
        elif effect.effect == EffectType.KISS:
            self.value = SpecialValue.KISS
            self.description += "  Kissed!"
            
        elif effect.effect == EffectType.REVERSE:
            if self.value in (SpecialValue.WIN, SpecialValue.LOSE):
                self.value = -self.value
                self.description += "  Reversed."
            elif self.value in SpecialValue.all():
                return
            else:
                self.value = 11 - self.value
                self.description += "  Reversed to %s." % self.value
                
        elif effect.effect == EffectType.REPLACE:
            if isinstance(effect.value, str):
                self.suit = effect.value
                self.description += "  Replaced suit with %s." % self.suit
            elif isinstance(effect.value, int):
                self.value = effect.value
                self.description += "  Replaced value with %s." % self.value
            else:
                self.suit = effect.value.suit
                self.value = effect.value.value
                self.description += ("  Replaced by %s %s."
                                     % (self.suit, self.value))

        elif effect.effect == EffectType.SWITCH:
            self.value = effect.value
            self.description += "  Switched to %s." % self.value

        elif effect.effect == EffectType.CLONE:
            if effect.value is self:
                return
            (self.suit, self.value) = (effect.value.suit, effect.value.value)
            self.description += "  Cloned to %s." % effect.value
    

class SpecialCard(Card):

    """Extend Card for special features.

    Additional Attributes:
      requirement -- Requirement item (or combination via & and |)
      application -- Application item (or combination via & and |)
      effect      -- Effect item 

    """

    def __init__(self, name, description, requirement, application, effect):
        Card.__init__(self, SpecialSuit.SPECIAL, SpecialValue.SPECIAL)
        self.name = name
        self.description = "%s\nRequires: %s\nApplies to: %s\nEffect: %s" % \
                           (description, requirement, application, effect)
        self.requirement = requirement
        self.application = application
        self.effect = effect

    def __str__(self):
        """Return the name of the card."""
        return self.name

    def __repr__(self):
        """Return the initialization statement for this SpecialCard."""
        return self.__class__.__name__ + repr((self.name, self.description,
                                               self.requirement,
                                               self.application, self.effect))
                         
    def __eq__(self, other):
        """Equality rests on full name."""
        try:
            return self.name == other.name
        except AttributeError:
            return False

    def apply(self, effect):
        """Nothing affects a SpecialCard."""
        return

    def reset(self):
        """No effects to undo."""
        return


class Deck:
    
    """A player's deck of cards.

    Methods:
      shuffle -- reshuffle the entire deck and start from the beginning
      draw    -- return the top card from the deck

    """

    def __init__(self, definition, shuffle=True, achievements=None):
        """Prep the card list."""
        self.definition = definition
        self.achievements = achievements
        self._cards = list(definition.cards(self.achievements))
        self._next = self._draw()
        if shuffle:
            self.shuffle()

    def shuffle(self):
        """Shuffle the full deck together."""
        self._cards = list(self.definition.cards(self.achievements))
        random.shuffle(self._cards)
        self._next = self._draw()

    def suits_only(self, shuffle=True):
        """Include only the suit cards. All cards will return next shuffle."""
        self._cards = list(self.definition.cards(use_blocks=False,
                                                 skip_specials=True))
        if shuffle:
            random.shuffle(self._cards)
        self._next = self._draw()

    def _draw(self):
        """Generator; return each card in the current deck."""
        for card in self._cards:
            yield card

    def draw(self, auto_shuffle=True):
        """Return the next card in the current deck."""
        try:
            return next(self._next)
        except StopIteration:
            if not auto_shuffle:
                raise
            self.shuffle()
            return next(self._next)
        
        
class DeckDefinition:
    
    """The available cards to play with, and other deck details.

    Attributes:
      name     -- the name of the selected deck
      desc     -- brief description of the deck
      suits    -- names of all suits, in order to match the images
      values   -- all possible values, in order to match the images
      specials -- list of SpecialCards, in order to match the image

    Methods:
      cards            -- generator that returns all cards, unshuffled
      get_card_texture -- return the texture details for a specific card


    Deck Image Format:  DeckName.png
    
      The deck image file is 2048x2048 and is built on a 130x182 grid.

      The first five columns are filled with regular suit cards, with
      values from 1 to 10 vertically, top to bottom.  The suits are presented
      in the same order as they are introduced in the Deck Definition File. At
      the very bottom of each column, off of the grid rows, is a 130x130 suit
      icon.

      The next two columns are filled with up to 22 SpecialCards, in the order
      they are presented in the Deck Definition File.

      The next column contains the back of the card, KISS, WIN, and then the
      numbers greater than 10 (from 11 to 15 vertically).  The remaining grid
      spaces are currently empty.

      The next column contains the locked / unknown card, LOSE, then the
      numbers from 0 to -5 vertically.  The remaining spaces in this column are
      currently empty.

      The first row in each remaining column is currently empty.  Below that,
      the grid is sectioned into 2x2 blocks containing dealer images: the first
      row of this block contains the first suit's WIN, LOSE, and DRAW images,
      left to right.  Additional rows contain adidtional suit's dealers.


    Deck Definition File Format:  DeckName.txt

      The deck definition file contains all of the necessary details for the
      deck, in the format [TYPE-OF-INFO]Information

      The first section should contain the DECK-NAME and DECK-DESC, followed by
      five SUIT entries containing the names of the five suits.

      Next, up to 20 special cards may be defined with the following details:
        SPECIAL-NAME -- brief, human-readable name
        SPECIAL-DESC -- optional human-readable description
        SPECIAL-REQ  -- the requirements to play this card (as defined below)
        SPECIAL-APP  -- the cards this one applies to (as defined below)
        SPECIAL-EFF  -- the effect this card will have (as defined below)


    Special Card Syntax:

      Requirement:
        * Each card can have up to 3 SPECIAL-REQ tags.
        * Each SPECIAL-REQ tag consists of:
          - MIN or MAX
          - the number of cards required
          - an Application to look for

      Application:
        * Each card can have 1 or more SPECIAL-APP tags.
        * Each SPECIAL-APP tag consists of:
          - FRIENDLY, ENEMY, or ALL
          - A suit
          - A value operator (e.g. <= 3)
          - VS <another Application>
        * If the desired effect is FLUSH, then HAND can be used here.

      Effect:
        * Each card must have exactly 1 SPECIAL-EFF tag.
        * SPECIAL-EFF tag options include:
          - BUFF -- followed by an integer value
          - DEBUFF -- followed by an integer value
          - DOUBLE, TRIPLE, or HALVE
          - MULTIPLY -- followed by a decimal value
          - DIVIDE -- followed by a decimal value
          - WAIT
          - LOSE
          - WIN
          - SWITCH
          - REVERSE
          - REPLACE -- followed by the name of a suit and/or a value
          - KISS
          - CLONE
          - FLUSH

    """

    def __init__(self, name="Standard", blocked_cards=[]):
        self.name = self.base_filename = name
        self.blocked_cards = blocked_cards
        self.img_file = os.path.join("data", "decks", name + ".png")
        self.def_file = os.path.join("data", "decks", name + ".txt")
        if not os.path.isfile(self.img_file):
            raise MissingDeckError
        if not os.path.isfile(self.def_file):
            raise MissingDeckError
        self._read_definition()

    def _read_definition(self):
        """Read details from the Deck Definition File."""
        self.desc = ""
        self.suits = []
        self.values = list(range(1, 11))
        self.specials = []
        special_detail = {}
        for (tag, value) in FileReader(self.def_file):
            if tag == "DECK-NAME":
                self.name = value

            elif tag == "DECK-DESC":
                if self.desc:
                    self.desc += "\n\n"
                self.desc += value

            elif tag == "SUIT":
                try:
                    value = value[:value.index(':')].strip()
                except ValueError:
                    pass  # simple suit without details
                self.suits.append(value)

            elif tag == "SPECIAL-NAME":
                special_detail = {"name" : value, "desc" : "Special card"}
            elif tag == "SPECIAL-DESC":
                special_detail["desc"] = value
            elif tag == "SPECIAL-REQ":
                if "req" in special_detail:
                    special_detail["req"].append(value)
                else:
                    special_detail["req"] = [value]
            elif tag == "SPECIAL-APP":
                if "app" in special_detail:
                    special_detail["app"].append(value)
                else:
                    special_detail["app"] = [value]
            elif tag == "SPECIAL-EFF":
                special_detail["eff"] = value
                self.specials.append(self._parse_special(special_detail))
                special_detail = {}
            else:
                warnings.warn("Unknown tag in deck definition file: %s" % tag,
                              DeckSyntaxWarning)

    def _parse_special(self, special_detail):
        req = self._parse_requirement(special_detail["req"][0])
        for add in special_detail["req"][1:]:
            req = req & self._parse_requirement(add)
        app = self._parse_application(special_detail["app"][0])
        for add in special_detail["app"][1:]:
            app = app | self._parse_application(add)
        eff = self._parse_effect(special_detail["eff"])
        return SpecialCard(special_detail["name"], special_detail["desc"],
                           req, app, eff)

    def _parse_requirement(self, req_text):
        """[MIN|MAX] # <Application>"""
        req_text = req_text.upper()
        if req_text in ("", "ANY", "NONE", "NA", "N/A"):
            return Requirement()
        match = re.search('(MIN|MAX)?\s*(\d+)\s*(.*)', req_text)
        if not match:
            warnings.warn("Invalid requirement: %s" % req_text,
                          DeckSyntaxWarning)
            return Requirement()
        op = Operator.EXACTLY
        if match.group(1) == "MIN":
            op = Operator.AT_LEAST
        elif match.group(1) == "MAX":
            op = Operator.NO_MORE_THAN
        return Requirement(operator=op, count=int(match.group(2)),
                           style=self._parse_application(match.group(3)))

    def _parse_application(self, app_text):
        """[FRIENDLY|ENEMY|ALL] [<suit name>] [<operator> <value>] [VS <Application>]"""
        app_text = app_text.upper()
        match = re.search('(.*?)\s*VS\s*(.*)', app_text)
        opposite=None
        if match:
            opposite=self._parse_application(match.group(2))
            app_text = match.group(1)
        if app_text == "" or app_text == "ANY" or app_text == "ALL":
            return Application()
        match = re.search(
            '(FRIENDLY|ENEMY|ALL)?\s*([\w\s,]*?)\s*([\<\>=]*)\s*(\d*)\s*$', app_text)
        if not match:
            warnings.warn("Invalid application: %s" % app_text,
                          DeckSyntaxWarning)
            return Application()

        if match.group(2) == "HAND":
            return Application(suits=["HAND"])
        
        alignment = Alignment.ALL
        if match.group(1) == "FRIENDLY":
            alignment = Alignment.FRIENDLY
        elif match.group(1) == "ENEMY":
            alignment = Alignment.ENEMY
            
        suits = None
        if match.group(2) and match.group(2) != "ALL":
            suits_given = match.group(2).replace(",", " OR ").split(" OR ")
            upper_suits = [s.upper() for s in self.suits]
            suits = []
            for given in suits_given:
                given = given.strip()
                if given == "": continue  # ", or" has become " or  or "
                try:
                    suits.append(self.suits[upper_suits.index(given)])
                except ValueError:
                    warnings.warn("Invalid suit in application: %s" % given,
                                  DeckSyntaxWarning)
            if not suits:
                suits = None
                
        min_value = None
        max_value = None
        if match.group(3) == "<":
            max_value = int(match.group(4)) - 1
        elif match.group(3) == "<=":
            max_value = int(match.group(4))
        elif match.group(3) == ">":
            min_value = int(match.group(4)) + 1
        elif match.group(3) == ">=":
            min_value = int(match.group(4))
        elif match.group(3) != "":
            min_value = max_value = int(match.group(4))

        return Application(alignment=alignment, suits=suits, 
			   min_value=min_value, max_value=max_value, 
			   opposite=opposite)
            
    def _parse_effect(self, eff_text):
        words = eff_text.upper().split(' ')
        if words[0] == "BUFF":
            return Effect(EffectType.BUFF, int(words[1]))
        elif words[0] == "DEBUFF":
            return Effect(EffectType.BUFF, -int(words[1]))
        elif words[0] == "DOUBLE":
            return Effect(EffectType.MULTIPLY, 2)
        elif words[0] == "TRIPLE":
            return Effect(EffectType.MULTIPLY, 3)
        elif words[0] == "MULTIPLY":
            return Effect(EffectType.MULTIPLY, float(words[1]))
        elif words[0] == "HALVE":
            return Effect(EffectType.MULTIPLY, 0.5)
        elif words[0] == "DIVIDE":
            return Effect(EffectType.MULTIPLY, 1.0 / float(words[1]))
        elif words[0] == "WAIT":
            return Effect(EffectType.WAIT)
        elif words[0] == "LOSE":
            return Effect(EffectType.BUFF, SpecialValue.LOSE)
        elif words[0] == "WIN":
            return Effect(EffectType.BUFF, SpecialValue.WIN)
        elif words[0] == "SWITCH":
            return Effect(EffectType.SWITCH)
        elif words[0] == "REVERSE":
            return Effect(EffectType.REVERSE)
        elif words[0] == "REPLACE":
            suit = self._match_suit(' '.join(words[1:]))
            value = None
            if suit is None:
                suit = self._match_suit(' '.join(words[1:-1]))
                try: value = int(words[-1])
                except ValueError: value = None
            if suit is None:
                try: value = int(words[1])
                except ValueError: value = None
                
            if suit is None and value is None:
                warnings.warn("Invalid replacement suit/value: %s" % ' '.join(words[1:]),
                              DeckSyntaxWarning)
                return Effect()
            elif value is None:
                return Effect(EffectType.REPLACE, suit)
            elif suit is None:
                return Effect(EffectType.REPLACE, value)
            else:
                return Effect(EffectType.REPLACE, Card(suit, value))
        elif words[0] == "KISS":
            return Effect(EffectType.KISS)
        elif words[0] == "CLONE":
            return Effect(EffectType.CLONE)
        elif words[0] == "FLUSH":
            return Effect(EffectType.FLUSH)
        elif words[0] == "RANDOMIZE":
            if len(words) == 1 or words[1] == "ALL":
                return Effect(EffectType.RANDOMIZE, TargetField.ALL)
            elif words[1] == "SUIT":
                return Effect(EffectType.RANDOMIZE, TargetField.SUIT)
            elif words[1] == "VALUE":
                return Effect(EffectType.RANDOMIZE, TargetField.VALUE)
            warnings.warn("Invalid randomize target: %s" % words[1],
                          DeckSyntaxWarning)
            return Effect(EffectType.RANDOMIZE, TargetField.ALL)
        else:
            warnings.warn("Invalid special card effect: %s" % words[0])

    def _match_suit(self, suit_name):
        try:
            return self.suits[[s.upper() for s in self.suits].index(suit_name)]
        except ValueError:
            return None
        
    def cards(self, achievements=None, use_blocks=True, skip_specials=False):
        """Generator; return all card in the deck, unshuffled."""
        for suit in self.suits:
            for value in self.values:
                if not use_blocks or "%s %s" % (suit, value) not in self.blocked_cards:
                    yield Card(suit, value)
        if skip_specials: return
        for special in self.specials:
            if achievements is None or achievements.unlocked(special):
                if not use_blocks or special.name not in self.blocked_cards:
                    yield copy.copy(special)
                
    def get_special(self, name=None):
        """Return the named SpecialCard, or None."""
        if name is None:
            return copy.copy(random.choice(self.specials))
        for special in self.specials:
            if special.name == name:
                return copy.copy(special)
        return None

    def get_card(self, name):
        """Return the named Card, or None."""
        match = re.match(r'(.+) (\d+)', name)
        if match is not None:
            if match.group(1) in self.suits:
                return Card(match.group(1), int(match.group(2)))
        return self.get_special(name)

    def get_cards(self, names):
        """Return the named Cards, only if they are valid in this deck."""
        return list(filter(lambda c: c is not None,
                    [self.get_card(name) for name in names]))

    def get_card_texture(self, card):
        """Return texture details for the given card."""
        return self._get_rect(*self._get_card_loc(card))

    def get_back_texture(self):
        """Return texture details for the deck back image."""
        return self._get_rect(7, 0)

    def get_wait_texture(self):
        """Return texture details for the WAIT overlay image."""
        return self._get_rect(9, 0)
    
    def get_locked_texture(self):
        """Return texture details for the not-yet-unlocked card image."""
        return self._get_rect(8, 0)

    def get_suit_texture(self, suit):
        """Return texture details for the given suit's icon."""
        if suit in self.suits:
            suit = self.suits.index(suit)
        return (130 * suit, 0, 130, 130)

    def get_dealer_texture(self, suit, win_lose):
        """Return texture details for the dealer image.

        Arguments:
          suit -- name or index of the suit to show
          win_lose -- 1 for player won, 0 for a tie, -1 for dealer won
        """
        win_lose = [0, 2, 1][win_lose]
        if suit in self.suits:
            suit = self.suits.index(suit)
        rect = self._get_rect(9 + 2 * win_lose, 1 + 2 * suit + 1)
        return (rect[0], rect[1], rect[2] * 2, rect[3] * 2)

    def _get_card_loc(self, card):
        """Return the grid (col, row) for this card."""
        if card.value == SpecialValue.KISS:
            return (7, 1)
        elif card.value == SpecialValue.WIN:
            return (7, 2)
        elif card.value == SpecialValue.LOSE:
            return (8, 1)
        elif card.value == SpecialValue.SPECIAL:
            index = self.specials.index(card)
            if index < 11:
                return (5, index)
            else:
                return (6, index - 11)
        elif card.value > 18:
            return (7, 10)
        elif card.value > 10:
            return (7, 3 + card.value - 11)
        elif card.value < -8:
            return (8, 10)
        elif card.value < 1:
            return (8, 2 - card.value)
        else:
            return (self.suits.index(card.suit), card.value - 1)
        
    def _get_rect(self, col, row):
        """Return (left, bottom (inverted), width, height) of the given card."""
        return (130 * col, 2048 - 182 * (row + 1), 130, 182)


class DeckCatalogEntry:

    """One deck available for purchase."""
    
    def __init__(self, name, description, directory, base_filename):
        self.name = name
        self.description = description
        self.base_filename = base_filename
        self.definition = os.path.join(directory, base_filename) + ".txt"
        self.image_file = os.path.join(directory, base_filename) + ".png"
        self.icon = os.path.join(directory, base_filename) + "Icon.png"
        self.hand = os.path.join(directory, base_filename) + "Hand.png"

    @property
    def private(self):
        return 'Private' in self.base_filename

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == str(other)


class DeckCatalog:

    """List of decks available for purchase and play."""

    def __init__(self, purchased_file=None, directory=None):
        if purchased_file is None:
            purchased_file = os.path.join("player", "decks.txt")
        if directory is None:
            directory = os.path.join("data", "decks")
        self._decks = []
        self._read_available(directory)
        self._purchased = []
        self._read_purchased(purchased_file)

    @property
    def private(self):
        """Return boolean indicating whether there are any Private decks."""
        try:
            return self._has_private
        except AttributeError:
            for deck in self._decks:
                if deck.private:
                    self._has_private = True
                    break
            else:
                self._has_private = False
            return self._has_private

    @property
    def decks(self):
        """Automatically hide private decks if requested in GameSettings."""
        if GameSettings.SHOW_PRIVATE:
            return self._decks
        return list(filter(lambda d: not d.private, self._decks))

    # Shortcut to .decks as a hash[deck_name]
    def __len__(self):
        return len(self.decks)
    def __getitem__(self, name):
        return self._find_deck(name)
    def __iter__(self):
        return iter(self.decks)

    def _find_deck(self, name):
        """Locate and return a deck by name or base filename."""
        name = str(name)
        for deck in self.decks:
            if deck.name == name or deck.base_filename == name:
                return deck
        raise ValueError("invalid deck name '%s'" % name)

    def _read_available(self, directory):
        """Locate all available deck files."""
        for (dirpath, dirnames, filenames) in os.walk(directory):
            for file in filenames:
                if file[-4:] != ".txt":
                    continue
                if "Achievements" in file:
                    continue
                base = file[:-4]
                name = desc = ""
                definition_file = os.path.join(dirpath, base) + ".txt"
                for (tag, value) in FileReader(definition_file):
                    if tag == "DECK-NAME":
                        name = value
                    elif tag == "DECK-DESC":
                        desc = value
                    else:
                        self._decks.append(DeckCatalogEntry(name, desc,
                                                           dirpath, base))
                        break

    def _read_purchased(self, filename):
        """Read the list of purchased decks."""
        self._purchased_filename = filename
        if not os.path.isfile(filename):
            f = open(filename, 'w')
            f.close()
        for (tag, value) in FileReader(filename):
            if tag == "DECK-NAME":
                self._purchased.append(value)

    def _write(self):
        """Write the list of purchased decks."""
        f = open(self._purchased_filename, 'w')
        try:
            for deck_name in self._purchased:
                f.write("[DECK-NAME]%s\n" % deck_name)
        finally:
            f.close()

    def purchased(self, deck_name):
        """Return the DeckCatalogEntry if purchased, or None."""
        deck = self[deck_name]
        if deck.name in self._purchased:
            return deck
        return None

    def purchase(self, deck):
        """Mark the deck purchased and return its DeckCatalogEntry."""
        deck = self[deck]
        self._purchased.append(deck.name)
        self._write()
        return deck

    
