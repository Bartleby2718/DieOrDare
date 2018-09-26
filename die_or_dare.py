import random
import time


# TODO: AI Issues (나중에 AI vs AI 하게):
# 1) decide_joker_value: 조커를 몇으로 할지 -> 일단 13
# 2) decide_delegate: 값이 제일 큰 게 둘 이상일 때 delegate -> 일단 suit 알파벳순
# 3) decide_deck_order: delegate의 값이 같은 덱이 둘 이상 있을 때 순서 -> 일단 suit 알파벳순
# 4) decide_die_or_not: 두 번째 카드 공개 후 die할지 -> 일단 일단 확률 80% 초과할 때만
# 5) decide_draw_timing: 언제 draw라고 외칠지 -> 일단 안 외침


# class User(object):
#     id, name, time_created
#     pass


# class Game(object):
# id, player_red, player_black, over, ended_reason, time_created, time_ended, winner, lose

class Player(object):
    # id, user_id, num_death, num_victory, done, my_turn, num_shout_done, num_shout_draw
    def __init__(self, name, num_death=0, num_victory=0, done=False, num_shout_done=0,
                 num_shout_draw=0, decks=None):
        self.name = name
        self.num_death = num_death
        self.num_victory = num_victory
        self.done = done
        self.num_shout_done = num_shout_done
        self.num_shout_draw = num_shout_draw
        self.decks = decks

    def shout_done(self):
        if check_done(self.decks):
            game_over = True
            ended_reason = 'done'
            time.ended = time.time()
            winner = self
            # TODO: the opponent loses the game
        else:
            self.num_shout_done += 1
            if self.num_shout_done > 1:
                game_over = True
                ended_reason = 'done'
                time.ended = time.time()
                # TODO: the opponent wins the game
                loser = self

    def shout_draw(self, duel):
        if check_draw(duel.player1_deck, duel.player2_deck):
            duel.state='ended'
            duel.ended_in_draw = True
            # TODO: you win the duel
            # TODO: the opponent loses the duel
            loser=None
        else:
            self.num_shout_draw += 1
            if self.num_shout_draw > 1:
                duel.state='ended'
                duel.ended_in_draw = True
                game_over = True
                ended_reason = 'done'
                time.ended = time.time()
                # TODO: the opponent wins the game
                loser = self
                

    def open_card(self, card):
        card.is_open = True
        return card


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

    def delegate(self):
        return self.cards[0]


class Duel(object):
    # id, ended_in_draw, winner_id
    def __init__(self, player1_deck, player2_deck, state='unopened', ended_in_draw=False, winner=None, loser=None):
        self.player1_deck = player1_deck
        self.player2_deck = player2_deck
        self.state = state
        self.ended_in_draw = ended_in_draw
        self.winner = winner


# class DeckState(object):
#     # id, name
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


# Setup
black_suits = ['Spades', 'Clubs']
red_suits = ['Hearts', 'Diamonds']
suits = black_suits + red_suits
# TODO: AI Issue #1
red_joker = Card(None, True, 'Joker', 13)
black_joker = Card(None, False, 'Joker', 13)
ranks = ['Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King']
red_pile = [red_joker] + [Card(suit, True, rank, ranks.index(rank)) for suit in red_suits for rank in ranks]
black_pile = [black_joker] + [Card(suit, False, rank, ranks.index(rank)) for suit in black_suits for rank in ranks]
piles = [red_pile, black_pile]
deck_state = ['unopened', 'in_duel', 'is_open']
deck_per_pile = 9
card_per_deck = 3

print("Let's start DieOrDare! ")

# Initialize players with name validation
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

# Decide which buttons to use for player 1
print("{}(Player 1), let's decide which buttons to use.".format(player1_name))
player1_characters_settings = {'dare': '', 'die': '', 'done': '', 'draw': ''}
for action in player1_characters_settings:
    character = player1_characters_settings.get(action)
    while not character.isalnum() or character in player1_characters_settings.values():
        character = input('Which character will you use to indicate {}? '.format(action))
    player1_characters_settings[action] = character

# Decide which buttons to use for player 2
print()
print("{}(Player 2), let's decide which buttons to use.".format(player2_name))
player2_characters_settings = {'dare': '', 'die': '', 'done': '', 'draw': ''}
for action in player2_characters_settings:
    character = player2_characters_settings.get(action)
    used_characters = list(player1_characters_settings.values()) + list(player2_characters_settings.values())
    while not character.isalnum() or character in used_characters:
        character = input('Which character will you use to indicate {}? '.format(action))
    player2_characters_settings[action] = character

# Toss a coin to decide who will be the player_red (takes the red pile & goes first)
if random.random() > .5:
    player_red = player1
    player_black = player2
else:
    player_red = player2
    player_black = player1
players = [player_red, player_black]

# Start game
game_over = False
ended_reason = None
time_created = time.time()
time.ended = None
winner = None
loser = None

print()
# Draw cards to form 9 decks for each player
for i in range(2):
    # red first
    player = players[i]
    pile = piles[i]
    random.shuffle(pile)
    decks = []
    for j in range(deck_per_pile):
        cards = []
        for k in range(card_per_deck):
            cards.append(pile.pop())
        # TODO: AI Issue #2
        cards.sort(key=lambda x: (-x.value, x.suit))
        player.open_card(cards[0])
        new_deck = Deck('unopened', cards)
        decks.append(new_deck)
    # TODO: sort decks based on the biggest number
    decks.sort(key=lambda x: (x.cards[0].value, x.cards[0].suit))
    player.decks = decks

    duel_index = 0
    game_over = False
    # TODO: start duel

while not game_over:
    duel_index += 1
    if duel_index % 2 == 1:
        offense = player_red
        defense = player_black
    else:
        offense = player_black
        defense = player_red
    print()
    print('Starting Duel {}...'.format(duel_index))
    print('{}, your turn!'.format(offense.name))

    # Print both players' decks
    offense_valid_choice = False
    # Choose offense deck
    while not offense_valid_choice:
        print()
        print('The delegates of your unopened decks are: ')
        for i, deck in enumerate(offense.decks):
            if deck.state == 'unopened':
                print('\tDeck {}: {}'.format(i + 1, deck.delegate()))
        print("The delegates of your opponent's unopened decks are: ")
        for i, deck in enumerate(defense.decks):
            if deck.state == 'unopened':
                print('\tDeck {}: {}'.format(i + 1, deck.delegate()))
        offense_deck_index = input('Choose one of your deck (Enter the deck number): ')
        try:
            index = int(offense_deck_index) - 1
            offense_deck = offense.decks[index]
            if index >= 0 and offense_deck.state == 'unopened':
                offense_valid_choice = True
                offense_deck.state = 'in_duel'
            else:
                print('Invalid input. Enter another number.')
        except ValueError:
            print('Invalid input. Enter another number.')

    # Choose defense deck
    defense_valid_choice = False
    while not defense_valid_choice:
        print()
        print('You have chosen, as your deck, deck #', offense_deck_index, ': ', offense_deck)
        print("The delegates of your opponent's unopened decks are: ")
        for i, deck in enumerate(defense.decks):
            if deck.state == 'unopened':
                print('\tDeck {}: {}'.format(i + 1, deck.delegate()))
        defense_deck_index = input("Choose one of your opponent's deck (Enter the deck number): ")
        try:
            index = int(defense_deck_index) - 1
            defense_deck = defense.decks[index]
            if index >= 0 and defense_deck.state == 'unopened':
                defense_valid_choice = True
                defense_deck.state = 'in_duel'
            else:
                print('Invalid input. Enter another number.')
        except ValueError:
            print('Invalid input. Enter another number.')
    print("You have chosen, as your opponent's deck, deck #", defense_deck_index, ': ', defense_deck)
    print()
    print('The two decks have been chosen!')
    print("{}'s deck #{} vs. {}'s deck #{}!".format(offense.name, offense_deck_index, defense.name, defense_deck_index))
    print("{}'s deck #{}: {}".format(offense.name, offense_deck_index, offense_deck))
    print("{}'s deck #{}: {}".format(defense.name, defense_deck_index, defense_deck))
    print()
    print("The second cards will be opened in three seconds!")
    time.sleep(3)
    offense.open_card(offense_deck.cards[1])
    defense.open_card(defense_deck.cards[1])
    print('Now the decks look like this:')
    print("{}'s deck #{}: {}".format(offense.name, offense_deck_index, offense_deck))
    print("{}'s deck #{}: {}".format(defense.name, defense_deck_index, defense_deck))
    print()
    print('What will you two do?')
    # TODO: decide how to implement two users' input
    # case 1: time limit("Your have n seconds to shout die, done, or draw.")
    # -> identify the first valid action for either within the time frame
    # -> check if the event actually happened
    # case 2: catch keyboard input real-time
    # -> identify the first valid action for each player
    # -> halt if they 1) both dare, 2) one of them die/done/draw
    # case 3: wait until they both input values and reveal what they did and compare index
    game_over = True

# TODO: print ending statements
