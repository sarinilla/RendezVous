"""Intelligently select cards to play from a Hand.

Strategy:
  * Play according to HELD cards on the board (ours or theirs)
  * Attempt to play a special with complimentary normal cards.
  * Attempt to play a KISS with low normal cards.
  * Attempt to play high normal cards.
  * Attempt to play a FLUSH with debuffs or the highest possible cards.
  * Play anything!
  * Pass


Known Issues:
  * Some trouble playing complex SpecialCards, specifically mixed AT LEAST
    and NO MORE THAN requirement types.
  
"""

import random

from rendezvous import SpecialSuit, SpecialValue, Alignment, EffectType, Operator


class PossiblePlay:

    """One possible set of cards to play this turn."""

    def __init__(self, cards, board, score, hand, player_index):
        """Decide on the best configuration of cards, and score it.

        Arguments:
          cards -- suggested cards to play
          board -- 2D [player][index] board of held cards (if any)
          score -- 2D [player][suit] current scores in each suit
          hand  -- list of all cards available to be played
          player_index -- index of the current player

        """
        self.cards = cards
        self.board = board
        self.score = score
        self.hand = hand
        self.player = player_index
        self._apply_specials()
        self._arrange()
        self._remove_specials()
        self.value = self._calculate()

    def __lt__(self, other):
        """Sort by the value of this play."""
        try:
            return self.value < other.value
        except AttributeError:
            return -1

    def __str__(self):
        """Human-readable notation of the play."""
        return "play %s for %s pts" % ([str(c) for c in self.cards], self.value)

    def _board_empty(self, player_index):
        """Return True if the board passed is empty (all None) for this player."""
        for card in self.board[player_index]:
            if card is not None:
                return False
        return True
    def player_empty(self):
        """See if the player's board is empty (none held)."""
        return self._board_empty(self.player)
    def dealer_empty(self):
        """See if the dealer's board is empty (none held)."""
        return self._board_empty(self.player - 1)

    def _apply_specials(self):
        """Apply buffs/debuffs before arranging cards."""
        for card in self.cards:
            if card.suit != SpecialSuit.SPECIAL:
                continue
            if card.effect.effect == EffectType.BUFF:
                for ocard in self.cards:
                    if card.application.match(Alignment.FRIENDLY, ocard):
                        ocard.apply(card.effect)
                for ecard in self.board[self.player - 1]:
                    if ecard is not None:
                        if card.application.match(Alignment.ENEMY, ecard):
                            ecard.apply(card.effect)
            elif card.effect.effect == EffectType.SWITCH:
                for ocard in self.cards:
                    if (ocard.suit != SpecialSuit.SPECIAL and
                        (card.application.has_alignment(Alignment.ENEMY) or
                         card.application.match(Alignment.FRIENDLY, ocard))):
                        ocard.value *= -1
                for ecard in self.board[self.player - 1]:
                    if ecard is not None and ecard.suit != SpecialSuit.SPECIAL:
                        if (card.application.has_alignment(Alignment.FRIENDLY) or
                            card.application.match(Alignment.ENEMY, ecard)):
                            ecard.value *= -1
            elif card.effect.effect == EffectType.REVERSE:
                for ocard in self.cards:
                    if card.application.match(Alignment.FRIENDLY, ocard):
                        ocard.value = 11 - ocard.value
                for ecard in self.board[self.player - 1]:
                    if ecard is not None:
                        if card.application.match(Alignment.ENEMY, ecard):
                            ecard.value = 11 - ecard.value

    def _remove_specials(self):
        """Remove the effects of specials temporarily applied."""
        for card in self.cards + self.board[self.player - 1]:
            try:
                card.reset()
            except AttributeError:
                pass

    def _arrange(self):
        """Determine the best order for the cards."""
        for card in self.cards:
            if (card.suit == SpecialSuit.SPECIAL and
                card.effect.effect == EffectType.CLONE):
                self.cards.sort(reverse=True)
                return
        if self.dealer_empty():
            random.shuffle(self.cards)
            return
        offset = 0
        self.cards.sort()
        for i, dealer in enumerate(self.board[self.player - 1]):
            if self.board[self.player][i] is not None:
                offset += 1
                continue
            if self.board[self.player-1][i] is not None:
                target = self.board[self.player-1][i].value
                if target == SpecialValue.SPECIAL:
                    continue
                for j, card in enumerate(self.cards):
                    if (card.value > target and  # beats target, not used
                        (j > i or self.board[self.player-1][j] is None)):
                        self.cards[i-offset], self.cards[j] = \
                                    self.cards[j], self.cards[i-offset]
                        self.cards[i-offset+1:] = sorted(self.cards[i-offset+1:])
                        break
                else:
                    self.cards[i-offset], self.cards[0] = self.cards[0], self.cards[i-offset]
        
    def _calculate(self):
        """Score this potential play."""
        value = 0
        for i, card in enumerate(self.cards):

            # Bonus for a block or close win over a hold
            if self.board[self.player-1][i] is not None:
                evalue = self.board[self.player-1][i].value
                if card.value == SpecialValue.SPECIAL:
                    value += 10
                elif card.value > evalue and card.value - evalue < 2:
                    value += 10

            # Standard cards worth their value
            if card.value != SpecialValue.SPECIAL:
                value += card.value
                continue

            # 10-pt bonus for SpecialCards!
            value += 10

            # Adjust buffed card values and known debuffs
            if card.effect.effect == EffectType.BUFF:
                for ocard in self.cards:
                    if card.application.match(Alignment.FRIENDLY, ocard):
                        value += card.effect.value
                for hcard in self.board[self.player]:
                    if card.application.match(Alignment.FRIENDLY, hcard):
                        value += card.effect.value + 5
                for ecard in self.board[self.player-1]:
                    if card.application.match(Alignment.ENEMY, ecard):
                        value -= card.effect.value
                # Assume one unknown debuff
                if card.application.has_alignment(Alignment.ENEMY):
                    value -= card.effect.value

            # Score low cards (<5) for SWITCH/REVERSE/KISS
            elif (card.effect.effect == EffectType.SWITCH or
                  card.effect.effect == EffectType.REVERSE or
                  card.effect.effect == EffectType.KISS):
                for ocard in self.cards:
                    if card.application.match(Alignment.FRIENDLY, ocard):
                        value -= ocard.value
                        if ocard.value < 5:
                            value += 11 - ocard.value
                for ecard in self.board[self.player-1]:
                    if card.application.match(Alignment.ENEMY, ecard):
                        if ecard.value > 6:
                            value += ecard.value
                        elif ecard.value < 5:
                            value -= 11 - ecard.value
                if card.application.has_alignment(Alignment.ENEMY):
                    value += 5

            # Score all cards as the CLONE
            elif card.effect.effect == EffectType.CLONE:
                rcard = None
                for ocard in self.cards:
                    if ocard.suit == SpecialSuit.SPECIAL:
                        continue
                    elif rcard is not None:
                        value -= ocard.value
                        value += rcard.value
                    elif card.application.match(Alignment.FRIENDLY, ocard, None):
                        rcard = ocard
                if card.application.alignment in (Alignment.ENEMY,
                                                  Alignment.ALL):
                    ecard = self.board[self.player-1][0]
                    if (ecard is not None and
                        card.application.match(Alignment.ENEMY, ecard)):
                        if ecard.value < 5:
                            value += ecard.value * (len(self.board[self.player-1])-1)
                        elif ecard.value > 6:
                            value -= ecard.value * (len(self.board[self.player-1])-1)

            # Score low cards (and not good specials!) with FLUSH
            elif card.effect.effect == EffectType.FLUSH:
                for ocard in self.hand:
                    if ocard not in self.cards:
                        if ocard.suit == SpecialSuit.SPECIAL:
                            if ocard.effect.effect in (EffectType.WAIT,
                                                       EffectType.SWITCH,
                                                       EffectType.REVERSE,
                                                       EffectType.KISS,
                                                       EffectType.FLUSH):
                                value -= 50
                        else:
                            value += 6 - ocard.value
        return value

    def verify(self):
        """Double-check that the SpecialCard requirements are met."""
        for card in self.cards:
            if card.suit == SpecialSuit.SPECIAL:
                if not card.requirement.verify(self.cards +
                                               self.board[self.player]):
                    return False
        return True
    

class ArtificialIntelligence:

    """Used to determine the best cards to play from the hand."""

    def __init__(self, player, hand, board, score):
        """Analyze hand and prepare intelligent options.

        Arguments:
          player -- player index into board and score
          hand   -- list of available cards (or Hand object)
          board  -- 2D [player][index] list of spaces (or Gameboard)
          score  -- 2D [player][suit] list of scores (or Scoreboard)
        """
        self.player = player
        self.hand = hand
        self.board = board
        self.score = score
        self.analyze()

    def analyze(self):
        """Consider all of the variables and explore possible plays.

        Outputs:
          self.possible_plays -- all (or a selection of the best) plays

        """
        self.possible_plays = []
        self._consider_holds()
        if self._cards_needed == 0:
            self.possible_plays.append(PossiblePlay([], self.board,
                                                        self.score, self.hand,
                                                        self.player))
            return
        self._consider_specials()
        self._consider_values()
        self._meet_targets()
        self.possible_plays.sort(reverse=True)
        self._verify()

    def get_best_play(self):
        """Return the best play available.

        Raise IndexError if no possible plays.
        """
        return self.possible_plays[0].cards

    def _consider_holds(self):
        
        """Consider the effect of any holds present on the board.

        Outputs:
          self._cards_needed  -- how many cards to choose
          self._targets       -- values to beat

        """

        self._cards_needed = self.board[self.player].count(None)
        
        self._targets = []
        for ecard in self.board[self.player - 1]:
            if ecard is not None and ecard.value != SpecialValue.SPECIAL:
                self._targets.append(ecard.value)
                
    def _consider_specials(self, given=[]):
        """Consider the available SpecialCards and their requirements."""
        for g in given:
            self.hand.remove(g)
        self.hand.sort(reverse=True)
        for card in self.hand:
            if card.suit != SpecialSuit.SPECIAL:
                continue

            # Do we even have the requirements?
            if not (card.requirement.has_operator(Operator.NO_MORE_THAN) or
                    card.requirement.verify(list(self.hand) +
                                            self.board[self.player])):
                continue

            # Grab best cards meeting requirements
            required = applied = []
            required = card.requirement.filter(Alignment.FRIENDLY, self.hand)
            applied = card.requirement.filter(Alignment.FRIENDLY,
                                              self.board[self.player])
            needed = card.requirement.totalcount() - len(applied)
            cards = given + [card]
            reverse_values = card.effect.effect in (EffectType.SWITCH,
                                                    EffectType.REVERSE,
                                                    EffectType.KISS)
            def adjusted_value(req_card):
                """Prefer cards that will be affected, and account for reversal."""
                val = req_card.value
                if reverse_values:
                    val = -val
                if card.application.match(Alignment.FRIENDLY, req_card):
                    val += 50
                return val
            if not card.requirement.has_operator(Operator.NO_MORE_THAN):
                required.sort(key=adjusted_value, reverse=True)
                if card.effect.effect == EffectType.CLONE and required:
                    cards.append(required[0])
                    required.sort()  # then get low ones!
                    needed -= 1
                cards.extend(required[:needed])
                if len(cards) > self._cards_needed:
                    continue  # can't play this one

            # Grab best cards it will be applied to
            if reverse_values:
                self.hand.sort(reverse=False)
            applies = list(filter(lambda x: x not in cards,
                                  card.application.filter(Alignment.FRIENDLY,
                                                          self.hand)))
            if not card.requirement.has_operator(Operator.AT_LEAST):
                applies = list(filter(lambda x: x not in required,
                                      applies))
            if (card.effect.effect == EffectType.CLONE and
                self._cards_needed > len(cards)):
                cards.append(applies[0])
            else:
                cards.extend(applies[:self._cards_needed - len(cards)])
            if reverse_values:
                self.hand.sort(reverse=True)

            # Grab best filler cards (no specials)
            extra = list(filter(lambda x: x not in cards and
                                          x.suit != SpecialSuit.SPECIAL,
                                self.hand))
            if not card.requirement.has_operator(Operator.AT_LEAST):
                extra = list(filter(lambda x: x not in required,
                                    extra))
            if card.effect.effect == EffectType.CLONE:
                if len(list(card.application.filter(Alignment.FRIENDLY, cards))):
                    extra.sort()
            cards.extend(extra[:self._cards_needed - len(cards)])
            
            # Fill with matching / no-requirement specials if needed
            if len(cards) < self._cards_needed:
                specials = list(filter(lambda x: x not in cards and
                                                 x.suit == SpecialSuit.SPECIAL,
                                       self.hand))
                for scard in specials:
                    if (scard.requirement.verify(cards) and
                        len(scard.application.filter(Alignment.FRIENDLY, cards))):
                        cards.append(scard)
                        if len(cards) == self._cards_needed:
                            break
                        specials.remove(scard)
                else:
                    for scard in specials:
                        if scard.requirement.verify(cards):
                            cards.append(scard)
                            if len(cards) == self._cards_needed:
                                break

            # Save play only if we found enough cards
            if len(cards) == self._cards_needed:
                self.possible_plays.append(PossiblePlay(cards, self.board,
                                                        self.score, self.hand,
                                                        self.player))
        self.hand.extend(given)

    def _consider_values(self, given=[]):
        """Pick the highest filler cards we have."""
        possible = list(filter(lambda x: x not in given and
                                         x.suit != SpecialSuit.SPECIAL,
                               self.hand))
        possible.sort(reverse=True)
        cards = given + possible[:self._cards_needed-len(given)]
        if len(cards) == self._cards_needed:
            self.possible_plays.append(PossiblePlay(cards, self.board,
                                                    self.score, self.hand,
                                                    self.player))

    def _meet_targets(self):
        """Consider additional possibilities based on hold targets."""
        if self._targets == []:
            return
        possible = list(filter(lambda x: x.suit != SpecialSuit.SPECIAL,
                               self.hand))
        possible.sort()
        given = []
        for target in self._targets:
            for card in possible:
                if card.value > target:
                    given.append(card)
                    possible.remove(card)
                    break
        if given:
            self._consider_specials(given)
            self._consider_values(given)

    def _verify(self):
        """Double-check requirements on specials for the best play only."""
        while self.possible_plays:
            if not self.possible_plays[0].verify():
                self.possible_plays.pop(0)
            else:
                break
        
