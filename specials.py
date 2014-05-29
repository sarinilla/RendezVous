
from deck import Card


def combinable_class(cls):

    """Decorator so that a class can be combined by use of & and | symbols.

    Methods that should utilize this combination should be marked by
    @combinable_method.

    """

    class Combinable(cls):

        AND = 0
        OR  = 1
        
        def __init__(self, combo=None, items=None, **kwargs):
            """Combine the given classes.

            Arguments:
              combo -- combination type: AND or OR
              items -- items to combine

            """
            if items is None:
                self.type = None
                self.items = [cls(**kwargs)]
                cls.__init__(self, **kwargs)

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
        
    return Combinable


def combinable_method(f):

    """Decorator for methods within @combinable_class that should be combined.

    These methods should have boolean return values.
    """

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


@combinable_class
class Requirement:

    """A requirement for what card(s) must be played with a SpecialCard.

    Attributes:
      operator -- looking for AT LEAST, EXACTLY, or NO MORE THAN this many?
      count    -- how many cards matching this requirement must be played?
      card     -- Application defining the card to look for

    Methods:
      verify   -- confirm that the required cards are on the board

    """
    
    @combinable_method
    def verify(self):
        return True


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

    """

    @combinable_method
    def match(self):
        return True


@combinable_class
class Effect:

    """What happens to the cards affected by a SpecialCard.

    Methods:
      apply -- update the given card

    """

    @combinable_method
    def apply(self):
        return False  # always do all combined actions
    

class SpecialCard(Card):

    """Extend Card for special features.

    Additional Attributes:
      requirement -- Requirement item (or combination via & and |)
      application -- Application item (or combination via & and |)
      effect      -- Effect item 

    """
