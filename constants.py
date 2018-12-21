import enum


class Rank(enum.Enum):
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

    
class Suit(enum.Enum):
    SPADES = 1
    HEARTS = 2
    CLUBS = 3
    DIAMONDS = 4


class Action(enum.Enum):
    DARE = 1
    DIE = 2
    DONE = 3
    DRAW = 4


class DeckState(enum.Enum):
    UNDISCLOSED = 1
    IN_DUEL = 2
    FINISHED = 3


class DuelState(enum.Enum):
    UNSTARTED = 1
    ONGOING = 2
    DRAWN = 3
    FINISHED = 4
    DIED = 5
    ABORTED_BY_CORRECT_DONE = 6
    ABORTED_BY_WRONG_DONE = 7
    ABORTED_BY_WRONG_DRAW = 8
    ABORTED_BEFORE_DOUBLE_DONE = 9


class Duration(object):
    BEFORE_ACTION = 0
    BEFORE_CARD_OPEN = 5
    BEFORE_COIN_TOSS = 3
    BEFORE_DECK_CHOICE = 1
    BEFORE_GAME_START = 3
    ACTION = 7
    FINAL_ACTION = 5
    AFTER_COIN_TOSS = 3
    AFTER_DECK_CHOICE = 3
    AFTER_DUEL_ENDS = 5
    AFTER_GAME_ENDS = 0


class GameResult(enum.Enum):
    FINISHED = 1
    DONE = 2
    FORFEITED_BY_WRONG_DONE = 3
    FORFEITED_BY_WRONG_DRAW = 4
    FORFEITED_BEFORE_DOUBLE_DONE = 5


JOKER = 'Joker'
PLAYER_RED = 'Player Red'
PLAYER_BLACK = 'Player Black'
INDENT = '{:10}'.format(str())

DECK_PER_PILE = 9
CARD_PER_DECK = 3
REQUIRED_POINTS = 3
MAX_DIE = 2
MAX_DONE = 1
MAX_DRAW = 1
