DECK_PER_PILE = 9
CARD_PER_DECK = 3
RANKS = ('Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King')
HIGHEST_VALUE = 13
RED_SUITS = ('Hearts', 'Diamonds')
BLACK_SUITS = ('Spades', 'Clubs')
PLAYER_RED = 'Player Red'
PLAYER_BLACK = 'Player Black'
REQUIRED_WIN = 3
TIME_LIMIT_FOR_ACTION = 7
MAX_DIE = 2
MAX_DONE = 1
MAX_DRAW = 1


class Action(object):
    DARE = 'Dare'
    DIE = 'Die'
    DONE = 'Done'
    DRAW = 'Draw'


class DeckState(object):
    UNOPENED = 'Unopened'
    IN_DUEL = 'In Duel'
    FINISHED = 'Finished'


class DuelResult(object):
    DRAWN = 'Drawn'
    FINISHED = 'Finished'
    DIED = 'Died'
    ABORTED_BY_DONE = 'Aborted by done'
    ABORTED_BY_FORFEIT = 'Aborted by forfeit'


class GameResult(object):
    DRAWN = 'Drawn'
    GAME = 'Finished'
    DONE = 'Done'
    FORFEITED_BY_WRONG_DONE = 'Forfeited by wrong done'
    FORFEITED_BY_WRONG_DRAW = 'Forfeited by wrong draw'
