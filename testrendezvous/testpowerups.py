import os
import unittest


from rendezvous import PowerupType
from rendezvous.powerups import *


class TestPowerup(unittest.TestCase):

    def setUp(self):
        self.powerup = Powerup('Name', 'Desc', 55, PowerupType.SHOW_DEALER_PLAY)

    def test_init(self):
        self.assertEqual(self.powerup.name, 'Name')
        self.assertEqual(self.powerup.description, 'Desc')
        self.assertEqual(self.powerup.price, 55)
        self.assertEqual(self.powerup.type, PowerupType.SHOW_DEALER_PLAY)
        self.assertEqual(self.powerup.value, 0)

    def test_equal(self):
        self.assertEqual(self.powerup,
                         Powerup('Name', 'Desc', 55, PowerupType.SHOW_DEALER_PLAY))
        self.assertEqual(self.powerup, 'Name')

    def test_string(self):
        self.assertEqual(str(self.powerup), 'Name')

    def test_hash(self):
        self.assertEqual(hash(self.powerup), hash('Name'))


class TestPowerups(unittest.TestCase):

    def setUp(self):
        self.powerups = Powerups("test_powerups.txt")

    def tearDown(self):
        try: os.remove("test_powerups.txt")
        except FileNotFoundError: pass

    def test_init(self):
        self.assertEqual(len(self.powerups.available), 15)
        self.assertEqual(self.powerups.image_file,
                         os.path.join("data", "Powerups.png"))
        self.assertTrue(os.path.isfile(self.powerups.image_file))
        self.assertEqual(self.powerups._purchased_file,
                         "test_powerups.txt")
        self.assertEqual(self.powerups.purchased, {})

    def test_count(self):
        self.assertEqual(self.powerups.count('Ultra Debuff'), 0)
        self.powerups.purchase('Ultra Debuff')
        self.assertEqual(self.powerups.count('Ultra Debuff'), 1)
        self.powerups.purchase('Ultra Debuff')
        self.assertEqual(self.powerups.count('Ultra Debuff'), 2)

    def test_cards(self):
        from rendezvous.deck import Card
        self.assertEqual(self.powerups.cards(), [])
        powerup = self.powerups.find('Up Your Sleeve')
        powerup.value = Card('Boyfriend', 10)
        self.powerups.purchase(powerup)
        self.assertEqual(self.powerups.cards(), ['Boyfriend 10'])
        powerup = self.powerups.find('Up Your Sleeve')
        powerup.value = Card('Boyfriend', 10)
        self.powerups.use(powerup)
        self.assertEqual(self.powerups.cards(), [])
        
    def test_persistent(self):
        self.assertEqual(self.powerups.count('Ultra Debuff'), 0)
        self.powerups.purchase('Ultra Debuff')
        self.powerups = Powerups("test_powerups.txt")
        self.assertEqual(self.powerups.count('Ultra Debuff'), 1)

    def test_use(self):
        self.powerups.purchase('Ultra Debuff')
        self.assertEqual(self.powerups.count('Ultra Debuff'), 1)
        self.powerups.use('Ultra Debuff')
        self.assertEqual(self.powerups.count('Ultra Debuff'), 0)
