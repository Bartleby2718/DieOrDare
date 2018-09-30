import abc
import constants
import keyboard
import random
import time


class AI(abc.ABC):
    @abc.abstractmethod
    def decide_joker_value(self, deck):
        """determine the value of joker
        :param deck: a deck with a joker
        """
        pass

    @abc.abstractmethod
    def decide_and_open_delegate(self, deck):
        """determine the delegate, the card with the largest value in the deck, and open it
        :param deck: the deck in which a delegate has to be chosen
        :return: the same deck but with the delegate in the first of the cards
        """
        return deck

    @classmethod
    @abc.abstractmethod
    def decide_action(cls, my_decks, opponent_decks):
        """determine which action you will take, considering the odds
        :return: a boolean value indicating whether to die"""
        pass

    @abc.abstractmethod
    def decide_deck_in_duel(self, my_decks, opponent_decks):
        """determine which deck to put in a duel
        :return: a 2-tuple of my deck and opponent's deck"""
        pass


class BasicAI(AI):
    def decide_joker_value(self, deck):
        return constants.HIGHEST_VALUE

    def decide_and_open_delegate(self, deck):
        cards = deck.cards
        random.shuffle(cards)
        biggest_card = max(cards, key=lambda x: x.value)
        biggest_card.open_up()
        biggest_card_index = cards.index(biggest_card)  # zero-based
        cards[0], cards[biggest_card_index] = cards[biggest_card_index], cards[0]
        deck.cards = tuple(cards)
        return deck

    @classmethod
    def decide_action(cls, my_decks, opponent_decks):
        odds_lose = cls.get_chances(my_decks, opponent_decks)[2]
        return odds_lose > .5

    @abc.abstractmethod
    def decide_deck_in_duel(self, my_decks, opponent_decks):
        """determine which deck to put in a duel"""
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
        self.time_created = time.time()
        self.time_ended = None
        self.winner = None
        self.loser = None
        self.result = None
        self.duel_ongoing = None

    def end(self, result, winner=None, loser=None):
        self.over = True
        self.result = result
        self.time_ended = time.time()
        self.winner = winner
        self.loser = loser
        if winner is None and loser is None:
            raise ValueError('At least one of winner or loser must be supplied.')
        elif winner is None:
            self.winner = self.player_red if loser == self.player_black else self.player_black
        elif loser is None:
            self.loser = self.player_red if winner == self.player_black else self.player_black
        self.duel_ongoing = None
        for player in self.players():
            player.deck_in_duel = None

    def players(self):
        return self.player_red, self.player_black

    def process_action(self, player_shouted, action):
        if action == constants.Action.DIE:
            self.shout_die(player_shouted)
        elif action == constants.Action.DONE:
            self.shout_done(player_shouted)
        elif action == constants.Action.DRAW:
            self.shout_draw(player_shouted)
        else:
            self.double_dare()

    def double_dare(self):
        sum_red = sum([card.value for card in self.player_red.deck_in_duel.cards])
        sum_black = sum([card.value for card in self.player_black.deck_in_duel.cards])
        if sum_red > sum_black:
            self.duel_ongoing.end(constants.DuelResult.FINISHED, winner=self.player_red)
        elif sum_red < sum_black:
            self.duel_ongoing.end(constants.DuelResult.FINISHED, winner=self.player_black)
        else:
            self.duel_ongoing.end(constants.DuelResult.DRAWN)

    def shout_die(self, player_shouted):
        player_shouted.num_shout_die += 1
        self.duel_ongoing.end(constants.DuelResult.DIED, loser=player_shouted)

    def shout_done(self, player_shouted):
        player_shouted.num_shout_done += 1
        values = set([card.value for deck in player_shouted.decks for card in deck])
        if len(values) == len(constants.RANKS):
            self.duel_ongoing.end(constants.DuelResult.ABORTED_BY_DONE, winner=player_shouted)
            self.end(constants.GameResult.DONE, winner=player_shouted)
        else:
            player_shouted.num_shout_done += 1
            if player_shouted.num_shout_done > 1:
                self.duel_ongoing.end(constants.DuelResult.ABORTED_BY_FORFEIT, loser=player_shouted)
                self.end(constants.GameResult.FORFEITED_BY_WRONG_DONE, loser=player_shouted)

    def shout_draw(self, player_shouted):
        player_shouted.num_shout_draw += 1
        player_red_deck_sum = sum([card.value for card in self.player_red.deck])
        player_black_deck_sum = sum([card.value for card in self.player_black.deck])
        if player_red_deck_sum == player_black_deck_sum:
            self.duel_ongoing.end(constants.DuelResult.DRAWN, winner=player_shouted)
        else:
            player_shouted.num_shout_draw += 1
            if player_shouted.num_shout_draw > 1:
                self.duel_ongoing.end(constants.DuelResult.ABORTED_BY_FORFEIT, lose=player_shouted)
                self.end(constants.GameResult.FORFEITED_BY_WRONG_DRAW, loser=player_shouted)


class Player(object):
    def __init__(self, name):
        self.name = name
        self.num_victory = 0
        self.num_shout_die = 0
        self.num_shout_done = 0
        self.num_shout_draw = 0
        self.decks = None
        self.deck_in_duel = None
        self.pile = None
        self.key_settings = None

    def print_statistics(self):
        statistics = {
            'Number of duels {} won'.format(self.name):
                str(self.num_victory) + ' ({} more to go!)'.format(constants.REQUIRED_WIN - self.num_victory),
            'Number of times {} shouted die'.format(self.name):
                str(self.num_shout_die) + ' ({} more available)'.format(constants.MAX_DIE - self.num_shout_die),
            'Number of times {} shouted done'.format(self.name):
                str(self.num_shout_draw) + ' ({} more available)'.format(constants.MAX_DONE - self.num_shout_done),
            'Number of times {} shouted draw'.format(self.name):
                str(self.num_shout_draw) + ' ({} more available)'.format(constants.MAX_DRAW - self.num_shout_draw),
        }
        print(statistics)


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
        self.state = constants.DeckState.UNOPENED
        self.cards = cards
        self.index = None  # one-based

    def __repr__(self):
        return ' / '.join([repr(card) for card in self.cards])

    def delegate(self):
        return self.cards[0]


class Duel(object):
    def __init__(self, offense, defense, index=1):
        self.offense = offense
        self.defense = defense
        self.time_created = time.time()
        self.index = index  # one-based
        self.over = False
        self.time_ended = None
        self.winner = None
        self.loser = None
        self.result = None
        self.has_updated_score = False
        self.has_chosen_delegate = False

    def end(self, result, winner=None, loser=None):
        self.over = True
        self.time_ended = time.time()
        self.result = result
        self.winner = winner
        self.loser = loser
        if winner is None and loser is None:
            if result == constants.DuelResult.FINISHED:
                raise ValueError('At least one of winner or loser must be supplied.')
        else:
            if winner is None:
                self.winner = self.defense if loser == self.offense else self.offense
            if loser is None:
                self.loser = self.offense if winner == self.offense else self.defense
            self.winner.num_victory += 1


def main():
    def red_shout_die(key):
        keyboard.unhook_all()
        print('Player Red shouted Die!')
        whether_red_took_actions[constants.Action.DIE] = True

    def red_shout_done(key):
        keyboard.unhook_all()
        print('Player Red shouted Done!')
        whether_red_took_actions[constants.Action.DONE] = True

    def red_shout_draw(key):
        keyboard.unhook_all()
        print('Player Red shouted Draw!')
        whether_red_took_actions[constants.Action.DRAW] = True

    def black_shout_die(key):
        keyboard.unhook_all()
        print('Player black shouted Die!')
        whether_black_took_actions[constants.Action.DIE] = True

    def black_shout_done(key):
        keyboard.unhook_all()
        print('Player black shouted Done!')
        whether_black_took_actions[constants.Action.DONE] = True

    def black_shout_draw(key):
        keyboard.unhook_all()
        print('Player black shouted Draw!')
        whether_black_took_actions[constants.Action.DRAW] = True

    # Setup
    red_joker = Card(None, True, 'Joker', constants.HIGHEST_VALUE)
    black_joker = Card(None, False, 'Joker', constants.HIGHEST_VALUE)

    ranks = constants.RANKS
    red_pile = [red_joker] + [Card(suit, True, rank, ranks.index(rank) + 1) for suit in constants.RED_SUITS for rank in ranks]
    black_pile = [black_joker] + [Card(suit, False, rank, ranks.index(rank) + 1) for suit in constants.BLACK_SUITS for rank in ranks]

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

    # Start the game by tossing a coin to decide who will be the player_red (takes the red pile & goes first)
    if random.random() > .5:
        game = Game(player1, player2)
        player1.pile = red_pile
        player2.pile = black_pile
    else:
        game = Game(player2, player1)
        player2.pile = red_pile
        player1.pile = black_pile

    # Decide which characters to use for both players
    for player in game.players():
        print('\n{}, decide the set of characters you will use.'.format(player.name))
        player.key_settings = {constants.Action.DARE: '', constants.Action.DIE: '', constants.Action.DONE: '',
                               constants.Action.DRAW: ''}
        for action in player.key_settings:
            character = player.key_settings.get(action)
            while not character.isalpha() or character in player.key_settings.values():
                character = input('Which character will you use to indicate {}? '.format(action))
            player.key_settings[action] = character

    # Draw cards to form 9 decks for each player and sort them based on the delegate's value
    for player in game.players():
        pile = player.pile
        random.shuffle(pile)
        decks = []
        for j in range(constants.DECK_PER_PILE):
            cards = []
            for k in range(constants.CARD_PER_DECK):
                cards.append(pile.pop())
            cards.sort(key=lambda x: -x.value)
            new_deck = Deck(cards)
            new_deck.delegate().open_up()
            decks.append(new_deck)
        decks.sort(key=lambda x: x.delegate().value)
        for deck in decks:
            deck.index = decks.index(deck) + 1
        player.decks = tuple(decks)

    # Start playing
    duel_index = 0
    while not game.over:
        duel_index += 1
        # Decide offense and defense
        if duel_index % 2 == 1:
            offense = game.player_red
            defense = game.player_black
        else:
            offense = game.player_black
            defense = game.player_red

        # Duel starts
        duel = Duel(offense, defense, duel_index)
        game.duel_ongoing = duel
        print('\n\n\nStarting Duel {}...'.format(duel.index))
        print('\n{}, your turn!'.format(offense.name))
        time.sleep(1)

        # Skip choosing deck in the last duel
        is_last_duel = duel.index == 9
        if is_last_duel:
            offense_deck = [deck for deck in game.player_red.decks if deck.state == constants.DeckState.UNOPENED][0]
            offense_valid_input = True
            offense_deck.state = constants.DeckState.IN_DUEL
            offense.deck_in_duel = offense_deck
            defense_deck = [deck for deck in game.player_black.decks if deck.state == constants.DeckState.UNOPENED][0]
            defense_valid_input = True
            defense_deck.state = constants.DeckState.IN_DUEL
            defense.deck_in_duel = defense_deck
        else:
            offense_valid_input = False
            defense_valid_input = False
            print('\nThe delegates of your unopened decks are: ')
            for deck in offense.decks:
                if deck.state == constants.DeckState.UNOPENED:
                    print('\tDeck {}: {}'.format(deck.index, deck.delegate()))
            print("The delegates of your opponent's unopened decks are: ")
            for deck in defense.decks:
                if deck.state == constants.DeckState.UNOPENED:
                    print('\tDeck {}: {}'.format(deck.index, deck.delegate()))

        # Choose offense deck
        while not offense_valid_input:
            offense_deck_input = input('Choose one of your deck (Enter the deck number): ')
            try:
                offense_deck = offense.decks[int(offense_deck_input) - 1]
            except (ValueError, IndexError):
                print('Invalid input. Enter another number.')
            else:
                offense_valid_input = True
                offense_deck.state = constants.DeckState.IN_DUEL
                offense.deck_in_duel = offense_deck

        # Choose defense deck
        while not defense_valid_input:
            defense_deck_input = input("Choose one of your opponent's deck (Enter the deck number): ")
            try:
                defense_deck = defense.decks[int(defense_deck_input) - 1]
            except (ValueError, IndexError):
                print('Invalid input. Enter another number.')
            else:
                defense_valid_input = True
                defense_deck.state = constants.DeckState.IN_DUEL
                defense.deck_in_duel = defense_deck

        # display the decks chosen
        print('\nThe two decks have been chosen!')
        for player in game.players():
            print("{}'s deck #{}: {}".format(player.name, player.deck_in_duel.index, player.deck_in_duel))

        # open the second cards
        print("\nThe second cards will be opened in 3 seconds!")
        time.sleep(3)
        for player in game.players():
            player.deck_in_duel.cards[1].open_up()
            print("{}'s deck #{}: {}".format(player.name, player.deck_in_duel.index, player.deck_in_duel))

        # reset the players' actions before getting input
        whether_red_took_actions = {constants.Action.DARE: False, constants.Action.DIE: False,
                                    constants.Action.DONE: False, constants.Action.DRAW: False, }
        whether_black_took_actions = {constants.Action.DARE: False, constants.Action.DIE: False,
                                      constants.Action.DONE: False, constants.Action.DRAW: False, }

        # hook keys
        if game.player_red.num_shout_die < constants.MAX_DIE:
            keyboard.on_press_key(game.player_red.key_settings[constants.Action.DIE], red_shout_die)
        if game.player_red.num_shout_done < constants.MAX_DONE:
            keyboard.on_press_key(game.player_red.key_settings[constants.Action.DONE], red_shout_done)
        if game.player_black.num_shout_die < constants.MAX_DIE:
            keyboard.on_press_key(game.player_black.key_settings[constants.Action.DIE], black_shout_die)
        if game.player_black.num_shout_done < constants.MAX_DONE:
            keyboard.on_press_key(game.player_black.key_settings[constants.Action.DONE], black_shout_done)

        # start timing and wait for key press
        print('\nWhat will you two do?')
        start = time.time()
        while not (any(whether_red_took_actions.values()) or any(
                whether_black_took_actions.values()) or time.time() - start > constants.TIME_LIMIT_FOR_ACTION):
            pass

        # find out what happened and update the score accordingly
        has_found_action = False
        for action, has_happened in whether_red_took_actions.items():
            if not has_found_action and has_happened:
                game.process_action(game.player_red, action)
                has_found_action = True
        for action, has_happened in whether_black_took_actions.items():
            if not has_found_action and has_happened:
                game.process_action(game.player_black, action)
                has_found_action = True
        if not has_found_action:
            print('Ooh, double dare!')
            game.process_action(None, constants.Action.DARE)

        if not game.duel_ongoing.over:
            # reset the players' actions
            whether_red_took_actions = {constants.Action.DARE: False, constants.Action.DIE: False,
                                        constants.Action.DONE: False, constants.Action.DRAW: False, }
            whether_black_took_actions = {constants.Action.DARE: False, constants.Action.DIE: False,
                                          constants.Action.DONE: False, constants.Action.DRAW: False, }

            # hook keys
            if game.player_red.num_shout_done < constants.MAX_DONE:
                keyboard.on_press_key(game.player_red.key_settings[constants.Action.DONE], red_shout_done)
            if game.player_red.num_shout_draw < constants.MAX_DRAW:
                keyboard.on_press_key(game.player_red.key_settings[constants.Action.DRAW], red_shout_draw)
            if game.player_black.num_shout_done < constants.MAX_DONE:
                keyboard.on_press_key(game.player_black.key_settings[constants.Action.DONE], black_shout_done)
            if game.player_black.num_shout_draw < constants.MAX_DRAW:
                keyboard.on_press_key(game.player_black.key_settings[constants.Action.DRAW], black_shout_draw)

            # start timing and wait for key press
            print('\nWhat will you two do?')
            start = time.time()
            while not (any(whether_red_took_actions.values()) or any(
                    whether_black_took_actions.values()) or time.time() - start > constants.TIME_LIMIT_FOR_ACTION):
                pass

            # find out what happened and update the score accordingly
            has_found_action = False
            for action, has_happened in whether_red_took_actions.items():
                if not has_found_action and has_happened:
                    game.process_action(game.player_red, action)
                    has_found_action = True
            for action, has_happened in whether_black_took_actions.items():
                if not has_found_action and has_happened:
                    game.process_action(game.player_black, action)
                    has_found_action = True
            if not has_found_action:
                game.process_action(None, constants.Action.DARE)

        # open the last cards and output the current score
        for player in game.players():
            player.deck_in_duel.cards[-1].open_up()
            print("\n{}'s deck #{}: {}".format(player.name, player.deck_in_duel.index, player.deck_in_duel))
            player.print_statistics()
            player.deck_in_duel.state = constants.DeckState.FINISHED

    print('Game!')
    print(game.__dict__)


if __name__ == '__main__':
    main()
