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
    def __init__(self, name, num_death=0, num_victory=0, done=False, goes_first=False, num_shout_done=0, num_shout_draw=0, decks = []):
        self.name = name
        self.num_death = num_death
        self.num_victory = num_victory
        self.done = done
        self.goes_first = goes_first
        self.num_shout_done = num_shout_doneimport random


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
                 num_shout_draw=0, decks=[]):
        self.name = name
        self.num_death = num_death
        self.num_victory = num_victory
        self.done = done
        self.goes_first = goes_first
        self.num_shout_done = num_shout_done
        self.num_shout_draw = num_shout_draw
        self.decks = decks

    def shout_done(self):
        if check_done(self.decks):
            game_over = True
            # TODO: becomes the winner
        else:
            self.num_shout_done += 1
            if self.num_shout_done > 1:
                game_over = True
                # TODO: the opponent becomes the winner

    def shout_draw(self, duel):
        if check_draw(duel.player1_deck, duel.player2_deck):
            duel.ended_in_draw = True
            duel.winner = self
        else:
            self.num_shout_draw += 1
            if self.num_shout_draw > 1:
                game_over = True
                # TODO: the opponent becomes the winner

    def open_card(self, card):
        card.is_open = True


class Card(object):
    # id, suit, rank, value, open
    def __init__(self, suit, colored, rank, value=None, is_open=False):
        self.suit = suit
        self.colored = colored
        self.rank = rank
        self.value = value
        self.is_open = is_open

    def __repr__(self):
        if self.is_open:
            if self.suit is None:
                return 'Colored Joker' if self.colored else 'Black Joker'
            else:
                return '{} of {}'.format(self.rank, self.suit)
        else:
            return 'Hidden'


class Deck(object):
    # id, player_id, deck_state
    def __init__(self, state, cards):
        self.state = state
        self.cards = cards

    def __repr__(self):
        return ' / '.join([repr(card) for card in self.cards])


class Duel(object):
    # id, ended_in_draw, winner_id
    def __init__(self, player1_deck, player2_deck, state='unopened', ended_in_draw=False, winner=None):
        self.player1_deck = player1_deck
        self.player2_deck = player2_deck
        self.state = state
        self.ended_in_draw = ended_in_draw
        self.winner = winner


# class DeckState(object):
#     # id, name
#     def __init__(self, name):
#         pass
#     pass


# class PlayerGame(object):
# id, player_id, game_id
# pass


# class DeckCard(object):
# id, deck_id, card_id, card_index
# pass


# class DeckDuel(object):
# id, deck_id, duel_id
# pass


def check_done(decks):
    values = []
    for deck in decks:
        for card in deck:
            if card.value not in values:
                values.append(card.value)
    return len(values) == 13


def check_draw(deck1, deck2):
    return sum([card.value for card in deck1]) == sum([card.value for card in deck2])


# initialize basic variables
black_suits = ['Spades', 'Clubs']
red_suits = ['Hearts', 'Diamonds']
suits = black_suits + red_suits
# TODO: AI Issue #1
red_joker = Card(None, True, 'Joker', 13)
black_joker = Card(None, False, 'Joker', 13)
ranks = ['Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King']
red_pile = [red_joker] + [Card(suit, True, rank, ranks.index(rank)) for suit in red_suits for rank in ranks]
black_pile = [black_joker] + [Card(suit, False, rank, ranks.index(rank)) for suit in black_suits for rank in ranks]
piles = [black_pile, red_pile]
deck_state = ['unopened', 'in_duel', 'is_open']
deck_per_pile = 9
card_per_deck = 3

print("Let's start DieOrDare! ")

# initialize players with name validation
player1_name = '?'
while not player1_name.isalnum():
    player1_name = input("Enter player 1's name: ")
player1 = Player(player1_name)
player2_name = '?'
while not player2_name.isalnum() or player1_name == player2_name:
    player2_name = input("Enter player 2's name: ")
player2 = Player(player2_name)
players = [player1, player2]
print()
print("All right, {} and {}. Let's get started!".format(player1_name, player2_name))

# decide which buttons to use for player 1
print("{}(Player 1), let's decide which buttons to use.".format(player1_name))
player1_characters = []
characters = []
player1_dare_character = '?'
while not player1_dare_character.isalnum() or player1_dare_character in characters:
    player1_dare_character = input('Which button will you use to indicate dare? ')
player1_characters.append(player1_dare_character)
characters.append(player1_dare_character)
player1_die_character = '?'
while not player1_die_character.isalnum() or player1_die_character in characters:
    player1_die_character = input('Which button will you use to indicate die? ')
player1_characters.append(player1_die_character)
characters.append(player1_die_character)
player1_done_character = '?'
while not player1_done_character.isalnum() or player1_done_character in characters:
    player1_done_character = input('Which button will you use to indicate done? ')
player1_characters.append(player1_done_character)
characters.append(player1_done_character)
player1_draw_character = '?'
while not player1_draw_character.isalnum() or player1_draw_character in characters:
    player1_draw_character = input('Which button will you use to indicate draw? ')
player1_characters.append(player1_draw_character)
characters.append(player1_draw_character)

# decide which buttons to use for player 2
print()
print("{}(Player 2), let's decide which buttons to use.".format(player2_name))
player2_characters = []
player2_dare_character = '?'
while not player2_dare_character.isalnum() or player2_dare_character in characters:
    player2_dare_character = input('Which button will you use to indicate dare? ')
player2_characters.append(player2_dare_character)
characters.append(player2_dare_character)
player2_die_character = '?'
while not player2_die_character.isalnum() or player2_die_character in characters:
    player2_die_character = input('Which button will you use to indicate die? ')
player2_characters.append(player2_die_character)
characters.append(player2_die_character)
player2_done_character = '?'
while not player2_done_character.isalnum() or player2_done_character in characters:
    player2_done_character = input('Which button will you use to indicate done? ')
player2_characters.append(player2_done_character)
characters.append(player2_done_character)
player2_draw_character = '?'
while not player2_draw_character.isalnum() or player2_draw_character in characters:
    player2_draw_character = input('Which button will you use to indicate draw? ')
player2_characters.append(player2_draw_character)
characters.append(player2_draw_character)

players = [player1, player2]
# toss a coin to decide who takes the red pile and gets to go first
if random.random() > .5:
    player1.goes_first = True
else:
    player2.goes_first = True
players.sort(key=lambda x: x.goes_first)

# draw cards to form 9 decks for each player
for player in players:
    for pile in piles:
        random.shuffle(pile)
        decks = []
        for deck_index in range(deck_per_pile):
            cards = []
            for card_index in range(card_per_deck):
                cards.append(pile.pop())
            # TODO: AI Issue #2
            cards.sort(key=lambda x: x.value)
            player.open_card(cards[-1])
            new_deck = Deck('unopened', cards)
            decks.append(new_deck)
        # TODO: sort decks based on the biggest number
        decks.sort(key=lambda x: (x.cards[-1].value, x.cards[-1].suit))
        player.decks = decks
        print(decks)

        duel_index = 0
        game_over = False
        # TODO: start duel
game_over = True
while not game_over:
    duel_index += 1
    print('Starting Duel {}...'.format(duel_index))
    print('Your delegates are: ')
    print('Choose one of your deck: ')
    print("The opponent's delegates are: ")
    print("Choose one of the opponent's deck: ")
# print(Duel )


# TODO: print ending statements
        self.num_shout_draw = num_shout_draw
        self.decks = decks

    def shout_done(self, decks):
        pass

    def shout_draw(self, deck):
        pass

    def open_card(self, card):
        pass

    pass


class Card(object):
    # id, suit, rank, value, open
    def __init__(self, suit, colored, rank, value=None, is_open=False):
        self.suit = suit
        self.colored = colored
        self.rank = rank
        self.value = value
        self.is_open = is_open

    def __str__(self):
        if self.is_open:
            if suit is None:
                return 'Colored Joker' if self.colored else 'Black Joker'
            else:
                return '{} of {}'.format(rank, suit)


class Deck(object):
    # id, player_id, deck_state
    def __init__(self, player, state, cards):
        self.player = player
        self.state = state
        self.cards = cards

    def __str__(self):
        return ' / '.join(cards)



class Duel(object):
    # id, ended_in_draw, winner_id
    def __init__(self, player1_deck, player2_deck, state='unopened', ended_in_draw=False, winner=None):
        self.player1_deck = player1_deck
        self.player2_deck = player1_deck
        self.state = state
        self.ended_in_draw = ended_in_draw
        self.winner = winner


# class DeckState(object):
#     # id, name
#     def __init__(self, name):
#         pass
#     pass


# class PlayerGame(object):
    # id, player_id, game_id
    # pass


# class DeckCard(object):
    # id, deck_id, card_id, card_index
    # pass


# class DeckDuel(object):
    # id, deck_id, duel_id
    # pass


def check_done(decks):
    values = []
    for deck in decks:
        dor card in deck
  pass

def check_draw(deck):
    pass
  
# initialize basic variables
black_suits = ['Spades', 'Clubs']
red_suits = ['Hearts', 'Diamonds']
suits = black_suits + red_suits
# TODO: AI Issue #1
black_joker = Card(None, True, 'Joker', 13)
red_joker = Card(None, False, 'Joker', 13)
ranks = ['Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King']
red_pile = [red_joker] + [Card(suit, True, rank, value) for suit in suits for rank in ranks for value in range(1, 14)]
black_pile = [black_joker] + [Card(suit, False, rank, value) for suit in suits for rank in ranks for value in
                              range(1, 14)]
piles = [black_pile, red_pile]
deck_state = ['unopened', 'in_duel', 'is_open']
deck_per_pile = 9
card_per_deck = 3

print("Let's start DieOrDare! ")

# TODO: initialize players with name validation
player1_name = '?'
while not player1_name.isalnum():
    player1_name = input("Enter player 1's name: ")
player1 = Player(player1_name)
player2_name = '?'
while not player2_name.isalnum() or player1_name==player2_name:
    player2_name = input("Enter player 2's name: ")
player2 = Player(player2_name)
players = [player1, player2]
print()
print("All right, {} and {}. Let's get started!".format(player1_name, player2_name))

# decide which buttons to use for player 1
print("{}(Player 1), let's decide which buttons to use.".format(player1_name))
player1_characters = []
characters = []
player1_dare_character = '?'
while not player1_dare_character.isalnum() or player1_dare_character in characters:
    player1_dare_character = input('Which button will you use to indicate dare?')
player1_characters.append(player1_dare_character)
characters.append(player1_dare_character)
player1_die_character = '?'
while not player1_die_character.isalnum() or player1_die_character in characters:
    player1_die_character = input('Which button will you use to indicate die?')
player1_characters.append(player1_die_character)
characters.append(player1_die_character)
player1_done_character = '?'
while not player1_done_character.isalnum() or player1_done_character in characters:
    player1_done_character = input('Which button will you use to indicate done?')
player1_characters.append(player1_done_character)
characters.append(player1_done_character)
player1_draw_character = '?'
while not player1_draw_character.isalnum() or player1_draw_character in characters:
    player1_draw_character = input('Which button will you use to indicate draw?')
player1_characters.append(player1_draw_character)
characters.append(player1_draw_character)

# decide which buttons to use for player 2
print()
print("{}(Player 2), let's decide which buttons to use.".format(player2_name))
player2_characters = []
player2_dare_character = '?'
while not player2_dare_character.isalnum() or player2_dare_character in characters:
    player2_dare_character = input('Which button will you use to indicate dare?')
player2_characters.append(player2_dare_character)
characters.append(player2_dare_character)
player2_die_character = '?'
while not player2_die_character.isalnum() or player2_die_character in characters:
    player2_die_character = input('Which button will you use to indicate die?')
player2_characters.append(player2_die_character)
characters.append(player2_die_character)
player2_done_character = '?'
while not player2_done_character.isalnum() or player2_done_character in characters:
    player2_done_character = input('Which button will you use to indicate done?')
player2_characters.append(player2_done_character)
characters.append(player2_done_character)
player2_draw_character = '?'
while not player2_draw_character.isalnum() or player2_draw_character in characters:
    player2_draw_character = input('Which button will you use to indicate draw?')
player2_characters.append(player2_draw_character)
characters.append(player2_draw_character)

players = [player1, player2]
# TODO: toss a coin to decide who takes the red pile and gets to go first
if random.random() > .5:
    player1.goes_first = True
else:
    player2.goes_first = True
players.sort(key=lambda x: x.goes_first)

# TODO: draw cards to form 9 decks for each player
for player in players:
    for pile in piles:
        random.shuffle(pile)
        decks = []
        for deck_index in range(deck_per_pile):
            cards = []
            for card_index in range(card_per_deck):
                cards.append(pile.pop())
            # TODO: AI Issue #2
            cards.sort(key=lambda x: x.value)
            player.open_card(cards[-1])
            new_deck = Deck(player, 'unopened', cards)
            decks. append(new_deck)
        # TODO: sort decks based on the biggest number
        decks.sort(key=lambda x:(x.cards[-1].value, x.cards[-1].suit)

duel_index = 0
game_over = False
# TODO: start duel
while not game_over:
    duel_index += 1
    print('Starting Duel {}...'.format(duel_index))
    print('Your delegates are:')
# Choose one of your deck
# The opponent's delegates are:
# Choose one of the opponent's deck
# print(Duel )


# TODO: print ending statements
