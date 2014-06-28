import os
import unittest

from rendezvous import Currency


class TestCurrency(unittest.TestCase):

    def setUp(self):
        self.c = Currency("Name", "Desc", "testplayer")

    def tearDown(self):
        try:
            os.remove(self.c.filename)
            os.rmdir("testplayer")
        except: pass

    def test_init(self):
        self.assertEqual(self.c.name, "Name")
        self.assertEqual(self.c.description, "Desc")
        self.assertEqual(self.c.balance, 0)
        self.assertEqual(self.c.filename, os.path.join("testplayer", "Name.txt"))

    def test_string(self):
        self.assertEqual(str(self.c), "0 Names")

    def test_string_one(self):
        self.c.balance = 1
        self.assertEqual(str(self.c), "1 Name")

    def test_string_multi(self):
        self.c.balance = 50
        self.assertEqual(str(self.c), "50 Names")

    def test_earn(self):
        self.c.earn(50, "Reason")
        self.assertEqual(self.c.balance, 50)

    def test_purchase(self):
        self.c.balance = 75
        self.assertTrue(self.c.purchase("Item", 50))
        self.assertEqual(self.c.balance, 25)

    def test_purchase_exact(self):
        self.c.balance = 50
        self.assertTrue(self.c.purchase("Item", 50))
        self.assertEqual(self.c.balance, 0)

    def test_purchase_insufficient(self):
        self.c.balance = 25
        self.assertFalse(self.c.purchase("Item", 50))
        self.assertEqual(self.c.balance, 25)

    def test_persistent(self):
        self.c.balance = 50
        self.c = Currency("Name", "Desc", "testplayer")
        self.assertEqual(self.c.balance, 50)

    def test_multi(self):
        self.c.balance = 50
        c2 = Currency("Other Name", "Desc", "testplayer")
        self.assertEqual(c2.balance, 0)
        try: os.remove(c2.filename)
        except: pass
