"""Simple branch testing.

Until GL tests are implemented, these serve primarily to execute every line of
code to check for import errors, etc.  Actual functionality may not be fully
tested.

"""

import unittest

from gui.components import *


class TestCardDisplay(unittest.TestCase):

    def setUp(self):
        self.cd = CardDisplay()

    def test_init(self):
        self.assertIs(self.cd.card, None)
        self.assertEqual(self.cd.color, [1, 1, 1, 1])

    def test_highlight(self):
        self.cd.highlight([.2, .3, .4, .5])
        self.assertEqual(self.cd.color, [.2, .3, .4, .5])

    @unittest.skip("need to stub touch and app.root.card_touched")
    def test_touch(self):
        touch = StubTouch()
        self.cd.on_touch_down(touch)
        self.assertIs(touch.card, self.cd.card)
        self.cd.on_touch_up(touch)


class TestSuitDisplay(unittest.TestCase):

    def setUp(self):
        self.sd = SuitDisplay()

    def test_init(self):
        pass


class TestToolTipDisplay(unittest.TestCase):

    def setUp(self):
        self.tt = ToolTipDisplay()

    def test_init(self):
        pass


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

    def test_udpate(self):
        self.hd.update()

    def test_swap(self):
        one = self.hd.slots[3].card
        two = self.hd.slots[4].card
        self.hd.swap(one, two)
        self.assertIs(self.hd.slots[3].card, two)
        self.assertIs(self.hd.slots[4].card, one)
        self.assertIs(self.hd.hand[3], two)
        self.assertIs(self.hd.hand[4], one)

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

    def test_update(self):
        self.bd.update()

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
        self.sd.update()
        
        
