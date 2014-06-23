import unittest
import copy

from rendezvous.deck import Card, SpecialCard
from rendezvous.specials import Requirement, Application, Effect
from rendezvous import EffectType
from rendezvous.dealer import *


class TestPossiblePlay(unittest.TestCase):

    def setUp(self):
        """Generate a basic, blank object to test with."""
        self.board = [[None] * 4, [None] * 4]
        self.score = [[0] * 5, [0] * 5]
        self.hand = [Card("Suit", i+1) for i in range(10)]
        self.cards = self.hand[:4]
        random.seed(10101)  # prevent flukes
        self.p = PossiblePlay(self.cards, self.board, self.score,
                              self.hand, 0)

    def test_init(self):
        """Verify the object is initialized correctly."""
        self.assertEqual(sorted(self.p.cards), self.hand[:4])
        self.assertIs(self.p.board, self.board)
        self.assertIs(self.p.score, self.score)
        self.assertIs(self.p.hand, self.hand)
        self.assertEqual(self.p.player, 0)

    def test_shuffled(self):
        """Cards should be given in random order (usually)."""
        self.assertNotEqual(self.p.cards, self.hand[:4])

    def test_player_empty_yes(self):
        self.assertTrue(self.p.player_empty())

    def test_player_empty_no(self):
        self.p.board[0] = [None, None, Card("No Suit", 50), None]
        self.assertFalse(self.p.player_empty())

    def test_dealer_empty_yes(self):
        self.assertTrue(self.p.dealer_empty())

    def test_dealer_empty_no(self):
        self.p.board[1] = [None, None, Card("No Suit", 50), None]
        self.assertFalse(self.p.dealer_empty())


    def test_arrange_clone(self):
        """Replace a high-value card."""
        sc = SpecialCard('Clone', 'Testing Card',
                         Requirement(), Application(),
                         Effect(EffectType.CLONE))
        self.p.cards = [Card("Suit", i+1) for i in range(4)]  # unshuffle
        self.p.cards[2] = sc                                  # replace 3
        self.p._arrange()
        self.assertEqual(self.p.cards, [Card("Suit", 4),
                                        Card("Suit", 2),
                                        Card("Suit", 1),
                                        sc])

    def test_arrange_clone_enemy(self):
        """Give the enemy a low-value card."""
        sc = SpecialCard('Clone', 'Testing Card', Requirement(),
                         Application(alignment=Alignment.ENEMY),
                         Effect(EffectType.CLONE))
        self.p.cards = [Card("Suit", i+1) for i in range(4)]  # unshuffle
        self.p.cards[2] = sc                                  # replace 3
        self.p._arrange()
        self.assertEqual(self.p.cards, [sc,
                                        Card("Suit", 1),
                                        Card("Suit", 2),
                                        Card("Suit", 4)])

    def test_arrange_simple_hold(self):
        """Arrange cards to (barely) beat dealer holds."""
        self.p.board[1] = [Card("Suit", 2), Card("Suit", 1), Card("Suit", 3), None]
        self.p._arrange()
        self.assertEqual(self.p.cards, [Card("Suit", 3),
                                        Card("Suit", 2),
                                        Card("Suit", 4),
                                        Card("Suit", 1)])

    def test_arrange_both_hold(self):
        """Ensure player holds are accounted for."""
        self.p.board[0] = [Card("Suit", 2), None, None, None]
        self.p.board[1] = [None, Card("Suit", 2), Card("Suit", 1), Card("Suit", 3)]
        self.p.cards = [Card("Suit", 1), Card("Suit", 3), Card("Suit", 4)]
        self.p._arrange()
        self.assertEqual(self.p.cards, [Card("Suit", 3),
                                        Card("Suit", 4),
                                        Card("Suit", 1)])

    def test_arrange_impossible(self):
        """Use the lowest card on an impossible-to-win match."""
        self.p.board[1] = [None, None, Card("Suit", 5), None]
        self.p._arrange()
        self.assertEqual(self.p.cards, [Card("Suit", 3),
                                        Card("Suit", 2),
                                        Card("Suit", 1),
                                        Card("Suit", 4)])

    def test_arrange_special_over_impossible(self):
        """Block an impossible-to-win match with a special if available."""
        self.p.board[1] = [None, None, Card("Suit", 6), None]
        sc = SpecialCard("Buff", "Test Special", Requirement(), Application(),
                         Effect(EffectType.WAIT))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.p._arrange()
        self.assertEqual(self.p.cards, [Card("Suit", 3),
                                        Card("Suit", 2),
                                        sc,
                                        Card("Suit", 4)])

    def test_arrange_with_buff(self):
        """Ensure buffs are accounted for."""
        self.board[1] = [None, None, Card("Suit", 5), None]
        sc = SpecialCard("Buff", "Test Special", Requirement(),
                         Application(alignment=Alignment.FRIENDLY),
                         Effect(EffectType.BUFF, 2))
        self.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.p = PossiblePlay(self.cards, self.board, self.score,
                              self.hand, 0)
        self.assertEqual(self.p.cards, [sc,
                                        Card("Suit", 2),
                                        Card("Suit", 4),
                                        Card("Suit", 3)])
        self.assertEqual(self.p.board[1][2], Card("Suit", 5))

    def test_arrange_switch(self):
        """Ensure switches are accounted for properly."""
        self.board[1] = [None, Card("Suit", 3), None, None]
        sc = SpecialCard("Buff", "Test Special", Requirement(),
                         Application(alignment=Alignment.FRIENDLY),
                         Effect(EffectType.SWITCH))
        self.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.p = PossiblePlay(self.cards, self.board, self.score,
                              self.hand, 0)
        self.assertEqual(self.p.cards, [sc,
                                        Card("Suit", 2),
                                        Card("Suit", 4),
                                        Card("Suit", 3)])
        self.assertEqual(self.p.board[1][1], Card("Suit", 3))
        
    def test_arrange_reverse(self):
        """Ensure reverses are accounted for properly."""
        self.board[1] = [None, None, Card("Suit", 8), None]
        sc = SpecialCard("Buff", "Test Special", Requirement(),
                         Application(alignment=Alignment.FRIENDLY),
                         Effect(EffectType.REVERSE))
        self.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.p = PossiblePlay(self.cards, self.board, self.score,
                              self.hand, 0)
        self.assertEqual(self.p.cards, [sc,
                                        Card("Suit", 4),
                                        Card("Suit", 2),
                                        Card("Suit", 3)])
        self.assertEqual(self.p.board[1][2], Card("Suit", 8))


    def test_calculate_base(self):
        """Simple value is the sum of the values."""
        self.assertEqual(self.p.value, 10)

    def test_calculate_special_bonus(self):
        """10-point bonus just for playing a special."""
        sc = SpecialCard("Bonus", "Test Bonus", Requirement(),
                         Application(alignment=Alignment.FRIENDLY),
                         Effect(EffectType.BUFF, 0))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 19)

    def test_calculate_special_bonus_unapplied(self):
        """No bonus if it doesn't apply to anything."""
        sc = SpecialCard("Bonus", "Test Bonus", Requirement(),
                         Application(alignment=Alignment.FRIENDLY,
                                     suits=["No Suit"]),
                         Effect(EffectType.BUFF, 0))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 9)

    def test_calculate_special_bonus_enemy(self):
        """Include a bonus if it applies to the enemy unknown."""
        sc = SpecialCard("Bonus", "Test Bonus", Requirement(),
                         Application(alignment=Alignment.ENEMY,
                                     suits=["No Suit"]),
                         Effect(EffectType.BUFF, 0))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 19)

    def test_calculate_buff(self):
        """Account for the buffed value."""
        sc = SpecialCard("Buff", "Test Special", Requirement(),
                         Application(alignment=Alignment.FRIENDLY),
                         Effect(EffectType.BUFF, 2))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 25)

    def test_calculate_buff_partial(self):
        """Account for buffing only some friendlies."""
        sc = SpecialCard("Buff", "Test Special", Requirement(),
                         Application(alignment=Alignment.FRIENDLY,
                                     suits=["Suit"]),
                         Effect(EffectType.BUFF, 2))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3),
                        Card("No Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 23)

    def test_calculate_buff_held(self):
        """Bonus for buffing a held card."""
        sc = SpecialCard("Buff", "Test Special", Requirement(),
                         Application(alignment=Alignment.FRIENDLY),
                         Effect(EffectType.BUFF, 2))
        self.p.cards = [Card("Suit", 3), Card("Suit", 4), sc]
        self.p.board[0][2] = Card("Suit", 2)
        self.assertEqual(self.p._calculate(), 28)

    def test_calculate_debuff(self):
        """Account for an unknown debuff.""" 
        sc = SpecialCard("Buff", "Test Special", Requirement(),
                         Application(alignment=Alignment.ENEMY),
                         Effect(EffectType.BUFF, -2))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 21)

    def test_calculate_debuff_held(self):
        """Account for debuffing held cards."""
        self.p.board[1] = [None, None, Card("Suit", 8), None]
        sc = SpecialCard("Buff", "Test Special", Requirement(),
                         Application(alignment=Alignment.ENEMY),
                         Effect(EffectType.BUFF, -2))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 23)

    def test_calculate_reverse(self):
        """Account for reversals."""
        sc = SpecialCard("Reverse", "Test Special", Requirement(),
                         Application(alignment=Alignment.FRIENDLY),
                         Effect(EffectType.REVERSE))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 34)

    def test_calculate_reverse_high(self):
        """No points for reversing a high card."""
        sc = SpecialCard("Reverse", "Test Special", Requirement(),
                         Application(alignment=Alignment.FRIENDLY),
                         Effect(EffectType.REVERSE))
        self.p.cards = [Card("Suit", 8), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 25)

    def test_calculate_reverse_enemy(self):
        """Account for an unknown enemy reversal."""
        sc = SpecialCard("Reverse", "Test Special", Requirement(),
                         Application(alignment=Alignment.ENEMY),
                         Effect(EffectType.REVERSE))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 24)

    def test_calculate_reverse_enemy_hold(self):
        """Account for a known enemy reversal."""
        self.p.board[1] = [None, None, Card("Suit", 8), None]
        sc = SpecialCard("Reverse", "Test Special", Requirement(),
                         Application(alignment=Alignment.ENEMY),
                         Effect(EffectType.REVERSE))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 32)

    def test_calculate_reverse_enemy_hold_low(self):
        """Lose points for reversing a known low enemy card."""
        self.p.board[1] = [None, None, Card("Suit", 2), None]
        sc = SpecialCard("Reverse", "Test Special", Requirement(),
                         Application(alignment=Alignment.ENEMY),
                         Effect(EffectType.REVERSE))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 15)

    def test_calculate_clone(self):
        """Account for a cloned value."""
        sc = SpecialCard("Clone", "Test Special", Requirement(),
                         Application(alignment=Alignment.FRIENDLY),
                         Effect(EffectType.CLONE))
        self.p.cards = [Card("Suit", 8), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 34)

    def test_calculate_clone_other(self):
        """Account for a clone when requirement != application."""
        sc = SpecialCard("Clone", "Test Special",
                         Requirement(count=1, style=Application(suits=["No Suit"])),
                         Application(alignment=Alignment.FRIENDLY, suits=["Suit"]),
                         Effect(EffectType.CLONE))
        self.p.cards = [Card("Suit", 3), Card("No Suit", 8), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 34)

    def test_calculate_clone_enemy(self):
        """Account for an unknown enemy clone."""
        sc = SpecialCard("Clone", "Test Special", Requirement(),
                         Application(alignment=Alignment.ENEMY),
                         Effect(EffectType.CLONE))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 35)

    def test_calculate_clone_enemy_hold(self):
        """Lose points for a low enemy clone."""
        self.p.board[1] = [Card("Suit", 2), None, None, None]
        sc = SpecialCard("Replace", "Test Special", Requirement(),
                         Application(alignment=Alignment.ENEMY),
                         Effect(EffectType.CLONE))
        self.p.cards = [Card("Suit", 4), Card("Suit", 3), Card("Suit", 2), sc]
        self.assertEqual(self.p._calculate(), 23)

    def test_calculate_clone_enemy_hold_high(self):
        """Gain points for a high enemy clone."""
        self.p.board[1] = [Card("Suit", 8), None, None, None]
        sc = SpecialCard("Replace", "Test Special", Requirement(),
                         Application(alignment=Alignment.ENEMY),
                         Effect(EffectType.CLONE))
        self.p.cards = [Card("Suit", 2), Card("Suit", 3), Card("Suit", 4), sc]
        self.assertEqual(self.p._calculate(), 37)
        
    def test_calculate_flush(self):
        """Score the points in the hand for a flush."""
        sc = SpecialCard("Replace", "Test Special", Requirement(),
                         Application(), Effect(EffectType.FLUSH))
        self.p.cards = [sc, Card("Suit", 2), Card("Suit", 3), Card("Suit", 4)]
        self.assertEqual(self.p._calculate(), 15)

    def test_calculate_flush_specials(self):
        """Dock points for flushing good specials."""
        sc = SpecialCard("Replace", "Test Special", Requirement(),
                         Application(), Effect(EffectType.FLUSH))
        self.p.cards = [sc, Card("Suit", 2), Card("Suit", 3), Card("Suit", 4)]
        good = SpecialCard("Switch", "Don't Flush Me!", Requirement(),
                           Application(), Effect(EffectType.SWITCH))
        self.p.hand = [good] + self.p.cards + [Card("Suit", 1)] * 5
        self.assertEqual(self.p._calculate(), -6)


class TestAI(unittest.TestCase):

    """High-level testing of play selection."""

    def setUp(self):
        self.hand = [Card("Suit", i+1) for i in range(10)]
        self.board = [[None] * 4, [None] * 4]
        self.score = [[0] * 5, [0] * 5]
        self.ai = ArtificialIntelligence(0, self.hand, self.board, self.score)

    def test_play_high(self):
        """Play high values first."""
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [Card("Suit", i) for i in range(7, 11)])

    def test_play_target_held(self):
        """Play only as high as needed."""
        self.ai.board[1][1] = Card("Suit", 2)
        self.ai.analyze()
        self.assertEqual(self.ai.get_best_play(),
                         [Card("Suit", 8), Card("Suit", 3),
                          Card("Suit", 9), Card("Suit", 10)])

    def test_play_buff(self):
        """Play a buff with applicable cards."""
        suit_buff = SpecialCard("Suit Buff", "",
                                Requirement(),
                                Application(alignment=Alignment.FRIENDLY,
                                            suits=["Suit"]),
                                Effect(EffectType.BUFF, 2))
        other_buff = SpecialCard("Other Suit Buff", "",
                                Requirement(),
                                Application(alignment=Alignment.FRIENDLY,
                                            suits=["Other"]),
                                Effect(EffectType.BUFF, 2))
        self.ai.hand = ([Card("Suit", i+2) for i in range(4)] +
                        [Card("Other", i+4) for i in range(4)] +
                        [suit_buff, other_buff])
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [other_buff,
                          Card("Other", 5), Card("Other", 6), Card("Other", 7)])

    def test_play_held_buff(self):
        """Buff a held card."""
        suit_buff = SpecialCard("Suit Buff", "",
                                Requirement(),
                                Application(alignment=Alignment.FRIENDLY,
                                            suits=["Suit"]),
                                Effect(EffectType.BUFF, 2))
        other_buff = SpecialCard("Other Suit Buff", "",
                                Requirement(),
                                Application(alignment=Alignment.FRIENDLY,
                                            suits=["Other"]),
                                Effect(EffectType.BUFF, 2))
        self.ai.hand = ([Card("Suit", i+2) for i in range(4)] +
                        [Card("Other", i+4) for i in range(4)] +
                        [suit_buff, other_buff])
        self.ai.board[0][2] = Card("Suit", 5)
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [suit_buff, Card("Suit", 4), Card("Suit", 5)])

    def test_play_debuff(self):
        """Debuff the enemy if possible."""
        suit_buff = SpecialCard("Suit Debuff", "",
                                Requirement(),
                                Application(alignment=Alignment.ENEMY,
                                            suits=["Suit"]),
                                Effect(EffectType.BUFF, -2))
        other_buff = SpecialCard("Other Suit Debuff", "",
                                Requirement(),
                                Application(alignment=Alignment.ENEMY,
                                            suits=["Other"]),
                                Effect(EffectType.BUFF, -2))
        self.ai.hand = ([Card("Suit", i+1) for i in range(8)] +
                        [suit_buff, other_buff])
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [suit_buff,
                          Card("Suit", 6), Card("Suit", 7), Card("Suit", 8)])

    def test_play_held_debuff(self):
        """Debuff a held card."""
        suit_buff = SpecialCard("Suit Debuff", "",
                                Requirement(),
                                Application(alignment=Alignment.ENEMY,
                                            suits=["Suit"]),
                                Effect(EffectType.BUFF, -2))
        other_buff = SpecialCard("Other Suit Debuff", "",
                                Requirement(),
                                Application(alignment=Alignment.ENEMY,
                                            suits=["Other"]),
                                Effect(EffectType.BUFF, -2))
        self.ai.hand = ([Card("Suit", i+1) for i in range(8)] +
                        [suit_buff, other_buff])
        self.ai.board[1][2] = Card("Other", 10)
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [other_buff,
                          Card("Suit", 6), Card("Suit", 7), Card("Suit", 8)])

    def test_requirements(self):
        """Don't play outside of requirements."""
        require_none = SpecialCard("Require None", "",
                                   Requirement(operator=Operator.NO_MORE_THAN,
                                               count=0,
                                               style=Application(suits=["Suit"])),
                                   Application(alignment=Alignment.ENEMY),
                                   Effect(EffectType.BUFF, -2))
        self.ai.hand = ([Card("Other", i+1) for i in range(5)] +
                        [Card("Suit", i+4) for i in range(4)] +
                        [require_none])
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [require_none,
                          Card("Other", 3), Card("Other", 4), Card("Other", 5)])

    def test_switch(self):
        """Play low cards with a switch."""
        switch = SpecialCard("Switch", "",
                             Requirement(count=1, style=Application()),
                             Application(alignment=Alignment.FRIENDLY),
                             Effect(EffectType.SWITCH))
        self.ai.hand = ([Card("Suit", i+1) for i in range(9)] + [switch])
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [switch,
                          Card("Suit", 1), Card("Suit", 2), Card("Suit", 3)])

    def test_reverse(self):
        """Play low cards with a reverse."""
        switch = SpecialCard("Reverse", "", Requirement(),
                             Application(alignment=Alignment.FRIENDLY),
                             Effect(EffectType.REVERSE))
        self.ai.hand = ([Card("Suit", i+1) for i in range(9)] + [switch])
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [switch,
                          Card("Suit", 1), Card("Suit", 2), Card("Suit", 3)])


    def test_kiss(self):
        """Play low cards with a kiss."""
        switch = SpecialCard("Kiss", "", Requirement(),
                             Application(alignment=Alignment.FRIENDLY),
                             Effect(EffectType.KISS))
        self.ai.hand = ([Card("Suit", i+1) for i in range(9)] + [switch])
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [switch,
                          Card("Suit", 1), Card("Suit", 2), Card("Suit", 3)])


    def test_filler_high(self):
        """Fill with high cards if not applicable."""
        switch = SpecialCard("Reverse", "", Requirement(),
                             Application(alignment=Alignment.FRIENDLY,
                                         suits=["Suit"]),
                             Effect(EffectType.REVERSE))
        self.ai.hand = ([Card("Suit", i+1) for i in range(2)] +
                        [Card("Other", i+1) for i in range(7)] +
                        [switch])
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [switch,
                          Card("Suit", 1), Card("Suit", 2), Card("Other", 7)])

    def test_clone_one_high(self):
        """Fill clone with low cards."""
        replace = SpecialCard("Replace", "", Requirement(),
                              Application(alignment=Alignment.FRIENDLY),
                              Effect(EffectType.CLONE))
        self.ai.hand = ([Card("Suit", i+1) for i in range(9)] + [replace])
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [replace,
                          Card("Suit", 1), Card("Suit", 2), Card("Suit", 9)])

    def test_clone_differing(self):
        """Use clone requirement and application correctly."""
        clone = SpecialCard("Clone", "",
                            Requirement(count=1, style=Application(suits=["Cloned"])),
                            Application(alignment=Alignment.FRIENDLY, suits=["Replaced"]),
                            Effect(EffectType.CLONE))
        self.ai.hand = ([Card("Replaced", i+2) for i in range(5)] +
                        [Card("Cloned", i+1) for i in range(4)] +
                        [clone])
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [clone, Card("Replaced", 2), Card("Replaced", 3),
                          Card("Cloned", 4)])

    def test_clone_enemy(self):
        """Clone a low card to the enemy."""
        clone = SpecialCard("Clone", "",
                            Requirement(),
                            Application(alignment=Alignment.ENEMY),
                            Effect(EffectType.CLONE))
        self.ai.hand = ([Card("Suit", i+1) for i in range(9)] + [clone])
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [clone, Card("Suit", 1), Card("Suit", 8),
                          Card("Suit", 9)])

    def test_flush(self):
        """Use a flush with highest of low cards."""
        flush = SpecialCard("Flush", "", Requirement(), Application(),
                            Effect(EffectType.FLUSH))
        self.ai.hand = ([Card("Suit", 1) for i in range(6)] +
                        [Card("Suit", i+8) for i in range(3)] +
                        [flush])
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [flush,
                          Card("Suit", 8), Card("Suit", 9), Card("Suit", 10)])

    def test_no_flush(self):
        """Don't flush high cards."""
        flush = SpecialCard("Flush", "", Requirement(), Application(),
                            Effect(EffectType.FLUSH))
        self.ai.hand = ([Card("Suit %s" % i, 10) for i in range(9)] + [flush])
        self.ai.analyze()
        self.assertNotIn(flush, self.ai.get_best_play())

    def test_no_flush_special(self):
        """Don't flush good specials."""
        flush = SpecialCard("Flush", "", Requirement(), Application(),
                            Effect(EffectType.FLUSH))
        reverse = SpecialCard("Reverse", "Can't be played!",
                              Requirement(count=4, style=Application()),
                              Application(Alignment.FRIENDLY),
                              Effect(EffectType.REVERSE))
        self.ai.hand = ([Card("Suit %s" % i, 1) for i in range(8)] +
                        [flush, reverse])
        self.ai.analyze()
        self.assertNotIn(flush, self.ai.get_best_play())

    def test_special_filler(self):
        """Fill with a no-requirements special if needed."""
        filler = SpecialCard("Filler", "", Requirement(), Application(),
                             Effect(EffectType.BUFF, 0))
        filler2 = SpecialCard("Filler 2", "", Requirement(), Application(),
                             Effect(EffectType.BUFF, 0))
        self.ai.hand = ([Card("Suit", i+1) for i in range(2)] +
                        [SpecialCard("Filler %s" % i, "",
                                     Requirement(), Application(),
                                     Effect(EffectType.BUFF, 0))
                         for i in range(8)])
        self.ai.analyze()
        self.ai.get_best_play()  # no error

    def test_matching_special(self):
        """Prefer a matching special if a filler is needed."""
        suit_buff = SpecialCard("Suit Buff", "",
                                Requirement(),
                                Application(alignment=Alignment.FRIENDLY,
                                            suits=["Suit"]),
                                Effect(EffectType.BUFF, 2))
        other_buff = SpecialCard("Other Suit Buff", "",
                                Requirement(),
                                Application(alignment=Alignment.FRIENDLY,
                                            suits=["Other"]),
                                Effect(EffectType.BUFF, 2)) 
        filler = SpecialCard("Filler", "", Requirement(),
                             Application(suits=["None"]),
                             Effect(EffectType.BUFF, 0))
        reverse = SpecialCard("Reverse", "", Requirement(),
                             Application(alignment=Alignment.FRIENDLY),
                             Effect(EffectType.REVERSE))
        self.ai.hand = ([Card("Suit", i+1) for i in range(2)] +
                        [copy.copy(filler) for i in range(5)] +
                        [reverse, suit_buff, other_buff])
        self.ai.analyze()
        play = sorted(self.ai.get_best_play())
        if play[0] is suit_buff:
            play[:2] = reversed(play[:2])  # special order flexible
        self.assertEqual(play,
                         [reverse, suit_buff, Card("Suit", 1), Card("Suit", 2)])
     

    def test_impossible(self):
        """Handle case with no valid plays."""
        impossible = SpecialCard("Impossible", "Can't play!",
                                 Requirement(count=5, style=Application()),
                                 Application(),
                                 Effect(EffectType.BUFF, 2))
        self.ai.hand = [copy.copy(impossible) for i in range(10)]
        self.ai.analyze()
        self.assertRaises(IndexError, self.ai.get_best_play)

    def test_none_needed(self):
        """Handle full dealer hold."""
        self.ai.board[0] = [Card("Suit", 1), Card("Suit", 2),
                            Card("Suit", 3), Card("Suit", 4)]
        self.ai.analyze()
        self.assertEqual(self.ai.get_best_play(), [])

    def test_complex_cards(self):
        """Verify that complex cards can be played at allaccurately."""
        r1 = Requirement(count=1, style=Application(suits=["Suit"]))
        r2 = Requirement(count=1, style=Application(suits=["Other"]))
        a1 = Application(suits=["Suit"])
        a2 = Application(suits=["Other"])
        complex = SpecialCard("Complex", "",
                              r1 | r2,
                              a1 | a2,
                              Effect(EffectType.BUFF, 2))
        self.ai.hand = ([Card("Suit", i+1) for i in range(4)] +
                        [Card("Other", i+5) for i in range(5)] +
                        [complex])
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [complex, Card("Other", 7), Card("Other", 8),
                          Card("Other", 9)])

    @unittest.expectedFailure
    def test_complex_requirement(self):
        """Verify that complex cards can be played accurately."""
        r1 = Requirement(count=1, style=Application(suits=["Suit"]))
        r2 = Requirement(count=1, style=Application(suits=["Other"]))
        a1 = Application(suits=["Suit"])
        a2 = Application(suits=["Other"])
        complex = SpecialCard("Complex", "",
                              r1 & r2,
                              a1 | a2,
                              Effect(EffectType.BUFF, 2))
        self.ai.hand = ([Card("Suit", i+1) for i in range(4)] +
                        [Card("Other", i+5) for i in range(5)] +
                        [complex])
        self.ai.analyze()
        self.assertEqual(sorted(self.ai.get_best_play()),
                         [complex, Card("Suit", 1), Card("Other", 8),
                          Card("Other", 9)])
