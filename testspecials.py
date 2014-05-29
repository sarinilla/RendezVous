import unittest

from specials import *

@combinable_class
class DummyClass:

    def __init__(self, value=True):
        self.value = value

    @combinable_method
    def check(self):
        return self.value

class TestCombinations(unittest.TestCase):

    def test_single_true(self):
        r = DummyClass(value=True)
        self.assertTrue(r.check())

    def test_single_false(self):
        r = DummyClass(value=False)
        self.assertFalse(r.check())

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
        
        
        

if __name__ == "__main__":
    unittest.main()
