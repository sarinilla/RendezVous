import unittest

from rendezvous.deck import Card, SpecialCard
from rendezvous.specials import *

@combinable_class
class DummyClass:

    def __init__(self, value=True):
        self.value = value

    @combinable_method
    def check(self):
        return self.value

    def __str__(self):
        return "Dummy"

class TestCombinations(unittest.TestCase):

    def test_single_true(self):
        r = DummyClass(value=True)
        self.assertTrue(r.check())

    def test_single_false(self):
        r = DummyClass(value=False)
        self.assertFalse(r.check())

    def test_single_string(self):
        r = DummyClass()
        self.assertEqual(str(r), "Dummy")

    def test_AND_both_true(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=True)
        r = r1 & r2
        self.assertTrue(r.check())

    def test_AND_first_false(self):
        r1 = DummyClass(value=False)
        r2 = DummyClass(value=True)
        r = r1 & r2
        self.assertFalse(r.check())

    def test_AND_second_false(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=False)
        r = r1 & r2
        self.assertFalse(r.check())

    def test_AND_both_false(self):
        r1 = DummyClass(value=False)
        r2 = DummyClass(value=False)
        r = r1 & r2
        self.assertFalse(r.check())

    def test_AND_string(self):
        r1 = DummyClass()
        r2 = DummyClass()
        r = r1 & r2
        self.assertEqual(str(r), "(Dummy AND Dummy)")        

    def test_OR_both_true(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=True)
        r = r1 | r2
        self.assertTrue(r.check())

    def test_OR_first_false(self):
        r1 = DummyClass(value=False)
        r2 = DummyClass(value=True)
        r = r1 | r2
        self.assertTrue(r.check())

    def test_OR_second_false(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=False)
        r = r1 | r2
        self.assertTrue(r.check())

    def test_OR_both_false(self):
        r1 = DummyClass(value=False)
        r2 = DummyClass(value=False)
        r = r1 | r2
        self.assertFalse(r.check())

    def test_OR_string(self):
        r1 = DummyClass()
        r2 = DummyClass()
        r = r1 | r2
        self.assertEqual(str(r), "(Dummy OR Dummy)") 

    def test_autostack_and(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=True)
        r3 = DummyClass(value=True)
        r = r1 & r2 & r3
        self.assertEqual(r.type, r.AND)
        self.assertEqual(len(r.items), 3)
        self.assertIn(r1, r.items)
        self.assertIn(r2, r.items)
        self.assertIn(r3, r.items)

    def test_autostack_AND_string(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=True)
        r3 = DummyClass(value=True)
        r = r1 & r2 & r3
        self.assertEqual(str(r), "(Dummy AND Dummy AND Dummy)") 

    def test_autostack_or(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=True)
        r3 = DummyClass(value=True)
        r = r1 | r2 | r3
        self.assertEqual(r.type, r.OR)
        self.assertEqual(len(r.items), 3)
        self.assertIn(r1, r.items)
        self.assertIn(r2, r.items)
        self.assertIn(r3, r.items)

    def test_autostack_OR_string(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=True)
        r3 = DummyClass(value=True)
        r = r1 | r2 | r3
        self.assertEqual(str(r), "(Dummy OR Dummy OR Dummy)") 

    def test_stacked_types(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=True)
        r3 = DummyClass(value=False)
        r = r1 & (r2 | r3)
        self.assertEqual(r.type, r.AND)
        self.assertEqual(len(r.items), 2)
        self.assertIs(r1, r.items[0])
        self.assertEqual(r.items[1].type, r.OR)
        self.assertEqual(len(r.items[1].items), 2)
        self.assertIs(r2, r.items[1].items[0])
        self.assertIs(r3, r.items[1].items[1])

    def test_stacked_string(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=True)
        r3 = DummyClass(value=True)
        r = r1 & (r2 | r3)
        self.assertEqual(str(r), "(Dummy AND (Dummy OR Dummy))") 

    def test_stacked_and_or_TTF(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=True)
        r3 = DummyClass(value=False)
        r = r1 & (r2 | r3)
        self.assertTrue(r.check())

    def test_stacked_and_or_TFT(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=False)
        r3 = DummyClass(value=True)
        r = r1 & (r2 | r3)
        self.assertTrue(r.check())

    def test_stacked_and_or_FTT(self):
        r1 = DummyClass(value=False)
        r2 = DummyClass(value=True)
        r3 = DummyClass(value=True)
        r = r1 & (r2 | r3)
        self.assertFalse(r.check())

    def test_stacked_or_and_TFF(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=False)
        r3 = DummyClass(value=False)
        r = r1 | (r2 & r3)
        self.assertTrue(r.check())

    def test_stacked_or_and_FTT(self):
        r1 = DummyClass(value=False)
        r2 = DummyClass(value=True)
        r3 = DummyClass(value=True)
        r = r1 | (r2 & r3)
        self.assertTrue(r.check())

    def test_stacked_or_and_FTF(self):
        r1 = DummyClass(value=False)
        r2 = DummyClass(value=True)
        r3 = DummyClass(value=False)
        r = r1 | (r2 & r3)
        self.assertFalse(r.check())

    def test_stacked_no_paren(self):
        r1 = DummyClass(value=True)
        r2 = DummyClass(value=True)
        r3 = DummyClass(value=False)
        r = r1 | r2 & r3  # same as r1 | (r2 & r3)
        self.assertEqual(r.type, r.OR)
        self.assertEqual(len(r.items), 2)
        self.assertIs(r1, r.items[0])
        self.assertEqual(r.items[1].type, r.AND)
        self.assertEqual(len(r.items[1].items), 2)
        self.assertIs(r2, r.items[1].items[0])
        self.assertIs(r3, r.items[1].items[1])
        self.assertTrue(r.check())
        
        
class TestRequirement(unittest.TestCase):

    def test_init(self):
        """Verify __init__ function."""
        a = Application()
        r = Requirement(operator=Operator.NO_MORE_THAN, count=3, style=a)
        self.assertEqual(r.operator, Operator.NO_MORE_THAN)
        self.assertEqual(r.count, 3)
        self.assertIs(r.style, a)

    def test_default(self):
        """Verify reasonable defaults."""
        r = Requirement()
        self.assertEqual(r.operator, Operator.AT_LEAST)
        self.assertEqual(r.count, 0)
        self.assertIs(r.style, None)

    def test_verify_no_style(self):
        """Test the verify function for an empty application."""
        r = Requirement()
        self.assertTrue(r.verify([]))
        
    def test_verify_at_least_exact(self):
        """Test Operator.AT_LEAST in verify function."""
        r = Requirement(operator=Operator.AT_LEAST, count=2,
                        style=Application(min_value=3))
        self.assertTrue(r.verify([Card("Suit", 2), Card("Suit", 3),
                                  Card("Suit", 4)]))

    def test_verify_at_least_match(self):
        """Test Operator.AT_LEAST in verify function."""
        r = Requirement(operator=Operator.AT_LEAST, count=1,
                        style=Application(min_value=3))
        self.assertTrue(r.verify([Card("Suit", 2), Card("Suit", 3),
                                  Card("Suit", 4)]))
        
    def test_verify_at_least_no_match(self):
        """Test Operator.AT_LEAST in verify function."""
        r = Requirement(operator=Operator.AT_LEAST, count=3,
                        style=Application(min_value=3))
        self.assertFalse(r.verify([Card("Suit", 2), Card("Suit", 3),
                                   Card("Suit", 4)]))
        
    def test_verify_exactly_match(self):
        """Test Operator.EXACTLY in verify function."""
        r = Requirement(operator=Operator.EXACTLY, count=1,
                        style=Application(max_value=2))
        self.assertTrue(r.verify([Card("Suit", 2), Card("Suit", 3),
                                  Card("Suit", 4)]))
        
    def test_verify_exactly_no_match(self):
        """Test Operator.EXACTLY in verify function."""
        r = Requirement(operator=Operator.EXACTLY, count=2,
                        style=Application(max_value=2))
        self.assertFalse(r.verify([Card("Suit", 2), Card("Suit", 3),
                                   Card("Suit", 4)]))
        
    def test_verify_no_more_than_exact(self):
        """Test Operator.NO_MORE_THAN in verify function."""
        r = Requirement(operator=Operator.NO_MORE_THAN, count=2,
                        style=Application(min_value=3))
        self.assertTrue(r.verify([Card("Suit", 2), Card("Suit", 3),
                                  Card("Suit", 4)]))
        
    def test_verify_no_more_than_match(self):
        """Test Operator.NO_MORE_THAN in verify function."""
        r = Requirement(operator=Operator.NO_MORE_THAN, count=3,
                        style=Application(min_value=3))
        self.assertTrue(r.verify([Card("Suit", 2), Card("Suit", 3),
                                  Card("Suit", 4)]))
        
    def test_verify_no_more_than_no_match(self):
        """Test Operator.NO_MORE_THAN in verify function."""
        r = Requirement(operator=Operator.NO_MORE_THAN, count=1,
                        style=Application(min_value=3))
        self.assertFalse(r.verify([Card("Suit", 2), Card("Suit", 3),
                                   Card("Suit", 4)]))

    def test_string_(self):
        """Test string output."""
        self.assertEqual(str(Requirement(operator=Operator.AT_LEAST, count=2,
                                         style=Application())),
                         "At least 2 cards")
        self.assertEqual(str(Requirement(operator=Operator.EXACTLY, count=3,
                                         style=Application())),
                         "Exactly 3 cards")
        self.assertEqual(str(Requirement(operator=Operator.NO_MORE_THAN,
                                         count=1, style=Application())),
                         "No more than 1 cards")


class TestApplication(unittest.TestCase):

    def test_init(self):
        """Verify the __init__."""
        opp = Alignment()
        a = Application(alignment=Alignment.FRIENDLY,
                        suits=["Suit 1", "Suit 2"], min_value=3, max_value=5,
                        opposite=opp)
        self.assertEqual(a.alignment, Alignment.FRIENDLY)
        self.assertEqual(a.suits, ["Suit 1", "Suit 2"])
        self.assertEqual(a.min_value, 3)
        self.assertEqual(a.max_value, 5)
        self.assertIs(a.opposite, opp)

    def test_defaults(self):
        """Verify the default options."""
        a = Application()
        self.assertIs(a.alignment, None)
        self.assertIs(a.suits, None)
        self.assertIs(a.min_value, None)
        self.assertIs(a.max_value, None)
        self.assertIs(a.opposite, None)

    def test_reverse(self):
        """Verify alignment reversal."""
        a = Application()
        self.assertEqual(a._reverse_alignment(Alignment.FRIENDLY), Alignment.ENEMY)
        self.assertEqual(a._reverse_alignment(Alignment.ENEMY), Alignment.FRIENDLY)
        self.assertIs(a._reverse_alignment(None), None)

    def test_match_none(self):
        """Verify default Application matches everything."""
        a = Application()
        self.assertTrue(a.match(Alignment.ALL, Card("Test", 15), Card("S", 0)))

    def test_match_special(self):
        """Verify nothing matching a SpecialCard."""
        s = SpecialCard("Name", "Desc", Requirement(), Application(), Effect())
        a = Application()
        self.assertFalse(a.match(Alignment.ALL, s, s))

    def test_match_alignment(self):
        a = Application(alignment=Alignment.FRIENDLY)
        self.assertTrue(a.match(Alignment.FRIENDLY, Card("S", 0), Card("S", 0)))
        self.assertFalse(a.match(Alignment.ENEMY, Card("S", 0), Card("S", 0)))

    def test_match_suit(self):
        a = Application(suits=["Suit 1", "Suit 2"])
        self.assertTrue(a.match(Alignment.ALL, Card("Suit 1", 0), Card("S", 0)))
        self.assertTrue(a.match(Alignment.ALL, Card("Suit 2", 0), Card("S", 0)))
        self.assertFalse(a.match(Alignment.ALL, Card("S", 0), Card("Suit 1", 0)))

    def test_match_min_value(self):
        a = Application(min_value=3)
        self.assertTrue(a.match(Alignment.ALL, Card("Suit", 4), Card("S", 0)))
        self.assertTrue(a.match(Alignment.ALL, Card("Suit", 3), Card("S", 0)))
        self.assertFalse(a.match(Alignment.ALL, Card("Suit", 2), Card("S", 0)))

    def test_match_exact_value(self):
        a = Application(min_value=3, max_value=3)
        self.assertFalse(a.match(Alignment.ALL, Card("Suit", 4), Card("S", 0)))
        self.assertTrue(a.match(Alignment.ALL, Card("Suit", 3), Card("S", 0)))
        self.assertFalse(a.match(Alignment.ALL, Card("Suit", 2), Card("S", 0)))

    def test_match_max_value(self):
        a = Application(max_value=3)
        self.assertFalse(a.match(Alignment.ALL, Card("Suit", 4), Card("S", 0)))
        self.assertTrue(a.match(Alignment.ALL, Card("Suit", 3), Card("S", 0)))
        self.assertTrue(a.match(Alignment.ALL, Card("Suit", 2), Card("S", 0)))

    def test_match_opposite(self):
        a = Application(opposite=Application(min_value=3))
        self.assertFalse(a.match(Alignment.ALL, Card("Suit", 3), Card("Suit", 2)))
        self.assertTrue(a.match(Alignment.ALL, Card("Suit", 2), Card("Suit", 3)))

    def test_string_(self):
        """Verify string output."""
        self.assertEqual(str(Application()),
                         "cards")
        self.assertEqual(str(Application(alignment=Alignment.FRIENDLY)),
                         "Friendly cards")
        self.assertEqual(str(Application(alignment=Alignment.ENEMY)),
                         "Enemy cards")
        self.assertEqual(str(Application(alignment=Alignment.ALL)),
                         "cards")
        self.assertEqual(str(Application(suits=["Suit 1", "Suit 2"])),
                         "Suit 1 or Suit 2 cards")
        self.assertEqual(str(Application(min_value=3)),
                         "cards with a value of 3 or greater")
        self.assertEqual(str(Application(max_value=3)),
                         "cards with a value of 3 or less")
        self.assertEqual(str(Application(min_value=3, max_value=3)),
                         "cards with a value of 3")
        self.assertEqual(str(Application(min_value=3, max_value=5)),
                         "cards with a value of 3 to 5")
        self.assertEqual(str(Application(opposite=Application(alignment=Alignment.FRIENDLY, suits=["Boyfriend"], min_value=1, max_value=3))),
                         "cards placed VS Friendly Boyfriend cards with a value of 1 to 3")

class TestEffect(unittest.TestCase):

    def test_init(self):
        e = Effect(EffectType.BUFF, 2)
        self.assertEqual(e.effect, EffectType.BUFF)
        self.assertEqual(e.value, 2)

    def test_default(self):
        e = Effect()
        self.assertIs(e.effect, None)
        self.assertIs(e.value, None)

    def test_string_(self):
        """Verify string output."""
        self.assertEqual(str(Effect()),
                         "No effect")
        self.assertEqual(str(Effect(EffectType.BUFF, 2)),
                         "Buff value by 2")
        self.assertEqual(str(Effect(EffectType.BUFF, -2)),
                         "Debuff value by 2")
        self.assertEqual(str(Effect(EffectType.BUFF, 0)),
                         "Buff value by 0")
        self.assertEqual(str(Effect(EffectType.BUFF, SpecialValue.WIN)),
                         "Automatically WIN")
        self.assertEqual(str(Effect(EffectType.BUFF, SpecialValue.LOSE)),
                         "Automatically LOSE")
        self.assertEqual(str(Effect(EffectType.KISS)),
                         "KISS (both sides WIN)")
        self.assertEqual(str(Effect(EffectType.WAIT)),
                         "Wait through the next turn")
        self.assertEqual(str(Effect(EffectType.SWITCH)),
                         "Switch values with opponent")
        self.assertEqual(str(Effect(EffectType.REVERSE)),
                         "Reverse value (e.g. 1 becomes 10)")
        self.assertEqual(str(Effect(EffectType.REPLACE, "NewSuit")),
                         "Replace suit with NewSuit")
        self.assertEqual(str(Effect(EffectType.CLONE)),
                         "All matching (friendly) cards become clones of the first")
        self.assertEqual(str(Effect(EffectType.FLUSH)),
                         "Flush all cards from the player's hand and redraws")

if __name__ == "__main__":
    unittest.main()
