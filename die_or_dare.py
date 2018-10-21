import abc
import constants
import itertools
import jsonpickle
import keyboard
import random
import sys
import time


class Game(object):
    def __init__(self, *args, player_red=None, player_black=None, over=False, time_created=None, time_ended=None, winner=None, loser=None, result=None, duel_index=0, duel_ongoing=None, red_pile=None, black_pile=None):
        self.player_red = player_red  # takes the red pile and gets to go first
        self.player_black = player_black
        self.over = over
        self.time_created = time_created or time.time()
        self.time_ended = time_ended
        self.winner = winner
        self.loser = loser
        self.result = result
        self.duel_index = duel_index  # one-based
        self.duel_ongoing = duel_ongoing
        red_joker = Card(None, True, constants.JOKER, None)
        black_joker = Card(None, False, constants.JOKER, None)
        ranks = constants.RANKS
        red_suits = constants.RED_SUITS
        black_suits = constants.BLACK_SUITS
        self.red_pile = red_pile or ([red_joker] + [Card(suit, True, rank, ranks.index(rank) + 1) for suit in red_suits for rank in ranks])
        self.black_pile = black_pile or ([black_joker] + [Card(suit, False, rank, ranks.index(rank) + 1) for suit in black_suits for rank in ranks])
        num_computers = len(args)
        if num_computers in range(3):
            self.num_human_players = 2 - num_computers
        else:
            raise ValueError('Invalid number of computer players')
        print("Let's start DieOrDare!")

    def players(self):
        return self.player_red, self.player_black
    
    def initialize_players(self):
        if self.num_human_players == 0:
            class1_name = sys.argv[1]
            class1 = globals().get(class1_name)
            if type(class1) in ['NoneType', 'ComputerPlayer'] or not issubclass(class1, ComputerPlayer):
                raise ValueError('Invalid class name for computer player')
            player1 = class1()
            class2_name = sys.argv[2]
            class2 = globals().get(class2_name)
            if type(class2) in ['NoneType', 'ComputerPlayer'] or not issubclass(class2, ComputerPlayer):
                raise ValueError('Invalid class name for computer player')
            forbidden_name = player1.name
            player2 = class2(forbidden_name)
        elif self.num_human_players == 1:
            class1_name = sys.argv[1]
            class1 = globals().get(class1_name)
            if type(class1) in ['NoneType', 'ComputerPlayer'] or not issubclass(class1, ComputerPlayer):
                raise ValueError('Invalid class name for computer player')
            player1 = class1()
            human_player1_prompt = "Enter your name: "
            forbidden_name = player1.name
            player2 = HumanPlayer.from_input(human_player1_prompt, forbidden_name)
        else:
            human_player1_prompt = "Enter player 1's name: "
            player1 = HumanPlayer.from_input(human_player1_prompt)
            human_player2_prompt = "Enter player 2's name: "
            forbidden_name = player1.name
            player2 = HumanPlayer.from_input(human_player2_prompt, forbidden_name)
        print("\nAll right, {} and {}. Let's get started!".format(player1.name, player2.name))
        print("Let's flip a coin to decide who will be the Player Red!")
        if random.random() > .5:
            self.player_red = player1
            self.player_black = player2
        else:
            self.player_red = player2
            self.player_black = player1
        self.player_red.pile = game.red_pile
        self.player_red.alias = constants.PLAYER_RED
        self.player_black.pile = game.black_pile
        self.player_black.alias = constants.PLAYER_BLACK
        time.sleep(1)
        print('{}, you are the Player Red, so you will go first.'.format(self.player_red.name))
        print('{}, you are the Player Black.'.format(self.player_black.name))

    def initialize_decks(self):
        for player in self.players():
            player.initialize_decks()

    def set_keys(self):
        self.player_red.set_keys()
        player_red_keys = list(self.player_red.key_settings.values())
        self.player_black.set_keys(blacklist=player_red_keys)

    def start_duel(self):
        self.duel_index += 1
        self.duel_ongoing = Duel(self.player_red, self.player_black, self.duel_index)
        self.duel_ongoing.decide_offense()
        print('\n\n\nStarting Duel {}...'.format(self.duel_index))
        print('\n{}, your turn!'.format(self.duel_ongoing.offense.name))
        time.sleep(constants.DELAY_AFTER_TURN_NOTICE)
        return self.duel_ongoing

    def cleanup_duel(self):
        # identify why the duel ended
        if self.duel_ongoing.result in [constants.DuelResult.DRAWN, constants.DuelResult.FINISHED]:
            for player in self.players():
                if player.num_victory == constants.REQUIRED_WIN:
                    self.end(constants.GameResult.FINISHED, winner=player)
                    print("{0} wins! The game has ended as {0} first scored {1} points".format(player.name,
                                                                                               constants.REQUIRED_WIN))
                    break
        elif self.duel_ongoing.result == constants.DuelResult.ABORTED_BY_CORRECT_DONE:
            self.end(constants.GameResult.DONE, winner=self.duel_ongoing.player_shouted)
            print("{0} wins! The game has ended as {0} first shouted done correctly.".format(self.winner.name))
        elif self.duel_ongoing.result == constants.DuelResult.ABORTED_BY_WRONG_DONE:
            self.end(constants.GameResult.FORFEITED_BY_WRONG_DONE, loser=self.duel_ongoing.player_shouted)
            print("{} wins! The game has ended as {} shouted done wrong.".format(self.winner.name, self.loser.name))
        elif self.duel_ongoing.result == constants.DuelResult.ABORTED_BY_WRONG_DRAW:
            self.end(constants.GameResult.FORFEITED_BY_WRONG_DRAW, loser=self.duel_ongoing.player_shouted)
            print("{} wins! The game has ended as {} shouted draw wrong.".format(self.winner.name, self.loser.name))
        elif self.duel_ongoing.result == constants.DuelResult.ABORTED_BEFORE_DOUBLE_DONE:
            self.end(constants.GameResult.FORFEITED_BEFORE_DOUBLE_DONE, loser=self.player_red)
            print("{} wins! The game has ended as the Player Red failed to finish the game before the final double done.".format(self.winner.name))

        # cleanup
        for player in self.players():
            player.deck_in_duel.state = constants.DeckState.FINISHED
            player.deck_in_duel = None
        self.duel_ongoing = None
        time.sleep(constants.DELAY_AFTER_DUEL_ENDS)

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


class Player(object):
    def __init__(self, name='', num_victory=0, num_shout_die=0, num_shout_done=0, num_shout_draw=0, decks=None, deck_in_duel=None, pile=None, key_settings=None, alias=None):
        self.name = name
        self.num_victory = num_victory
        self.num_shout_die = num_shout_die
        self.num_shout_done = num_shout_done
        self.num_shout_draw = num_shout_draw
        self.decks = decks
        self.deck_in_duel = deck_in_duel
        self.pile = pile
        self.key_settings = key_settings or {action: '' for action in constants.Action}
        self.alias = alias

    def initialize_decks(self):
        random.shuffle(self.pile)
        decks = []
        for j in range(constants.DECK_PER_PILE):
            cards = []
            for k in range(constants.CARD_PER_DECK):
                cards.append(self.pile.pop())
            cards = self.decide_delegate(cards)
            new_deck = Deck(cards)
            new_deck.delegate().open_up()
            decks.append(new_deck)
        decks.sort(key=lambda x: x.delegate().value)
        for deck in decks:
            deck.index = decks.index(deck) + 1
        self.decks = tuple(decks)

    @abc.abstractmethod
    def set_keys(self, blacklist=None):
        pass

    @abc.abstractmethod
    def decide_delegate(self, cards):
        pass

    @abc.abstractmethod
    def decide_decks_for_duel(self, opponent_decks):
        pass

    def open_next_card(self):
        to_open_index = len([card for card in self.deck_in_duel.cards if card.is_open])
        self.deck_in_duel.cards[to_open_index].open_up()


class HumanPlayer(Player):
    @classmethod
    def from_input(cls, prompt, forbidden_name=''):
        name = input(prompt)
        while not name.isalnum() or name == forbidden_name:
            if name == forbidden_name:
                print("You can't use {}. Choose another name.".format(forbidden_name))
            else:
                print("Only alphanumeric characters are allowed for the player's name.")
            name = input(prompt)
        return cls(name)

    def set_keys(self, blacklist=None):
        blacklist = [] if blacklist is None else blacklist
        print('\n{}, decide the set of keys you will use.'.format(self.name))
        for action in self.key_settings:
            key = input('{}, which key will you use to indicate {}? '.format(self.name, action.name))
            is_valid_key = len(key) == 1 and key.islower() and key not in blacklist
            while not is_valid_key:
                if key in blacklist:
                    print("You can't use the following key(s): {}".format(', '.join(blacklist)))
                else:
                    print('Use a single lowercase alphabet.')
                key = input('{}, which key will you use to indicate {}? '.format(self.name, action.name))
                is_valid_key = len(key) == 1 and key.islower() and key not in blacklist
            self.key_settings[action] = key
            blacklist.append(key)

    def decide_delegate(self, cards):
        joker_found = False
        joker_index = -1
        for i in range(len(cards)):
            card = cards[i]
            if card.suit is None:
                joker_found = True
                joker_index = i
                break
        if joker_found:
            joker = cards[joker_index]
            cards_without_joker = list([card for card in cards if card != joker])
            biggest = max(cards_without_joker, key=lambda x: x.value)
            smallest = min(cards_without_joker, key=lambda x: x.value)
            joker.value = biggest.value
            return biggest, joker, smallest
        else:
            biggest = max(cards, key=lambda x: x.value)
            smallest = min(cards, key=lambda x: x.value)
            middle = [card for card in cards if card != biggest and card != smallest].pop()
            not_biggest = [middle, smallest]
            random.shuffle(not_biggest)
            return tuple([biggest] + not_biggest)

    def decide_decks_for_duel(self, opponent_decks):
        # Choose offense deck
        offense_deck_input = input('Choose one of your deck (Enter the deck number): ')
        offense_allowed_inputs = [deck.index for deck in self.decks if deck.state == constants.DeckState.UNOPENED]
        offense_valid_input = False
        while not offense_valid_input:
            try:
                if int(offense_deck_input) in offense_allowed_inputs:
                    offense_valid_input = True
                else:
                    raise ValueError
            except ValueError:
                print('Invalid input. Enter a number among {}.'.format(
                    ', '.join([str(index) for index in offense_allowed_inputs])))
                offense_deck_input = input('Choose one of your deck (Enter the deck number): ')
        offense_deck = self.decks[int(offense_deck_input) - 1]

        # Choose defense deck
        defense_deck_input = input("Choose one of your opponent's deck (Enter the deck number): ")
        defense_allowed_inputs = [deck.index for deck in opponent_decks if deck.state == constants.DeckState.UNOPENED]
        defense_valid_input = False
        while not defense_valid_input:
            try:
                if int(defense_deck_input) in defense_allowed_inputs:
                    defense_valid_input = True
                else:
                    raise ValueError
            except ValueError:
                print('Invalid input. Enter a number among {}.'.format(
                    ', '.join([str(index) for index in defense_allowed_inputs])))
                defense_deck_input = input("Choose one of your opponent's deck (Enter the deck number): ")
        defense_deck = opponent_decks[int(defense_deck_input) - 1]
        return offense_deck, defense_deck


class ComputerPlayer(Player):
    @classmethod
    def auto_generate(cls, forbidden_name=''):
        name = 'Computer{}'.format(random.randint(1, 999))
        if name == forbidden_name:
            name += 'a'
        return cls(name)

    def set_keys(self, blacklist=None):
        if self.alias == constants.PLAYER_RED:
            self.key_settings = {constants.Action.DARE: 'z', constants.Action.DIE: 'x',
                                 constants.Action.DONE: 'c', constants.Action.DRAW: 'v'}
        else:
            self.key_settings = {constants.Action.DARE: 'u', constants.Action.DIE: 'i',
                                 constants.Action.DONE: 'o', constants.Action.DRAW: 'p'}

    @abc.abstractmethod
    def decide_delegate(self, cards):
        pass

    @abc.abstractmethod
    def decide_decks_for_duel(self, opponent_decks):
        pass

    @staticmethod
    def unopened_values(decks):
        values = []
        for deck in decks:
            for card in deck.cards:
                if deck.state == constants.DeckState.UNOPENED or not card.is_open:
                    values.append(card.value)
        return tuple(set(values))

    @staticmethod
    def opened_values(decks):
        values = []
        for deck in decks:
            for card in deck.cards:
                if deck.state != constants.DeckState.UNOPENED and card.is_open:
                    values.append(card.value)
        return tuple(set(values))


class DumbComputerPlayer(ComputerPlayer):
    def decide_delegate(self, cards):
        cards.sort(key=lambda x: -x.value)
        joker_found = False
        joker_index = 0
        for i in range(len(cards)):
            card = cards[i]
            if card.suit is None:
                joker_found = True
                joker_index = i
                break
        if joker_found:
            cards[0], cards[joker_index] = cards[joker_index], cards[0]
        return cards

    def decide_decks_for_duel(self, opponent_decks):
        my_min_deck = min([deck for deck in self.decks if deck.state == constants.DeckState.UNOPENED],
                     key=lambda x: x.index)
        opponent_min_deck = min([deck for deck in opponent_decks if deck.state == constants.DeckState.UNOPENED],
                           key=lambda x: x.index)
        return my_min_deck, opponent_min_deck


class Card(object):
    def __init__(self, suit, colored, rank, value=None, is_open=False):
        self.suit = suit
        self.colored = colored
        self.rank = rank
        self.value = value
        self.is_open = is_open

    def __eq__(self, other):
        return self.suit == other.suit and self.colored == other.colored and self.value == other.value

    def __repr__(self):
        if self.is_open:
            if self.suit is None:
                return '{} {}'.format(self.value, '★' if self.colored else '☆')
            else:
                return '{} {}'.format(self.value, self.suit[0])
        else:
            return '?'

    def open_up(self):
        self.is_open = True


class Deck(object):
    def __init__(self, cards, state=constants.DeckState.UNOPENED, index=None):
        self.state = state
        self.cards = cards
        self.index = index  # one-based

    def __repr__(self):
        return ' / '.join([repr(card) for card in self.cards])

    def delegate(self):
        return self.cards[0]


class Duel(object):
    def __init__(self, player_red, player_black, index, time_created=None, over=False, time_ended=None, player_shouted=None, winner=None, loser=None, result=None, offense=None, defense=None):
        self.player_red = player_red
        self.player_black = player_black
        self.time_created = time_created or time.time()
        self.index = index  # one-based
        self.over = over
        self.time_ended = time_ended
        self.player_shouted = player_shouted
        self.winner = winner
        self.loser = loser
        self.result = result
        self.offense = offense
        self.defense = defense
    
    def players(self):
        return self.player_red, self.player_black

    def decide_offense(self):
        if self.index % 2 == 1:
            self.offense, self.defense = self.player_red, self.player_black
        else:
            self.offense, self.defense = self.player_black, self.player_red

    def decide_decks_for_duel(self):
        # Skip choosing deck in the last duel
        if self.index == constants.DECK_PER_PILE:
            offense_deck = [deck for deck in self.offense.decks if deck.state == constants.DeckState.UNOPENED].pop()
            defense_deck = [deck for deck in self.defense.decks if deck.state == constants.DeckState.UNOPENED].pop()
        else:
            offense_deck, defense_deck = self.offense.decide_decks_for_duel(self.defense.decks)
        offense_deck.state = constants.DeckState.IN_DUEL
        defense_deck.state = constants.DeckState.IN_DUEL
        self.offense.deck_in_duel = offense_deck
        self.defense.deck_in_duel = defense_deck

        # display the decks chosen
        print('\nThe two decks have been chosen!')

    def display_decks(self):
        row_format = '{:^15}' * constants.DECK_PER_PILE
        red_first_line = '{:^105}{:^30}'.format('{} ({})'.format(self.player_red.name, self.player_red.alias),
                                                'Score {} / Die {}'.format(self.player_red.num_victory,
                                                                           self.player_red.num_shout_die))
        print(red_first_line)
        red_numbers = [
            '< #{} >'.format(deck.index) if deck.state == constants.DeckState.IN_DUEL else '#{}'.format(deck.index)
            for deck in self.player_red.decks]
        red_number_line = row_format.format(*red_numbers)
        print(red_number_line)
        red_unopened_delegates = [repr(deck.cards[0]) if deck.state == constants.DeckState.UNOPENED else '' for deck in
                                  self.player_red.decks]
        print(row_format.format(*red_unopened_delegates))
        red_opened_delegates = ['' if deck.state == constants.DeckState.UNOPENED else repr(deck.cards[0]) for deck in
                                self.player_red.decks]
        print(row_format.format(*red_opened_delegates))
        red_seconds = ['' if deck.state == constants.DeckState.UNOPENED else repr(deck.cards[1]) for deck in
                       self.player_red.decks]
        print(row_format.format(*red_seconds))
        red_lasts = ['' if deck.state == constants.DeckState.UNOPENED else repr(deck.cards[2]) for deck in
                     self.player_red.decks]
        print(row_format.format(*red_lasts))
        print()
        black_lasts = ['' if deck.state == constants.DeckState.UNOPENED else repr(deck.cards[2]) for deck in
                       self.player_black.decks]
        print(row_format.format(*black_lasts))
        black_seconds = ['' if deck.state == constants.DeckState.UNOPENED else repr(deck.cards[1]) for deck in
                         self.player_black.decks]
        print(row_format.format(*black_seconds))
        black_opened_delegates = ['' if deck.state == constants.DeckState.UNOPENED else repr(deck.cards[0]) for deck in
                                  self.player_black.decks]
        print(row_format.format(*black_opened_delegates))
        black_unopened_delegate = [repr(deck.cards[0]) if deck.state == constants.DeckState.UNOPENED else '' for deck in
                                   self.player_black.decks]
        print(row_format.format(*black_unopened_delegate))
        black_numbers = [
            '< #{} >'.format(deck.index) if deck.state == constants.DeckState.IN_DUEL else '#{}'.format(deck.index) for
            deck in self.player_black.decks]
        black_number_line = row_format.format(*black_numbers)
        print(black_number_line)
        black_first_line = '{:^105}{:^30}'.format('{} (Player Black)'.format(self.player_black.name),
                                                  'Score {} / Die {}'.format(self.player_black.num_victory,
                                                                             self.player_black.num_shout_die))
        print(black_first_line)

    def open_next_cards(self):
        if self.over:
            print("\nLet's open the last cards anyway.\n")
        else:
            print("Cards will be opened in {} seconds!\n".format(constants.DELAY_BEFORE_CARD_OPEN))
            time.sleep(constants.DELAY_BEFORE_CARD_OPEN)
        for player in self.players():
            player.open_next_card()

    def process_action(self, player_shouted, action):
        if action is None:
            self.process_no_shouts()
        elif action == constants.Action.DARE:
            self.process_double_dare()
        elif action == constants.Action.DIE:
            self.process_shout_die(player_shouted)
        elif action == constants.Action.DONE:
            self.process_shout_done(player_shouted)
        elif action == constants.Action.DRAW:
            self.process_shout_draw(player_shouted)
        else:
            raise ValueError('Unaccepted action.')

    def process_no_shouts(self):
        """compare the sums and decides the winner"""
        print('All right. No actions.')
        sum_red = sum([card.value for card in self.player_red.deck_in_duel.cards])
        sum_black = sum([card.value for card in self.player_black.deck_in_duel.cards])
        if sum_red > sum_black:
            self.end(constants.DuelResult.FINISHED, winner=self.player_red)
        elif sum_red < sum_black:
            self.end(constants.DuelResult.FINISHED, winner=self.player_black)
        else:
            self.end(constants.DuelResult.DRAWN, winner=self.defense)

    def process_double_dare(self):
        """do nothing if both users have dared after the second cards are open"""
        print('Ooh, double dare!')
        pass

    def process_shout_die(self, player_shouted):
        player_shouted.num_shout_die += 1
        self.end(constants.DuelResult.DIED, player_shouted)

    def process_shout_done(self, player_shouted):
        player_shouted.num_shout_done += 1
        values = set(
            [card.value for deck in player_shouted.decks if deck.state != constants.DeckState.UNOPENED for card in
             deck.cards if card.is_open])
        if len(values) == len(constants.RANKS):
            self.end(constants.DuelResult.ABORTED_BY_CORRECT_DONE, player_shouted)
        else:
            if player_shouted.num_shout_done > constants.MAX_DONE:
                self.end(constants.DuelResult.ABORTED_BY_WRONG_DONE, player_shouted)
            else:
                print("That was a wrong done, but you'll have one more chance.")

    def process_shout_draw(self, player_shouted):
        player_shouted.num_shout_draw += 1
        player_red_deck_sum = sum([card.value for card in self.player_red.deck_in_duel.cards])
        player_black_deck_sum = sum([card.value for card in self.player_black.deck_in_duel.cards])
        if player_red_deck_sum == player_black_deck_sum:
            self.end(constants.DuelResult.DRAWN, winner=player_shouted)
        else:
            if player_shouted.num_shout_draw > constants.MAX_DRAW:
                self.end(constants.DuelResult.ABORTED_BY_WRONG_DRAW, player_shouted)
            else:
                print("That was a wrong draw, but you'll have one more chance.")

    def get_and_process_input(self):
        def red_shout_dare(key):
            keyboard.unhook_key(key.name)
            print('Player Red shouted Dare!')
            player_has_shouted_dare[constants.PLAYER_RED] = True

        def red_shout_die(key):
            keyboard.unhook_key(key.name)
            print('Player Red shouted Die!')
            has_red_shouted_other[constants.Action.DIE] = True

        def red_shout_done(key):
            keyboard.unhook_key(key.name)
            print('Player Red shouted Done!')
            has_red_shouted_other[constants.Action.DONE] = True

        def black_shout_dare(key):
            keyboard.unhook_key(key.name)
            print('Player Black shouted Dare!')
            player_has_shouted_dare[constants.PLAYER_BLACK] = True

        def black_shout_die(key):
            keyboard.unhook_key(key.name)
            print('Player black shouted Die!')
            has_black_shouted_other[constants.Action.DIE] = True

        def black_shout_done(key):
            keyboard.unhook_key(key.name)
            print('Player black shouted Done!')
            has_black_shouted_other[constants.Action.DONE] = True

        # Prevent double done
        red_opened_values = ComputerPlayer.opened_values(self.player_red.decks)
        red_unopened_values = ComputerPlayer.unopened_values(self.player_red.decks)
        red_right_before_done = len(red_opened_values) == constants.NUM_CARD - 1 and len(red_unopened_values) == 1
        black_opened_values = ComputerPlayer.opened_values(self.player_black.decks)
        black_unopened_values = ComputerPlayer.unopened_values(self.player_black.decks)
        black_right_before_done = len(black_opened_values) == constants.NUM_CARD - 1 and len(black_unopened_values) == 1
        if red_right_before_done and black_right_before_done:
            self.end(constants.DuelResult.ABORTED_BEFORE_DOUBLE_DONE, winner=self.player_black)

        # reset the players' actions before getting input
        player_has_shouted_dare = {constants.PLAYER_RED: False, constants.PLAYER_BLACK: False}
        has_red_shouted_other = {constants.Action.DIE: False, constants.Action.DONE: False,
                                 constants.Action.DRAW: False, }
        has_black_shouted_other = {constants.Action.DIE: False, constants.Action.DONE: False,
                                   constants.Action.DRAW: False, }

        # hook keys
        keyboard.on_press_key(self.player_red.key_settings[constants.Action.DARE], red_shout_dare)
        if self.player_red.num_shout_die < constants.MAX_DIE:
            keyboard.on_press_key(self.player_red.key_settings[constants.Action.DIE], red_shout_die)
        keyboard.on_press_key(self.player_red.key_settings[constants.Action.DONE], red_shout_done)
        keyboard.on_press_key(self.player_black.key_settings[constants.Action.DARE], black_shout_dare)
        if self.player_black.num_shout_die < constants.MAX_DIE:
            keyboard.on_press_key(self.player_black.key_settings[constants.Action.DIE], black_shout_die)
        keyboard.on_press_key(self.player_black.key_settings[constants.Action.DONE], black_shout_done)

        # start timing and wait for key press
        print('\nWhat will you two do?')
        num_open = len([card for card in self.offense.deck_in_duel.cards if card.is_open])
        offense_delegate = self.offense.deck_in_duel.delegate()
        defense_delegate = self.defense.deck_in_duel.delegate()
        start = time.time()
        while not (all([player_has_shouted_dare[player.alias] for player in self.players()])
                   or any(has_red_shouted_other.values()) or any(
                    has_black_shouted_other.values()) or time.time() - start > constants.TIME_LIMIT_FOR_ACTION):
            pass
        keyboard.unhook_all()

        # identify and process the action
        has_found_action = False
        if all([player_has_shouted_dare[player.alias] for player in self.players()]):
            self.process_action(None, constants.Action.DARE)
            has_found_action = True
        for action, has_happened in has_red_shouted_other.items():
            if not has_found_action and has_happened:
                self.process_action(self.player_red, action)
                has_found_action = True
        for action, has_happened in has_black_shouted_other.items():
            if not has_found_action and has_happened:
                self.process_action(self.player_black, action)
                has_found_action = True
        if not has_found_action:  # consider no input as dare
            print('All right. No actions. That counts as a double dare.')
            self.process_action(None, constants.Action.DARE)

    def get_and_process_final_input(self):
        def red_shout_done(key):
            keyboard.unhook_key(key.name)
            print('Player Red shouted Done!')
            has_red_shouted_other[constants.Action.DONE] = True

        def red_shout_draw(key):
            keyboard.unhook_key(key.name)
            print('Player Red shouted Draw!')
            has_red_shouted_other[constants.Action.DRAW] = True

        def black_shout_done(key):
            keyboard.unhook_key(key.name)
            print('Player black shouted Done!')
            has_black_shouted_other[constants.Action.DONE] = True

        def black_shout_draw(key):
            keyboard.unhook_key(key.name)
            print('Player black shouted Draw!')
            has_black_shouted_other[constants.Action.DRAW] = True

        # reset the players' actions before getting input
        has_red_shouted_other = {constants.Action.DIE: False, constants.Action.DONE: False,
                                 constants.Action.DRAW: False}
        has_black_shouted_other = {constants.Action.DIE: False, constants.Action.DONE: False,
                                   constants.Action.DRAW: False}

        # hook keys
        keyboard.on_press_key(self.player_red.key_settings[constants.Action.DONE], red_shout_done)
        keyboard.on_press_key(self.player_red.key_settings[constants.Action.DRAW], red_shout_draw)
        keyboard.on_press_key(self.player_black.key_settings[constants.Action.DONE], black_shout_done)
        keyboard.on_press_key(self.player_black.key_settings[constants.Action.DRAW], black_shout_draw)

        # start timing and wait for key press
        print("\nShout done or draw, if that's the case.")
        start = time.time()
        while not (any(has_red_shouted_other.values()) or any(has_black_shouted_other.values())
                   or time.time() - start > constants.TIME_LIMIT_FOR_FINAL_ACTION):
            pass
        keyboard.unhook_all()

        # identify and process the action
        has_found_action = False
        for action, has_happened in has_red_shouted_other.items():
            if not has_found_action and has_happened:
                self.process_action(self.player_red, action)
                has_found_action = True
        for action, has_happened in has_black_shouted_other.items():
            if not has_found_action and has_happened:
                self.process_action(self.player_black, action)
                has_found_action = True
        if not has_found_action:
            self.process_action(None, None)

    def end(self, result, player_shouted=None, winner=None, loser=None):
        self.over = True
        self.time_ended = time.time()
        self.result = result
        self.player_shouted = player_shouted
        self.winner = winner
        self.loser = loser
        if winner is None and loser is None:
            if result == constants.DuelResult.DIED:
                print("Duel #{}: {} died, so no one gets a point.".format(self.index, self.player_shouted.name))
            elif result == constants.DuelResult.DRAWN:
                self.winner = self.defense
                self.loser = self.offense
                self.winner.num_victory += 1
                print("Duel #{}: The sums are equal, but no one shouted draw, so the defense ({}) gets a point.".format(
                    self.index, self.winner.name))
            elif result == constants.DuelResult.ABORTED_BY_CORRECT_DONE:
                print("Duel #{}: {} is done, so this duel is aborted.".format(self.index, self.player_shouted.name))
            elif result == constants.DuelResult.ABORTED_BY_WRONG_DONE:
                print(
                    "Duel #{}: {} shouted done wrong, so this duel is aborted.".format(self.index,
                                                                                       self.player_shouted.name))
            elif result == constants.DuelResult.ABORTED_BY_WRONG_DRAW:
                print(
                    "Duel #{}: {} shouted draw wrong, so this duel is aborted.".format(self.index,
                                                                                       self.player_shouted.name))
            else:
                raise ValueError('At least one of winner or loser must be supplied.')
        else:
            if winner is None:
                self.winner = self.defense if loser == self.offense else self.offense
            if loser is None:
                self.loser = self.offense if winner == self.offense else self.defense
            self.winner.num_victory += 1
            print("Duel #{}: {} wins and gets a point.".format(self.index, self.winner.name))


class OutputHandler(object):
    def __init__(self):
        self.states = []
        self.messages = []

    def display(self, game_state_in_json=None, message='', duration=0):
        if game_state_in_json is None:
            if message:
                message_delimited = message.split('\n')
                print('Message:  {}'.format(message_delimited[0]))
                for line in message_delimited[1:]:
                    print('{:10}{}'.format('', line))
            time.sleep(duration)
            return
        self.states.append(game_state_in_json)
        self.messages.append(message)
        game = jsonpickle.decode(game_state_in_json)
        duel = game.duel_ongoing
        row_format = '{:^15}' * constants.DECK_PER_PILE
        red_fense = '' if duel is None else ('Offense' if game.player_red == duel.offense else 'Defense')
        red_first_line = '{:^30}{:^75}{:^30}'.format(red_fense,
                                                     '{} ({})'.format(game.player_red.name, game.player_red.alias),
                                                     'Score {} / Die {}'.format(game.player_red.num_victory,
                                                                                game.player_red.num_shout_die))
        print(red_first_line)
        red_decks = game.player_red.decks
        red_numbers = ['< #{} >'.format(deck.index) if deck.state == constants.DeckState.IN_DUEL else '#{}'.format(
            deck.index) for deck in red_decks]
        red_number_line = row_format.format(*red_numbers)
        print(red_number_line)
        red_unopened_delegates = [repr(deck.cards[0]) if deck.state == constants.DeckState.UNOPENED else '' for deck in
                                  red_decks]
        print(row_format.format(*red_unopened_delegates))
        red_opened_delegates = ['' if deck.state == constants.DeckState.UNOPENED else repr(deck.cards[0]) for deck in
                                red_decks]
        print(row_format.format(*red_opened_delegates))
        red_seconds = ['' if deck.state == constants.DeckState.UNOPENED else repr(deck.cards[1]) for deck in
                       red_decks]
        print(row_format.format(*red_seconds))
        red_lasts = ['' if deck.state == constants.DeckState.UNOPENED else repr(deck.cards[2]) for deck in
                     red_decks]
        print(row_format.format(*red_lasts))
        print()
        print('{:^135}'.format('' if duel is None else '[Duel #{}]'.format(duel.index)))
        print()
        black_decks = game.player_black.decks
        black_lasts = ['' if deck.state == constants.DeckState.UNOPENED else repr(deck.cards[2]) for deck in
                       black_decks]
        print(row_format.format(*black_lasts))
        black_seconds = ['' if deck.state == constants.DeckState.UNOPENED else repr(deck.cards[1]) for deck in
                         black_decks]
        print(row_format.format(*black_seconds))
        black_opened_delegates = ['' if deck.state == constants.DeckState.UNOPENED else repr(deck.cards[0]) for
                                  deck in black_decks]
        print(row_format.format(*black_opened_delegates))
        black_unopened_delegate = [repr(deck.cards[0]) if deck.state == constants.DeckState.UNOPENED else '' for
                                   deck in black_decks]
        print(row_format.format(*black_unopened_delegate))
        black_numbers = [
            '< #{} >'.format(deck.index) if deck.state == constants.DeckState.IN_DUEL else '#{}'.format(
                deck.index) for deck in black_decks]
        black_number_line = row_format.format(*black_numbers)
        print(black_number_line)
        black_fense = '' if duel is None else ('Offense' if game.player_black == duel.offense else 'Defense')
        black_first_line = '{:^30}{:^75}{:^30}'.format(black_fense, '{} (Player Black)'.format(game.player_black.name),
                                                       'Score {} / Die {}'.format(game.player_black.num_victory,
                                                                                  game.player_black.num_shout_die))
        print(black_first_line)
        if message:
            message_delimited = message.split('\n')
            print('Message:  {}'.format(message_delimited[0]))
            for line in message_delimited[1:]:
                print('{:10}{}'.format('', line))
        time.sleep(duration)
        
    def export_to_json(self, last_game_state_in_json=None):
        if last_game_state_in_json is None:
            last_game_state_in_json = self.states[-1]
        last_game = jsonpickle.decode(last_game_state_in_json)
        red_class = last_game.player_red.__class__.__name__
        red_name = last_game.player_red.name
        black_class = last_game.player_black.__class__.__name__
        black_name = last_game.player_black.name
        time_created_str = last_game.time_created
        time_created_float = float(time_created_str)
        datetime_started = datetime.datetime.fromtimestamp(time_created_float)
        datetime_str = datetime.datetime.strftime(datetime_started, '%Y%m%d%H%M%S')
        file_name = '{}({}){}({}){}.json'.format(red_class, red_name, black_class, black_name, datetime_str)
        content = jsonpickle.encode(self.states)
        with open(file_name, 'w') as file:
            file.write(content)

    def import_from_json(self, file_name):
        with open(file_name) as file:
            content = file.read()
            self.states = jsonpickle.decode(content)

            
if __name__ == '__main__':
    game = Game(*sys.argv[1:])
    game.initialize_players()
    game.set_keys()
    game.initialize_decks()
    output_handler = OutputHandler()
    while not game.over:
        duel = game.start_duel()
        output_handler.display(jsonpickle.encode(game))
        duel.decide_decks_for_duel()
        output_handler.display(jsonpickle.encode(game))
        duel.open_next_cards()
        output_handler.display(jsonpickle.encode(game))
        duel.get_and_process_input()
        output_handler.display(jsonpickle.encode(game))
        duel.open_next_cards()
        output_handler.display(jsonpickle.encode(game))
        if not duel.over:
            duel.get_and_process_final_input()
        game.cleanup_duel()
    ending_message = 'Game!\nCongratulations! {} has won the Game! (Reason: {})'.format(game.winner.name, game.result)
    output_hander.display(jsonpickle.encode(game), ending_message)
