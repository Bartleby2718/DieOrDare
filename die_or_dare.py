import getpass
import random


# TODO: AI Decisions to be made
# 1) 조커를 몇으로 할지 : 일단 13
# 2) 제일 큰 게 하나가 아닐 때 어떤 suit을 위에 둘지 : 조커 -> 아무거나
# 3) 두 번째 카드 공개 후 die할지 : 고민 좀
# 4) 언제 draw라고 외칠지 : 고민 좀


class User(object):
    # id, name, time_created
    pass


class Game(object):
    # id, over, time_created, time_ended
    pass


class Player(object):
    # id, user_id, num_death, num_victory, done, my_turn, num_shout_done, num_shout_draw
    def __init__(self, name, num_death=0, num_victory=0, done=False, goes_first=False, num_shout_done=0,
                 num_shout_draw=0):
        pass

    def shout_done(self):
        pass

    def shout_draw(self, deck):
        pass

    def open_card(self, card):
        pass

    pass


class Card(object):
    # id, suit, rank, value, open
    def __init__(self, suit, colored, rank, value=None, open=False):
        pass

    pass


class Deck(object):
    # id, player_id, deck_state
    def __init__(self, player, state):
        pass

    pass


class Duel(object):
    # id, ended_in_draw, winner_id
    def __init__(self, player1_deck, player2_deck, state='unopened', ended_in_draw=False, winner=None):
        pass

    pass


# class DeckState(object):
#     # id, name
#     def __init__(self, name):
#         pass
#     pass


class PlayerGame(object):
    # id, player_id, game_id
    pass


class DeckCard(object):
    # id, deck_id, card_id, card_index
    pass


class DeckDuel(object):
    # id, deck_id, duel_id
    pass


# initialize basic variables
black_suits = ['spades', 'clubs']
red_suits = ['hearts', 'diamonds']
suits = black_suits + red_suits
# TODO: AI Issue #1
black_joker = Card(None, True, 'joker', 13)
red_joker = Card(None, False, 'joker', 13)
ranks = ['Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King']
red_pile = [red_joker] + [Card(suit, True, rank, value) for suit in suits for rank in ranks for value in range(1, 14)]
black_pile = [black_joker] + [Card(suit, False, rank, value) for suit in suits for rank in ranks for value in
                              range(1, 14)]
piles = [red_pile, black_pile]
deck_state = ['unopened', 'in_duel', 'open']
deck_per_pile = 9
card_per_deck = 3

print("Let's start DieOrDare!: ")

# TODO: initialize players with name validation
player1_name = None
while not player1_name.isalnum():
    player1_name = input("Enter player 1's name: ")
player1 = Player(player1_name)
player2_name = None
while not player2_name.isalnum():
    player2_name = input("Enter player 2's name: ")
player2 = Player(player2_name)
players = [player1, player2]

# decide which buttons to use for player 1
player1_dare_character = None
while not player1_dare_character.isalnum():
    player1_dare_character = input('Which button will you use to indicate dare?')
characters = [player1_dare_character]
player1_die_character = None
while not player1_die_character.isalnum or player1_die_character in characters:
    player1_ = input('Which button will you use to indicate die?')
characters.append(player1_die_character)
player1_done_chracter = None
while not player1_done_character.isalnum or player1_done_character in characters:
    player1_done_character = input('Which button will you use to indicate done?')
characters.append(player1_done_character)
player1_draw_character = None
while not player1_draw_character.isalnum() or player1_draw_character in characters:
    player1_draw_character = input('Which button will you use to indicate draw?')
characters.append(player1_draw_character)
player1_characters =
import copy copy.copy()
# decide which buttons to use for player 2
player2_dare_character = None
while not player2_dare_character.isalnum() or player2_dare_character in characters:
    player2_dare_character = input('Which button will you use to indicate dare?')
characters.append(player2_dare_character)
player2_die_character = None
while not player2_die_character.isalnum or player2_die_character in characters:
    player2_ = input('Which button will you use to indicate die?')
characters.append(player2_die_character)
player2_done_chracter = None
while not player2_done_character.isalnum or player2_done_character in characters:
    player2_done_character = input('Which button will you use to indicate done?')
characters.append(player2_done_character)
player2_draw_character = None
while not player2_draw_character.isalnum() or player2_draw_character in characters:
    player2_draw_character = input('Which button will you use to indicate draw?')
characters.append(player2_draw_character)

players = [player1, player2]
# TODO: toss a coin to decide who takes the red pile and gets to go first
# blah b
player1.goes_first = True
players.sort(key=lambda x: x.goes_first)

# TODO: draw cards to form 9 decks for each player
for player in players:
    for pile in piles:
        random.shuffle(pile)
        decks = []
        for deck_index in range(deck_per_pile):
            deck = []
            for card_index in range(card_per_deck):
                deck.append(pile.pop())
            # TODO: AI Issue #2
            deck.sort(key=lambda x: x.value)
            player.open_card(deck[-1])
        # TODO: sort decks based on the biggest number

# TODO: start duel
# Your heads are:
# The opponent's heads are:
# Choose one of your deck
# Choose one of the opponent's deck
# print(Duel )


# TODO: print ending statements
