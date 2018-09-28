import abc
import random
import time


class AI(abc.ABC):
    # 나중에 AI vs AI 해서 전략간 상성이나 최고의 전략을 알아내기 위함
    @staticmethod
    @abc.abstractmethod
    def decide_joker_value(self, deck):
        """determine the value of joker
        :param deck: a deck with a joker
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def decide_delegate(self, deck):
        """determine the delegate, the card with the largest value in the deck
        :param deck: the deck in which a delegate has to be chosen
        :return: the same deck but with the delegate in the first of the cards
        """
        return deck

    @staticmethod
    @abc.abstractmethod
    def decide_deck_order(self, decks):
        """determine the order of decks when more than two or more delegates--including a joker--has the same value
        :param decks: a list of decks to sort
        :return: the same list of decks, sorted in ascending order"""
        return decks

    @classmethod
    @abc.abstractmethod
    def decide_die_or_not(cls, my_decks, opponent_decks):
        """determine whether you will shout die, considering the odds
        :return: a boolean value indicating whether to die"""
        pass

    @staticmethod
    @abc.abstractmethod
    def decide_shout_draw_timing(self, my_deck, opponent_deck):
        """determine when to shout Draw!"""
        pass


class BasicAI(AI):
    @staticmethod
    def decide_joker_value(deck):
        return 13

    @staticmethod
    def decide_delegate(deck):
        # TODO: test this
        random.shuffle(deck.cards)
        print(deck)
        first = deck.cards[0]
        biggest = sorted(deck.cards, key=lambda x: x.value)[-1]
        first, biggest = biggest, first
        print(deck)
        return deck

    @staticmethod
    def decide_deck_order(decks):
        decks.sort(key=lambda x: x.delegate().value)
        return decks

    @classmethod
    def decide_die_or_not(cls, my_decks, opponent_decks):
        odds_lose = cls.get_chances(my_decks, opponent_decks)[2]
        return odds_lose > .5

    @staticmethod
    def decide_shout_draw_timing(my_deck, opponent_deck):
        # TODO: shout을 감지하는 걸 어떻게 구현할지 결정하기 전까지 일단 안 외침
        pass

    @staticmethod
    def get_chances(me, opponent):
        """get chances of winning, tying, losing, and unknown.
        :return: a 4-tuple containing the chances of winning, tying, losing, and unknown
        """
        # get the value of my delegate and the opponent's
        my_delegate_value = me.deck_in_duel.delegate().value
        opponent_delegate_value = opponent.deck_in_duel.delegate().value
        # get a list of my hidden cards with value no bigger than that of the delegate
        my_hidden_cards = []
        for deck in me.decks:
            for card in deck.cards:
                if not card.is_open and card.value <= my_delegate_value:
                    my_hidden_cards.append(card)
        # get a list hidden cards with value no bigger than that of the delegate
        opponent_hidden_cards = []
        for deck in opponent.decks:
            for card in deck.cards:
                if not card.is_open and card.value <= opponent_delegate_value:
                    opponent_hidden_cards.append(card)
        # calculate the odds that you will lose the duel
        win, lose, draw, unknown = 0, 0, 0, 0
        for my_card in my_hidden_cards:
            for opponent_card in opponent_hidden_cards:
                # joker may still be hidden
                if my_card.value is None or opponent_card.value is None:
                    unknown += 1
                elif my_card.value > opponent_card.value:
                    win += 1
                elif my_card.value == opponent_card.value:
                    draw += 1
                elif my_card.value < opponent_card.value:
                    lose += 1
                else:
                    raise Exception('Something is wrong.')
        total = len(my_hidden_cards) * len(opponent_hidden_cards)
        odds_win = win / total
        odds_draw = draw / total
        odds_lose = lose / total
        odds_unknown = unknown / total
        return odds_win, odds_draw, odds_lose, odds_unknown


class Game(object):
    def __init__(self, player_red, player_black):
        self.player_red = player_red  # takes the red pile and gets to go first
        self.player_black = player_black
        self.over = False
        self.ended_reason = None
        self.time_created = time.time()
        self.time_ended = None
        self.winner = None
        self.loser = None

    def end(self, ended_reason, winner=None, loser=None):
        self.over = True
        self.ended_reason = ended_reason
        self.time_ended = time.time()
        self.winner = winner
        self.loser = loser
        if winner is None and loser is None:
            raise ValueError('At least one of winner or loser must be supplied.')
        elif winner is None:
            self.winner = self.player_red if loser == self.player_black else self.player_black
        elif loser is None:
            self.loser = self.player_red if loser == self.player_black else self.player_black

    def players(self):
        return [self.player_red, self.player_black]

    def shout_done(self, player_shouted):
        values = []
        for deck in player_shouted.decks:
            for card in deck:
                if card.value not in values:
                    values.append(card.value)
        if len(values) == 13:
            self.end('done', winner=player_shouted)
        else:
            player_shouted.num_shout_done += 1
            if player_shouted.num_shout_done > 1:
                self.end('forfeit_done', loser=player_shouted)

    def shout_draw(self, player_shouted, duel):
        player_red_deck_sum = sum([card.value for card in duel.player_red.deck])
        player_black_deck_sum = sum([card.value for card in duel.player_black.deck])
        if player_red_deck_sum == player_black_deck_sum:
            duel.end('draw', winner=player_shouted)
        else:
            player_shouted.num_shout_draw += 1
            if player_shouted.num_shout_draw > 1:
                self.end('forfeit_draw', loser=player_shouted)


class Player(object):
    def __init__(self, name, decks=None):
        self.name = name
        self.num_death = 0
        self.num_victory = 0
        self.done = False
        self.num_shout_done = 0
        self.num_shout_draw = 0
        self.decks = decks
        self.deck_in_duel = None


class Card(object):
    def __init__(self, suit, colored, rank, value=None):
        self.suit = suit
        self.colored = colored
        self.rank = rank
        self.value = value
        self.is_open = False

    def __repr__(self):
        if self.is_open:
            if self.suit is None:
                return 'Colored Joker' if self.colored else 'Black Joker'
            else:
                return '{} of {}'.format(self.rank, self.suit)
        else:
            return 'Hidden'

    def open_up(self):
        self.is_open = True


class Deck(object):
    def __init__(self, cards):
        self.state = 'unopened'
        self.cards = cards

    def __repr__(self):
        return ' / '.join([repr(card) for card in self.cards])

    
    def delegate(self):
        return self.cards[0]

class Duel(object):
    def __init__(self, player_red, player_black, winner=None, loser=None):
        self.player_red = player_red
        self.player_black = player_black
        self.state = 'unopened'
        self.time_created = time.time()
        self.time_ended = None
        self.winner = winner
        self.loser = loser

    def end(self, state, winner=None, loser=None):
        self.state = state
        self.time_ended = time.time()
        self.winner = winner
        self.loser = loser
        if winner is None and loser is None:
            raise ValueError('At least one of winner or loser must be supplied.')
        elif winner is None:
            self.winner = self.player_red if loser == self.player_black else self.player_black
        elif loser is None:
            self.loser = self.player_red if loser == self.player_black else self.player_black


def main():
    # Setup
    BLACK_SUITS = ['Spades', 'Clubs']
    RED_SUITS = ['Hearts', 'Diamonds']
    # TODO: 일단 13으로 고정
    red_joker = Card(None, True, 'Joker', 13)
    black_joker = Card(None, False, 'Joker', 13)
    RANKS = ['Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King']
    red_pile = [red_joker] + [Card(suit, True, rank, RANKS.index(rank) + 1) for suit in RED_SUITS for rank in RANKS]
    black_pile = [black_joker] + [Card(suit, False, rank, RANKS.index(rank) + 1) for suit in BLACK_SUITS for rank in RANKS]
    piles = [red_pile, black_pile]
    DECK_PER_PILE = 9
    CARD_PER_DECK = 3

    print("Let's start DieOrDare!")

    # Initialize players with name validation
    player1_name = ''
    while not player1_name.isalnum():
        player1_name = input("Enter player 1's name: ")
    player1 = Player(player1_name)
    player2_name = ''
    while not player2_name.isalnum() or player1_name == player2_name:
        player2_name = input("Enter player 2's name: ")
    player2 = Player(player2_name)
    print("\nAll right, {} and {}. Let's get started!".format(player1_name, player2_name))

    # Decide which buttons to use for player 1
    print("\n{}(Player 1), let's decide which buttons to use.".format(player1_name))
    player1_characters_settings = {'dare': '', 'die': '', 'done': '', 'draw': ''}
    for action in player1_characters_settings:
        character = player1_characters_settings.get(action)
        while not character.isalnum() or character in player1_characters_settings.values():
            character = input('Which character will you use to indicate {}? '.format(action))
        player1_characters_settings[action] = character

    # Decide which buttons to use for player 2
    print("\n{}(Player 2), let's decide which buttons to use.".format(player2_name))
    player2_characters_settings = {'dare': '', 'die': '', 'done': '', 'draw': ''}
    for action in player2_characters_settings:
        character = player2_characters_settings.get(action)
        used_characters = list(player1_characters_settings.values()) + list(player2_characters_settings.values())
        while not character.isalnum() or character in used_characters:
            character = input('Which character will you use to indicate {}? '.format(action))
        player2_characters_settings[action] = character

    # Start the game by tossing a coin to decide who will be the player_red (takes the red pile & goes first)
    if random.random() > .5:
        game = Game(player1, player2)
    else:
        game = Game(player2, player1)

    # Draw cards to form 9 decks for each player and sort them based on the delegate's value
    for i in range(2):
        # red first
        player = game.players()[i]
        pile = piles[i]
        random.shuffle(pile)
        decks = []
        for j in range(DECK_PER_PILE):
            cards = []
            for k in range(CARD_PER_DECK):
                cards.append(pile.pop())
            cards.sort(key=lambda x: -x.value)
            new_deck = Deck(cards)
            new_deck.delegate().open_up()
            decks.append(new_deck)
        decks.sort(key=lambda x: x.delegate().value)
        player.decks = decks

    # The Duels start
    duel_index = 0
    while not game.over:
        duel_index += 1
        if duel_index % 2 == 1:
            offense = game.player_red
            defense = game.player_black
        else:
            offense = game.player_black
            defense = game.player_red
        print('\nStarting Duel {}...'.format(duel_index))
        print('\n{}, your turn!'.format(offense.name))

        # Choose offense deck
        offense_valid_choice = False
        while not offense_valid_choice:
            print('\nThe delegates of your unopened decks are: ')
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
                    offense.deck_in_duel = offense_deck
                else:
                    print('Invalid input. Enter another number.')
            except ValueError:
                print('Invalid input. Enter another number.')

        # Choose defense deck
        defense_valid_choice = False
        while not defense_valid_choice:
            print('\nYou have chosen, as your deck, deck #', offense_deck_index, ': ', offense_deck)
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
                    defense.deck_in_duel = defense_deck
                else:
                    print('Invalid input. Enter another number.')
            except ValueError:
                print('Invalid input. Enter another number.')
        print("You have chosen, as your opponent's deck, deck #", defense_deck_index, ': ', defense_deck)
        print('\nThe two decks have been chosen!')
        print("{}'s deck #{} vs. {}'s deck #{}!".format(offense.name, offense_deck_index, defense.name,
                                                        defense_deck_index))
        print("{}'s deck #{}: {}".format(offense.name, offense_deck_index, offense_deck))
        print("{}'s deck #{}: {}".format(defense.name, defense_deck_index, defense_deck))
        print("\nThe second cards will be opened in three seconds!")
        time.sleep(3)
        offense_deck.cards[1].open_up()
        defense_deck.cards[1].open_up()
        print('Now the decks look like this:')
        print("{}'s deck #{}: {}".format(offense.name, offense_deck_index, offense_deck))
        print("{}'s deck #{}: {}".format(defense.name, defense_deck_index, defense_deck))
        print('\nWhat will you two do?')
        # TODO: decide how to implement two users' input
        # until then,
        break
        # case 1: time limit("Your have n seconds to shout die, done, or draw.")
        # -> identify the first valid action for either within the time frame
        # -> check if the event actually happened
        # case 2: catch keyboard input real-time
        # -> identify the first valid action for each player
        # -> halt if they 1) both dare, 2) one of them die/done/draw
        # case 3: wait until they both input values and reveal what they did and compare index
    # TODO: print ending statements
    print('Game!')


if __name__ == '__main__':
    main()
