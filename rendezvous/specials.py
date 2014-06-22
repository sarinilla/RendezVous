from rendezvous import Operator, SpecialSuit, SpecialValue, Alignment, EffectType

def combinable_class(cls):

    """Decorator so that a class can be combined by use of & and | symbols.

    Methods that should utilize this combination should be marked by
    @combinable_method.

    """

    class Combinable(cls):

        AND = 0
        OR  = 1
        
        def __init__(self, combo=None, items=None, *args, **kwargs):
            """Combine the given classes.

            Arguments:
              combo -- combination type: AND or OR
              items -- items to combine

            """
            if items is None:
                self.type = None
                self.items = [cls(*args, **kwargs)]
                cls.__init__(self, *args, **kwargs)

            elif combo is None:
                raise TypeError

            else:
                self.type = combo
                for item in items:
                    if item.type == combo:
                        self.items = items + item.items
                        self.items.remove(item)
                        break
                else:
                    self.items = items

        def __and__(self, other):
            return self.__class__(combo=self.AND, items=[self, other])

        def __or__(self, other):
            return self.__class__(combo=self.OR, items=[self, other])

        def __str__(self):
            if len(self.items) == 1:
                return str(self.items[0])
            elif self.type == self.AND:
                return "(" + " AND ".join([str(i) for i in self.items]) + ")"
            else:
                return "(" + " OR ".join([str(i) for i in self.items]) + ")"
        
    return Combinable


def combinable_method(f):

    """Decorator for boolean methods within @combinable_class to combine."""

    def combined(self, *args, **kwargs):
        if self.type == self.AND:
            for item in self.items:
                try:
                    if not f(item, *args, **kwargs):
                        return False
                except AttributeError:
                    if not combined(item, *args, **kwargs):
                        return False
            return True

        elif self.type == self.OR:
            for item in self.items:
                try:
                    if f(item, *args, **kwargs):
                        return True
                except AttributeError:
                    if combined(item, *args, **kwargs):
                        return True
            return False
        
        else:
            return f(self.items[0], *args, **kwargs)
        
    return combined


def combinable_list_method(f):

    """Decorator for list methods within @combinable_class to combine."""

    def combined_list(self, *args, **kwargs):
        if self.type == self.AND:
            try:
                result = f(self.items[0], *args, **kwargs)
            except AttributeError:
                result = combined_list(self.items[0], *args, **kwargs)
            for item in self.items[1:]:
                try:
                    result = list(filter(lambda x: x in result,
                                         f(item, *args, **kwargs)))
                except AttributeError:
                    result = list(filter(lambda x: x in result,
                                         combined_list(item, *args, **kwargs)))
            return result

        elif self.type == self.OR:
            result = []
            for item in self.items:
                try:
                    result += f(item, *args, **kwargs)
                except AttributeError:
                    result += combined_list(item, *args, **kwargs)
            return list(set(result))

        else:
            return f(self.items[0], *args, **kwargs)
        
    return combined_list


@combinable_class
class Requirement:

    """A requirement for what card(s) must be played with a SpecialCard.

    Attributes:
      operator -- looking for AT LEAST, EXACTLY, or NO MORE THAN this many?
      count    -- how many cards matching this requirement must be played?
      style    -- Application defining the card to look for

    Methods:
      verify   -- confirm that the required cards are on the board

    """

    def __init__(self, operator=Operator.AT_LEAST, count=0, style=None):
        self.operator = operator
        self.count = count
        self.style = style

    def __str__(self):
        """Return a human-readable description."""
        if self.operator == Operator.AT_LEAST and self.count == 0:
            return "Nothing"
        txt = "At least"
        if self.operator == Operator.EXACTLY:
            txt = "Exactly"
        elif self.operator == Operator.NO_MORE_THAN:
            txt = "No more than"
        style_str = str(self.style)
        if style_str == "ALL cards":
            style_str = "cards"
        if self.count == 1:
            style_str = style_str.replace("cards", "card")
        return "%s %s %s" % (txt, self.count, style_str)
    
    @combinable_method
    def verify(self, friendly_cards):
        if self.style is None:
            return True
        counter = 0
        for card in friendly_cards:
            if self.style.match(None, card, None):
                counter += 1
        if self.operator == Operator.AT_LEAST:
            return counter >= self.count
        elif self.operator == Operator.NO_MORE_THAN:
            return counter <= self.count
        else:
            return counter == self.count

    @combinable_method
    def has_operator(self, operator):
        return self.operator == operator

    @combinable_list_method
    def filter(self, alignment, cards):
        if self.style is None:
            return []
        return self.style.filter(alignment, cards)

    # lazy man's @combinable_sum_method :o
    def totalcount(self):
        if 'items' in dir(self):
            return sum([i.totalcount() for i in self.items])
        else:
            return self.count


@combinable_class
class Application:

    """What other cards a SpecialCard affects.

    Attributes:
      alignment   -- looking for Friendly or Enemy cards? (or None for all)
      valid_suits -- what suit(s) are we looking for? (or None to disable)
      min_value   -- minimum valid value (or None)
      max_value   -- maximum valid value (or None)
      opposite    -- Application that must be met by the opposing card (or None)

    Methods:
      match  -- return boolean: is this card affected?
      filter -- return a subset of the card list that is affected

    """

    def __init__(self, alignment=None, suits=None, min_value=None,
                 max_value=None, opposite=None):
        self.alignment = alignment
        self.suits = suits
        self.min_value = min_value
        self.max_value = max_value
        self.opposite = opposite

    def __str__(self):
        """Return a human-readable description."""
        if self.suits == ["HAND"]:
            return "The player's hand"
        txt = ""
        if self.alignment == Alignment.FRIENDLY:
            txt = "Friendly "
        elif self.alignment == Alignment.ENEMY:
            txt = "Enemy "
        if self.suits is not None:
            txt += " or ".join(self.suits) + " "
        txt += "cards"
        if self.min_value is not None:
            if self.max_value == self.min_value:
                txt += " with a value of %s" % self.min_value
            elif self.max_value is not None:
                txt += " with a value of %s to %s" % (self.min_value, self.max_value)
            else:
                txt += " with a value of %s or greater" % self.min_value
        elif self.max_value is not None:
            txt += " with a value of %s or less" % self.max_value
        if self.opposite is not None:
            txt += " placed VS %s" % self.opposite
        if txt == "cards":
            return "ALL cards"
        return txt

    def _reverse_alignment(self, alignment):
        """Return the opposite alignment."""
        if alignment is None:
            return None
        return 1 - alignment

    @combinable_method
    def match(self, alignment, card, opposite=None):
        """Return boolean indicating if card matches this Application."""
        if card is None:
            return False
        if card.suit == SpecialSuit.SPECIAL:
            return False
        if self.alignment is not None:
            if alignment != self.alignment:
                return False
        if self.suits is not None:
            if card.suit not in self.suits:
                return False
        if self.min_value is not None:
            if card.value < self.min_value:
                return False
        if self.max_value is not None:
            if card.value > self.max_value:
                return False
        if self.opposite is not None and opposite is not None:
            return self.opposite.match(self._reverse_alignment(alignment),
                                       opposite, card)
        return True

    @combinable_method
    def has_alignment(self, alignment):
        return self.alignment == alignment or self.alignment == Alignment.ALL

    # NOT @combinable_list_method because it relies on match()
    def filter(self, alignment, cards):
        """Return the subset of cards that are affected."""
        subset = []
        for card in cards:
            if self.match(alignment, card, None):
                subset.append(card)
        return subset


class Effect:

    """What happens to the cards affected by a SpecialCard.

    Attributes:
      effect -- type of action to take (from EffectTypes)
      value  -- additional information on the degree of the action

    """

    def __init__(self, effect=None, value=None):
        self.effect = effect
        self.value = value

    def __str__(self):
        """Return a human-readable description."""
        if self.effect == EffectType.BUFF:
            if self.value == SpecialValue.WIN:
                return "Automatically WIN"
            elif self.value == SpecialValue.LOSE:
                return "Automatically LOSE"
            elif self.value >= 0:
                return "Buff value by %s" % self.value
            else:
                return "Debuff value by %s" % -self.value
        elif self.effect == EffectType.KISS:
            return "KISS (both sides WIN)"
        elif self.effect == EffectType.WAIT:
            return "Wait through the next turn"
        elif self.effect == EffectType.SWITCH:
            return "Switch values with opponent"
        elif self.effect == EffectType.REVERSE:
            return "Reverse value (e.g. 1 becomes 10)"
        elif self.effect == EffectType.REPLACE:
            return "Replace suit with %s" % self.value
        elif self.effect == EffectType.CLONE:
            return "All matching cards become clones of the first requirement found"
        elif self.effect == EffectType.FLUSH:
            return "Flush all cards from the player's hand and redraws"
        else:
            return "No effect"
        
