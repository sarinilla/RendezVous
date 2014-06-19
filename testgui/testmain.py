"""Limited testing of the contents of main.py, where deemed possible."""

import unittest

from main import *


class TestTouch(unittest.TestCase):

    def setUp(self):
        self.app = RendezVousApp()
        self.root = RendezVousWidget(app=self.app)

    def test_touch_hand(self):
        card = self.root.game.players[PLAYER][3]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.assertEqual(self.root.game.board[PLAYER][0], card)
        self.assertEqual(self.root.game.players[PLAYER][3], card)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)
        
    def test_touch_hand_empty(self):
        card = self.root.game.players[PLAYER][3]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.assertEqual(self.root.game.board[PLAYER][0], card)
        self.assertEqual(self.root.game.players[PLAYER][3], card)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)
        self.assertIs(self.root.game.board[PLAYER][1], None)
        self.assertIs(self.root.current_screen.gameboard.slots[PLAYER][1].card, None)
        
    def test_touch_board(self):
        card = self.root.game.players[PLAYER][3]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_touched(self.root.current_screen.gameboard.slots[PLAYER][0])
        self.assertIs(self.root.game.board[PLAYER][0], None)
        self.assertEqual(self.root.game.players[PLAYER][3], card)
        self.assertIs(self.root.current_screen.gameboard.slots[PLAYER][0].card, None)
        self.assertEqual(self.root.current_screen.hand_display.slots[3].card, card)

    def test_touch_board_empty(self):
        card = self.root.game.players[PLAYER][3]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_touched(self.root.current_screen.gameboard.slots[PLAYER][1])
        self.assertEqual(self.root.game.board[PLAYER][0], card)
        self.assertEqual(self.root.game.players[PLAYER][3], card)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)
        self.assertIs(self.root.game.board[PLAYER][1], None)
        self.assertIs(self.root.current_screen.gameboard.slots[PLAYER][1].card, None)

    def test_touch_board_enemy(self):
        card = Card("Boyfriend", 1)
        self.root.game.board[DEALER][0] = card
        self.root.game.board._wait[DEALER][0] = True
        self.root.current_screen.gameboard.slots[DEALER][0].card = card
        self.root.card_touched(self.root.current_screen.gameboard.slots[DEALER][0])
        self.assertEqual(self.root.game.board[DEALER][0], card)
        self.assertEqual(self.root.current_screen.gameboard.slots[DEALER][0].card, card)
        
    def test_touch_board_enemy_empty(self):
        self.root.card_touched(self.root.current_screen.gameboard.slots[DEALER][0])

    def test_touch_board_enemy_duplicate(self):
        pcard = Card("Boyfriend", 1)
        self.root.game.players[PLAYER].cards[3] = pcard
        self.root.current_screen.hand_display.slots[3].card = pcard
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        dcard = Card("Boyfriend", 1)
        self.root.game.board[DEALER][0] = dcard
        self.root.game.board._wait[DEALER][0] = True
        self.root.current_screen.gameboard.slots[DEALER][0].card = dcard
        self.root.card_touched(self.root.current_screen.gameboard.slots[DEALER][0])
        self.assertEqual(self.root.game.board[PLAYER][0], pcard)
        self.assertEqual(self.root.game.players[PLAYER][3], pcard)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, pcard)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)
        self.assertEqual(self.root.game.board[DEALER][0], dcard)
        self.assertEqual(self.root.current_screen.gameboard.slots[DEALER][0].card, dcard)

    def test_touch_board_held(self):
        card = Card("Boyfriend", 1)
        self.root.game.board[PLAYER][0] = card
        self.root.game.board._wait[PLAYER][0] = True
        self.root.current_screen.gameboard.slots[PLAYER][0].card = card
        self.root.card_touched(self.root.current_screen.gameboard.slots[PLAYER][0])
        self.assertEqual(self.root.game.board[PLAYER][0], card)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card)


class TestDragAndDrop(unittest.TestCase):

    def setUp(self):
        self.app = RendezVousApp()
        self.root = RendezVousWidget(app=self.app)

    def test_drag_hand_to_hand(self):
        card3 = self.root.game.players[PLAYER][3]
        card5 = self.root.game.players[PLAYER][5]
        self.root.card_dropped(self.root.current_screen.hand_display.slots[5], card3)
        self.assertEqual(self.root.game.players[PLAYER][5], card3)
        self.assertEqual(self.root.game.players[PLAYER][3], card5)
        self.assertEqual(self.root.current_screen.hand_display.slots[5].card, card3)
        self.assertEqual(self.root.current_screen.hand_display.slots[3].card, card5)
        self.assertIs(self.root.current_screen.gameboard.slots[PLAYER][0].card, None)
        self.assertIs(self.root.game.board[PLAYER][0], None)
        
    def test_drag_hand_to_hand_empty(self):
        card3 = self.root.game.players[PLAYER][3]
        card5 = self.root.game.players[PLAYER][5]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.assertEqual(self.root.current_screen.hand_display._played, [3])
        self.root.card_dropped(self.root.current_screen.hand_display.slots[3], card5)
        self.assertEqual(self.root.game.players[PLAYER][3], card5)
        self.assertEqual(self.root.game.players[PLAYER][5], card3)
        self.assertEqual(self.root.current_screen.hand_display.slots[3].card, card5)
        self.assertIs(self.root.current_screen.hand_display.slots[5].card, None)
        self.assertEqual(self.root.game.board[PLAYER][0], card3)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card3)
        self.assertEqual(self.root.current_screen.hand_display._played, [5])
        
    def test_drag_hand_to_hand_from_empty(self):
        card3 = self.root.game.players[PLAYER][3]
        card5 = self.root.game.players[PLAYER][5]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.assertEqual(self.root.current_screen.hand_display._played, [3])
        self.root.card_dropped(self.root.current_screen.hand_display.slots[5], None)
        self.assertEqual(self.root.game.players[PLAYER][3], card3)
        self.assertEqual(self.root.game.players[PLAYER][5], card5)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)
        self.assertEqual(self.root.current_screen.hand_display.slots[5].card, card5)
        self.assertEqual(self.root.game.board[PLAYER][0], card3)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card3)
        self.assertEqual(self.root.current_screen.hand_display._played, [3])

    def test_drag_hand_to_hand_same(self):
        card = self.root.game.players[PLAYER][3]
        self.root.card_dropped(self.root.current_screen.hand_display.slots[3], card)
        self.assertIs(self.root.game.board[PLAYER][0], None)
        self.assertEqual(self.root.game.players[PLAYER][3], card)
        self.assertIs(self.root.current_screen.gameboard.slots[PLAYER][0].card, None)
        self.assertEqual(self.root.current_screen.hand_display.slots[3].card, card)
        
    def test_drag_hand_to_board(self):
        card = self.root.game.players[PLAYER][3]
        self.root.card_dropped(self.root.current_screen.gameboard.slots[PLAYER][1], card)
        self.assertEqual(self.root.game.board[PLAYER][1], card)
        self.assertEqual(self.root.game.players[PLAYER][3], card)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][1].card, card)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)
        self.assertIs(self.root.game.board[PLAYER][0], None)
        self.assertIs(self.root.current_screen.gameboard.slots[PLAYER][0].card, None)
        
    def test_drag_hand_to_board_full(self):
        card3 = self.root.game.players[PLAYER][3]
        card5 = self.root.game.players[PLAYER][5]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_dropped(self.root.current_screen.gameboard.slots[PLAYER][0], card5)
        self.assertEqual(self.root.game.board[PLAYER][0], card5)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card5)
        self.assertIs(self.root.game.board[PLAYER][1], None)
        self.assertIs(self.root.current_screen.gameboard.slots[PLAYER][1].card, None)
        self.assertEqual(self.root.game.players[PLAYER][3], card3)
        self.assertEqual(self.root.current_screen.hand_display.slots[3].card, card3)
        self.assertEqual(self.root.game.players[PLAYER][5], card5)
        self.assertIs(self.root.current_screen.hand_display.slots[5].card, None)
        
    def test_drag_hand_to_board_empty(self):
        card = self.root.game.players[PLAYER][3]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_dropped(self.root.current_screen.gameboard.slots[PLAYER][0], None)
        self.assertEqual(self.root.game.board[PLAYER][0], card)
        self.assertEqual(self.root.game.players[PLAYER][3], card)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)        
        
    def test_drag_board_to_hand(self):
        card = self.root.game.players[PLAYER][3]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_dropped(self.root.current_screen.hand_display.slots[3], card)
        self.assertIs(self.root.game.board[PLAYER][0], None)
        self.assertEqual(self.root.game.players[PLAYER][3], card)
        self.assertIs(self.root.current_screen.gameboard.slots[PLAYER][0].card, None)
        self.assertEqual(self.root.current_screen.hand_display.slots[3].card, card)
        self.assertEqual(self.root.current_screen.hand_display._played, [])

    def test_drag_board_to_hand_full(self):
        card3 = self.root.game.players[PLAYER][3]
        card5 = self.root.game.players[PLAYER][5]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_dropped(self.root.current_screen.hand_display.slots[5], card3)
        self.assertIs(self.root.game.board[PLAYER][0], None)
        self.assertIs(self.root.current_screen.gameboard.slots[PLAYER][0].card, None)
        self.assertEqual(self.root.game.players[PLAYER][3], card5)
        self.assertEqual(self.root.current_screen.hand_display.slots[3].card, card5)
        self.assertEqual(self.root.game.players[PLAYER][5], card3)
        self.assertEqual(self.root.current_screen.hand_display.slots[5].card, card3)

    def test_drag_board_to_hand_empty(self):
        card = self.root.game.players[PLAYER][3]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_dropped(self.root.current_screen.hand_display.slots[3], None)
        self.assertEqual(self.root.game.board[PLAYER][0], card)
        self.assertEqual(self.root.game.players[PLAYER][3], card)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)
        
    def test_drag_board_to_board(self):
        card3 = self.root.game.players[PLAYER][3]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_dropped(self.root.current_screen.gameboard.slots[PLAYER][2], card3)
        self.assertIs(self.root.game.board[PLAYER][0], None)
        self.assertIs(self.root.current_screen.gameboard.slots[PLAYER][0].card, None)
        self.assertEqual(self.root.game.board[PLAYER][2], card3)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][2].card, card3)
        self.assertEqual(self.root.game.players[PLAYER][3], card3)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)
        self.assertEqual(self.root.current_screen.hand_display._played, [3])
        
    def test_drag_board_to_board_empty(self):
        card = self.root.game.players[PLAYER][3]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_dropped(self.root.current_screen.gameboard.slots[PLAYER][0], None)
        self.assertEqual(self.root.game.board[PLAYER][0], card)
        self.assertEqual(self.root.game.players[PLAYER][3], card)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)
        
    def test_drag_board_to_board_full(self):
        card3 = self.root.game.players[PLAYER][3]
        card5 = self.root.game.players[PLAYER][5]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_touched(self.root.current_screen.hand_display.slots[5])
        self.root.card_dropped(self.root.current_screen.gameboard.slots[PLAYER][0], card5)
        self.assertEqual(self.root.game.board[PLAYER][0], card5)
        self.assertEqual(self.root.game.board[PLAYER][1], card3)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card5)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][1].card, card3)
        self.assertEqual(self.root.game.players[PLAYER][3], card3)
        self.assertEqual(self.root.game.players[PLAYER][5], card5)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)
        self.assertIs(self.root.current_screen.hand_display.slots[5].card, None)
        
    def test_drag_board_to_board_from_held(self):
        card = Card("Boyfriend", 1)
        self.root.game.board[PLAYER][2] = card
        self.root.game.board._wait[PLAYER][2] = card
        self.root.current_screen.gameboard.slots[PLAYER][2].card = card
        card3 = self.root.game.players[PLAYER][3]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_dropped(self.root.current_screen.gameboard.slots[PLAYER][0], card)
        self.assertEqual(self.root.game.board[PLAYER][0], card3)
        self.assertEqual(self.root.game.players[PLAYER][3], card3)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card3)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)
        self.assertEqual(self.root.game.board[PLAYER][2], card)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][2].card, card)
        
    def test_drag_board_to_board_to_held(self):
        card = Card("Boyfriend", 1)
        self.root.game.board[PLAYER][2] = card
        self.root.game.board._wait[PLAYER][2] = card
        self.root.current_screen.gameboard.slots[PLAYER][2].card = card
        card3 = self.root.game.players[PLAYER][3]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_dropped(self.root.current_screen.gameboard.slots[PLAYER][2], card3)
        self.assertEqual(self.root.game.board[PLAYER][0], card3)
        self.assertEqual(self.root.game.players[PLAYER][3], card3)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card3)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)
        self.assertEqual(self.root.game.board[PLAYER][2], card)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][2].card, card)
        
    def test_drag_board_to_board_same(self):
        card3 = self.root.game.players[PLAYER][3]
        self.root.card_touched(self.root.current_screen.hand_display.slots[3])
        self.root.card_dropped(self.root.current_screen.gameboard.slots[PLAYER][0], card3)
        self.assertEqual(self.root.game.board[PLAYER][0], card3)
        self.assertEqual(self.root.game.players[PLAYER][3], card3)
        self.assertEqual(self.root.current_screen.gameboard.slots[PLAYER][0].card, card3)
        self.assertIs(self.root.current_screen.hand_display.slots[3].card, None)

    # tooltip's CardDisplay is not mapped
    #def test_drag_hand_to_tooltip(self):
    #def test_drag_board_to_tooltip(self):
    #def test_drag_enemy_to_tooltip(self):
    
    def test_drag_tooltip_to_hand(self):
        card = Card("Boyfriend", 1)
        card3 = self.root.game.players[PLAYER][3]
        self.root.card_dropped(self.root.current_screen.hand_display.slots[3], card)
        self.assertEqual(self.root.game.players[PLAYER][3], card3)
        self.assertEqual(self.root.current_screen.hand_display.slots[3].card, card3)
        
    def test_drag_tooltip_to_board(self):
        card = Card("Boyfriend", 1)
        self.root.card_dropped(self.root.current_screen.gameboard.slots[PLAYER][0], card)
        self.assertIs(self.root.game.board[PLAYER][0], None)
        self.assertIs(self.root.current_screen.gameboard.slots[PLAYER][0].card, None)
        
    def test_drag_tooltip_to_enemy(self):
        card = Card("Boyfriend", 1)
        self.root.card_dropped(self.root.current_screen.gameboard.slots[DEALER][0], card)
        self.assertIs(self.root.game.board[DEALER][0], None)
        self.assertIs(self.root.current_screen.gameboard.slots[DEALER][0].card, None)


if __name__ == "__main__":
    unittest.main()
