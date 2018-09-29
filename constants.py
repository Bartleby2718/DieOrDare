DECK_PER_PILE = 9
CARD_PER_DECK = 3
RANKS = ('Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King')
RED_SUITS = ('Hearts', 'Diamonds')
BLACK_SUITS = ('Spades', 'Clubs')


class Action(object):
    DARE = 'dare'
    DIE = 'die'
    DONE = 'done'
    DRAW = 'draw'


class DeckState(object):
    UNOPENED = 'Unopened'
    IN_DUEL = 'In Duel'
    FINISHED = 'Finished'


class DuelResult(object):
    DRAWN = 'Drawn'
    GAME = 'Finished'
    DONE = 'Done'
    ABORTED_BY_DONE = 'Aborted by done'
    ABORTED_BY_FORFEIT = 'Aborted by forfeit'


class GameResult(object):
    DRAWN = 'Drawn'
    GAME = 'Finished'
    DONE = 'Done'
    FORFEITED_BY_DONE = 'Forfeited by done'
    FORFEITED_BY_DRAW = 'Forfeited by draw'
