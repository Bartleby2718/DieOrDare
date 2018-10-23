import enum

DECK_PER_PILE = 9
CARD_PER_DECK = 3
RANKS = ('Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King')
HIGHEST_VALUE = NUM_CARD = len(RANKS)
RED_SUITS = ('Hearts', 'Diamonds')
BLACK_SUITS = ('Spades', 'Clubs')
JOKER = 'Joker'
PLAYER_RED = 'Player Red'
PLAYER_BLACK = 'Player Black'
REQUIRED_WIN = 3
TIME_LIMIT_FOR_ACTION = 7
TIME_LIMIT_FOR_FINAL_ACTION = 5
DELAY_AFTER_TURN_NOTICE = 1
DELAY_BEFORE_CARD_OPEN = 5
DELAY_AFTER_DUEL_ENDS = 5

MAX_DIE = 2
MAX_DONE = 1
MAX_DRAW = 1


class Action(enum.Enum):
    DARE = 'Dare'
    DIE = 'Die'
    DONE = 'Done'
    DRAW = 'Draw'


class DeckState(enum.Enum):
    UNOPENED = 'Unopened'
    IN_DUEL = 'In Duel'
    FINISHED = 'Finished'


class DuelState(enum.Enum):
    ONGOING = 'Ongoing'
    DRAWN = 'Drawn'
    FINISHED = 'Finished'
    DIED = 'Died'
    ABORTED_BY_CORRECT_DONE = 'Aborted by correct done'
    ABORTED_BY_WRONG_DONE = 'Aborted by wrong done'
    ABORTED_BY_WRONG_DRAW = 'Aborted by wrong draw'
    ABORTED_BEFORE_DOUBLE_DONE = 'Aborted before double done'


class GameResult(enum.Enum):
    FINISHED = 'Finished'
    DONE = 'Done'
    FORFEITED_BY_WRONG_DONE = 'Forfeited by wrong done'
    FORFEITED_BY_WRONG_DRAW = 'Forfeited by wrong draw'
    FORFEITED_BEFORE_DOUBLE_DONE = 'Forfeited before double done'
