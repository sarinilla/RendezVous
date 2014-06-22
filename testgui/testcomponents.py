"""Simple branch testing.

Until GL tests are implemented, these serve primarily to execute every line of
code to check for import errors, etc.  Actual functionality may not be fully
tested.

"""

import unittest

from gui.components import *


## GUI Components ##

class TestCardDisplay(unittest.TestCase):

    def setUp(self):
        self.cd = CardDisplay()

    def test_init(self):
        self.assertIs(self.cd.card, None)
        self.assertEqual(self.cd.color, [1, 1, 1, 1])
        self.assertEqual(self.cd.waited, False)

    def test_highlight(self):
        self.cd.highlight([.2, .3, .4, .5])
        self.assertEqual(self.cd.color, [.2, .3, .4, .5])

    # touch events are thoroughly tested via testmain.py


class TestSuitDisplay(unittest.TestCase):

    def setUp(self):
        self.sd = SuitDisplay()

    def test_init(self):
        pass


class TestSuitScoreDisplay(unittest.TestCase):

    def setUp(self):
        self.ssd = SuitScoreDisplay()

    def test_init(self):
        pass


class TestToolTipDisplay(unittest.TestCase):

    def setUp(self):
        self.tt = ToolTipDisplay()

    def test_init(self):
        pass


## Game Components ##

class TestRoundCounter(unittest.TestCase):

    def setUp(self):
        self.rc = RoundCounter()

    def test_init(self):
        pass


class TestHandDisplay(unittest.TestCase):

    def setUp(self):
        from rendezvous.deck import Deck, DeckDefinition
        from rendezvous.gameplay import Hand
        self.hd = HandDisplay(hand=Hand(Deck(DeckDefinition())))

    def test_init(self):
        self.assertEqual(len(self.hd.slots), 10)
        self.assertEqual(self.hd._played, [])

    def test_init_partial(self):
        self.hd.hand.pop()
        self.hd = HandDisplay(hand=self.hd.hand)
        self.assertEqual(len(self.hd.slots), 10)

    def test_update(self):
        self.hd.hand.cards[3] = Card("Suit", 3)
        self.hd.update()
        self.assertIs(self.hd.slots[3].card, self.hd.hand.cards[3])
        self.assertEqual(self.hd.slots[3].card, Card("Suit", 3))

    def test_swap_by_card(self):
        one = self.hd.slots[3].card
        two = self.hd.slots[4].card
        self.hd.swap(one, two)
        self.assertIs(self.hd.slots[3].card, two)
        self.assertIs(self.hd.slots[4].card, one)
        self.assertIs(self.hd.hand[3], two)
        self.assertIs(self.hd.hand[4], one)

    def test_swap_by_slot(self):
        one = self.hd.slots[3].card
        two = self.hd.slots[4].card
        self.hd.swap(self.hd.slots[3], self.hd.slots[4])
        self.assertIs(self.hd.slots[3].card, two)
        self.assertIs(self.hd.slots[4].card, one)
        self.assertIs(self.hd.hand[3], two)
        self.assertIs(self.hd.hand[4], one)

    def test_swap_by_index(self):
        one = self.hd.slots[3].card
        two = self.hd.slots[4].card
        self.hd.swap(3, 4)
        self.assertIs(self.hd.slots[3].card, two)
        self.assertIs(self.hd.slots[4].card, one)
        self.assertIs(self.hd.hand[3], two)
        self.assertIs(self.hd.hand[4], one)

    def test_swap_played(self):
        self.hd.get(self.hd.slots[3])
        self.hd.swap(3, 4)
        self.assertEqual(self.hd._played, [4])        

    def test_get(self):
        expected = self.hd.slots[3].card
        card = self.hd.get(self.hd.slots[3])
        self.assertIs(card, expected)
        self.assertIs(self.hd.slots[3].card, None)
        self.assertEqual(self.hd._played, [3])

    def test_return(self):
        card = self.hd.get(self.hd.slots[3])
        self.hd.return_card(card)
        self.assertIs(self.hd.slots[3].card, card)
        self.assertEqual(self.hd._played, [])

    def test_is_played(self):
        self.assertFalse(self.hd.is_played(self.hd.hand[3]))
        self.hd.get(self.hd.slots[3])
        self.assertTrue(self.hd.is_played(self.hd.hand[3]))

    def test_confirm(self):
        card = self.hd.get(self.hd.slots[3])
        self.hd.confirm()
        self.assertEqual(len(self.hd.hand.cards), 9)
        self.assertEqual(self.hd._played, [])


class TestBoardDisplay(unittest.TestCase):

    def setUp(self):
        from rendezvous.gameplay import Gameboard
        from rendezvous.deck import Card
        self.bd = BoardDisplay(board=Gameboard())

    def test_init(self):
        self.assertEqual(len(self.bd.slots), 2)
        self.assertEqual(len(self.bd.slots[0]), 4)
        self.assertEqual(len(self.bd.slots[1]), 4)
        self.assertNotIn(self.bd._next_round_prompt, self.bd.children)
        
    def test_prompt(self):
        self.bd.prompt_for_next_round()
        self.assertIn(self.bd._next_round_prompt, self.bd.children)

    @unittest.skip("No running app!")
    def test_next_round_prompted(self):
        self.bd.prompt_for_next_round()
        self.bd.next_round_prompted()
        self.assertNotIn(self.bd._next_round_prompt, self.bd.children)

    @unittest.skip("No running app!")
    def test_replay_prompted(self):
        self.bd.prompt_for_next_round()
        self.bd.rescore_prompted()
        self.assertNotIn(self.bd._next_round_prompt, self.bd.children)

    def test_update(self):
        self.bd.board[0][0] = Card("Suit", 1)
        self.bd.board[1][1] = Card("Suit", 5)
        self.bd.board._wait[1][1] = True
        self.bd.update()
        self.assertEqual(self.bd.slots[0][0].card, Card("Suit", 1))
        self.assertEqual(self.bd.slots[0][0].waited, False)
        self.assertEqual(self.bd.slots[1][1].card, Card("Suit", 5))
        self.assertEqual(self.bd.slots[1][1].waited, True)

    def test_highlight(self):
        self.bd.highlight([.2, .3, .4, .5])
        for side in self.bd.slots:
            for slot in side:
                self.assertEqual(slot.color, [.2, .3, .4, .5])

    def test_place(self):
        card = Card("Suit", 5)
        self.bd.place_card(card)
        self.assertEqual(self.bd.board.board, [[None, None, None, None],
                                               [card, None, None, None]])
        self.assertIs(self.bd.slots[1][0].card, card)

    def test_place_index(self):
        card = Card("Suit", 5)
        self.bd.place_card(card, 2)
        self.assertEqual(self.bd.board.board, [[None, None, None, None],
                                               [None, None, card, None]])
        self.assertIs(self.bd.slots[1][2].card, card)

    def test_place_player(self):
        card = Card("Suit", 5)
        self.bd.place_card(card, player=0)
        self.assertEqual(self.bd.board.board, [[card, None, None, None],
                                               [None, None, None, None]])
        self.assertIs(self.bd.slots[0][0].card, card)

    def test_remove(self):
        card = Card("Suit", 5)
        self.bd.place_card(card)
        result = self.bd.remove_card(self.bd.slots[1][0])
        self.assertIs(result, card)
        self.assertIs(self.bd.slots[1][0].card, None)

    def test_place_twice(self):
        card = Card("Suit", 5)
        self.bd.place_card(card)
        result = self.bd.remove_card(self.bd.slots[1][0])
        self.assertIs(result, card)
        self.assertIs(self.bd.slots[1][0].card, None)
        self.bd.place_card(card)
        self.assertIs(self.bd.slots[1][0].card, card)

    def test_validate(self):
        from rendezvous.deck import SpecialCard
        from rendezvous.specials import Requirement, Application, Effect
        from rendezvous import EffectType
        req = Requirement(count=2, style=Application(suits=["Boyfriend"]))
        sc = SpecialCard("Special", "", req, Application(),
                         Effect(EffectType.SWITCH))
        self.bd.place_card(Card("Girlfriend", 1))
        self.bd.place_card(sc)
        self.bd.place_card(Card("Girlfriend", 2))
        self.bd.place_card(Card("Girlfriend", 3))
        result = self.bd.validate()
        self.assertEqual(result, [sc])
        self.assertIs(self.bd.slots[1][1].card, None)

    def test_pop(self):
        card = Card("Suit", 3)
        self.bd.place_card(card)
        result = self.bd.pop(0)
        self.assertIs(result, card)
        self.assertIs(self.bd.slots[1][0].card, None)

    def test_swap_by_card(self):
        card1 = Card("Boyfriend", 1)
        card2 = Card("Boyfriend", 2)
        self.bd.place_card(card1)
        self.bd.place_card(card2)
        self.bd.swap(card1, card2)
        self.assertEqual(self.bd.slots[PLAYER][0].card, card2)
        self.assertEqual(self.bd.slots[PLAYER][1].card, card1)
        self.assertEqual(self.bd.board[PLAYER][0], card2)
        self.assertEqual(self.bd.board[PLAYER][1], card1)

    def test_swap_by_display(self):
        card1 = Card("Boyfriend", 1)
        card2 = Card("Boyfriend", 2)
        self.bd.place_card(card1)
        self.bd.place_card(card2)
        self.bd.swap(self.bd.slots[PLAYER][0], self.bd.slots[PLAYER][1])
        self.assertEqual(self.bd.slots[PLAYER][0].card, card2)
        self.assertEqual(self.bd.slots[PLAYER][1].card, card1)
        self.assertEqual(self.bd.board[PLAYER][0], card2)
        self.assertEqual(self.bd.board[PLAYER][1], card1)

    def test_swap_by_index(self):
        card1 = Card("Boyfriend", 1)
        card2 = Card("Boyfriend", 2)
        self.bd.place_card(card1)
        self.bd.place_card(card2)
        self.bd.swap(0, 1)
        self.assertEqual(self.bd.slots[PLAYER][0].card, card2)
        self.assertEqual(self.bd.slots[PLAYER][1].card, card1)
        self.assertEqual(self.bd.board[PLAYER][0], card2)
        self.assertEqual(self.bd.board[PLAYER][1], card1)

    def test_play_dealer(self):
        cards = [Card("Girlfriend", 1), Card("Girlfriend", 2),
                 Card("Girlfriend", 3), Card("Girlfriend", 4)]
        self.bd.play_dealer(cards, callback=self.dealer_callback, timer=0.001)

    def dealer_callback(self):
        self.assertEqual(self.bd.board[0],
                         [Card("Girlfriend", 1), Card("Girlfriend", 2),
                          Card("Girlfriend", 3), Card("Girlfriend", 4)])
        self.assertEqual(self.bd.slots[0][0].card, Card("Girlfriend", 1))
        self.assertEqual(self.bd.slots[0][1].card, Card("Girlfriend", 2))
        self.assertEqual(self.bd.slots[0][2].card, Card("Girlfriend", 3))
        self.assertEqual(self.bd.slots[0][3].card, Card("Girlfriend", 4))

    def test_apply_specials(self):
        from rendezvous.deck import SpecialCard
        from rendezvous.specials import Requirement, Application, Effect
        from rendezvous import EffectType
        req = Requirement(count=2, style=Application(suits=["Girlfriend"]))
        sc = SpecialCard("Special", "", req, Application(),
                         Effect(EffectType.SWITCH))
        self.bd.place_card(Card("Girlfriend", 1))
        self.bd.place_card(Card("Girlfriend", 2))
        self.bd.place_card(Card("Girlfriend", 3))
        self.bd.place_card(sc)
        self.bd.play_dealer([Card("Boyfriend", 1), Card("Boyfriend", 2),
                             Card("Boyfriend", 3), Card("Boyfriend", 4)],
                            callback=self.special_cont, timer=0.001)
        
    def special_cont(self):
        from rendezvous.gameplay import RendezVousGame
        game = RendezVousGame()
        game.board = self.bd.board
        hd = HandDisplay(game.players[1])
        self.bd.apply_specials(game, hd,
                               callback=self.special_callback, timer=0.001)

    def special_callback(self):
        self.assertEqual(self.bd.board[1][0].value, 3)
        self.assertEqual(self.bd.board[1][1].value, 4)
        self.assertEqual(self.bd.board[1][2].value, 5)

    def test_score_round(self):
        self.bd.place_card(Card("Girlfriend", 2))
        self.bd.place_card(Card("Girlfriend", 3))
        self.bd.place_card(Card("Girlfriend", 4))
        self.bd.place_card(Card("Girlfriend", 5))
        self.bd.play_dealer([Card("Boyfriend", 1), Card("Boyfriend", 2),
                             Card("Boyfriend", 3), Card("Boyfriend", 4)],
                            callback=self.score_cont, timer=0.001)

    def score_cont(self):
        from rendezvous.gameplay import Scoreboard
        self.sd = ScoreDisplay(scoreboard=Scoreboard())
        self.bd.score_round(self.sd, callback=self.score_callback, timer=0.001)

    def score_callback(self):
        self.assertEqual(self.sd.score.scores, [[40, 40, 0, 0, 0],
                                                [-40, 0, 0, 0, 0]])


class TestScoreDisplay(unittest.TestCase):

    def setUp(self):
        from rendezvous.gameplay import Scoreboard
        from rendezvous.deck import DeckDefinition
        self.sd = ScoreDisplay(scoreboard=Scoreboard(DeckDefinition()))

    def test_init(self):
        self.assertEqual(len(self.sd.rows), 5)

    def test_update(self):
        self.sd.scoreboard[DEALER][2] = 20
        self.sd.update()
        self.assertEqual(self.sd.rows[2].dscore, 20)

    def test_update_suits(self):
        self.sd.scoreboard.suits = ["1", "2", "3", "4", "5"]
        self.sd.update_suits()
        for i, suit in enumerate(self.sd.scoreboard.suits):
            self.assertEqual(self.sd.rows[i].suit, suit)
        
        
