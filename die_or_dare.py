import abc
import constants
import datetime
import functools
import itertools
import json
import jsonpickle
import keyboard
import numpy
import os
import random
import sys
import time


class Input(abc.ABC):
    @staticmethod
    def validate(function_):
        @functools.wraps(function_)
        def wrapper_validate(*args, **kwargs):
            if args[0].is_valid():
                return function_(*args, **kwargs)
            else:
                raise ValueError('Invalid input.')

        return wrapper_validate

    @abc.abstractmethod
    def is_valid(self, *args, **kwargs):
        pass

    @property
    @abc.abstractmethod
    def value(self):
        pass


class NameInput(Input):
    def __init__(self, name=None):
        self._name = name

    def is_valid(self):
        if self._name is None:
            return False
        return self._name.isalnum()

    @property
    def value(self):
        return self._name


class NameTextInput(NameInput):
    @classmethod
    def from_human(cls, prompt, forbidden_name=''):
        name = input(prompt)
        while not name.isalnum() or name == forbidden_name:
            if name == forbidden_name:
                print("You can't use that name. Choose another name.")
            else:
                print('Only alphanumeric characters are allowed.')
            name = input(prompt)
        return cls(name)

    @classmethod
    def auto_generate(cls, forbidden_name):
        name = 'Computer' + str(random.randint(1, 999999))
        if name == forbidden_name:
            name += 'a'
        return cls(name)


class KeySettingsInput(Input):
    def __init__(self, key_settings=None):
        self._key_settings = key_settings

    def is_valid(self):
        if self._key_settings is None:
            return False
        all_actions_set = all(
            self._key_settings.get(action) is not None for action in
            constants.Action)
        num_keys = len(set(self._key_settings.keys()))
        num_values = len(set(self._key_settings.values()))
        all_keys_distinct = num_keys == num_values
        return all_actions_set and all_keys_distinct

    @property
    def value(self):
        return self._key_settings

    @staticmethod
    def bottom_left():
        return {constants.Action.DARE: 'z', constants.Action.DIE: 'x',
                constants.Action.DONE: 'c', constants.Action.DRAW: 'v'}

    @staticmethod
    def top_left():
        return {constants.Action.DARE: 'q', constants.Action.DIE: 'w',
                constants.Action.DONE: 'e', constants.Action.DRAW: 'r'}

    @staticmethod
    def top_right():
        return {constants.Action.DARE: 'u', constants.Action.DIE: 'i',
                constants.Action.DONE: 'o', constants.Action.DRAW: 'p'}


class KeySettingsTextInput(KeySettingsInput):
    @classmethod
    def from_human(cls, player_name, blacklist=None):
        key_settings = {action: '' for action in constants.Action}
        if blacklist is None:
            blacklist = []
        print('\n{}, decide the set of keys you will use.'.format(player_name))
        for action in key_settings:
            prompt = '{}, which key will you use to indicate {}? '.format(
                player_name, action.name)
            key = input(prompt)
            is_single = len(key) == 1
            is_lower = key.islower()
            is_not_duplicate = key not in blacklist
            is_valid_key = is_single and is_lower and is_not_duplicate
            while not is_valid_key:
                if key in blacklist:
                    print("You can't use the following key(s): {}".format(
                        ', '.join(blacklist)))
                else:
                    print('Use a single lowercase alphabet.')
                prompt = '{}, which key will you use to indicate {}? '.format(
                    player_name, action.name)
                key = input(prompt)
                is_single = len(key) == 1
                is_lower = key.islower()
                is_not_duplicate = key not in blacklist
                is_valid_key = is_single and is_lower and is_not_duplicate
            key_settings[action] = key
            blacklist.append(key)
        return cls(key_settings)


class JokerValueStrategy(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def apply(cards):
        pass


class Thirteen(JokerValueStrategy):
    @staticmethod
    def apply(cards):
        for card in cards:
            if card.is_joker():
                card.value = max(constants.Rank.value)
                break


class SameAsMax(JokerValueStrategy):
    @staticmethod
    def apply(cards):
        if any(card.is_joker() for card in cards):
            joker = next(card for card in cards if card.is_joker())
            cards_without_joker = [card for card in cards if card != joker]
            biggest = max(cards_without_joker, key=lambda x: x.value)
            joker.value = biggest.value


class RandomNumber(JokerValueStrategy):
    @staticmethod
    def apply(cards):
        for card in cards:
            if card.is_joker():
                values = [rank.value for rank in constants.Rank]
                card.value = random.choice(values)
                break


class NextBiggest(JokerValueStrategy):
    @staticmethod
    def apply(cards):
        if any(card.is_joker() for card in cards):
            joker = next(card for card in cards if card.is_joker())
            cards_without_joker = [card for card in cards if card != joker]
            biggest = max(cards_without_joker, key=lambda x: x.value)
            smallest = min(cards_without_joker, key=lambda x: x.value)
            if biggest.value == 1:
                joker.value = 1
            elif biggest.value == 2:
                joker.value = 3 - smallest.value
            else:
                if smallest.value == biggest.value - 1:
                    joker.value = biggest.value - 2
                else:
                    joker.value = biggest.value - 1


class JokerPositionStrategy(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def apply(cards):
        pass


class JokerFirst(JokerPositionStrategy):
    @staticmethod
    def apply(cards):
        biggest = max(cards, key=lambda x: x.value)
        biggest_index = cards.index(biggest)
        cards[0], cards[biggest_index] = cards[biggest_index], cards[0]
        joker_index = -1
        for i in range(len(cards)):
            if cards[i].is_joker():
                joker_index = i
        if joker_index > -1:
            joker = cards[joker_index]
            cards_without_joker = [card for card in cards if
                                   not card.is_joker()]
            non_joker_bigger = max(cards_without_joker, key=lambda x: x.value)
            if joker.value == non_joker_bigger.value:
                cards[0], cards[joker_index] = cards[joker_index], cards[0]
            elif joker.value < non_joker_bigger.value:
                cards[1], cards[joker_index] = cards[joker_index], cards[1]


class JokerLast(JokerPositionStrategy):
    @staticmethod
    def apply(cards):
        biggest = max(cards, key=lambda x: x.value)
        biggest_index = cards.index(biggest)
        cards[0], cards[biggest_index] = cards[biggest_index], cards[0]
        joker_index = -1
        for i in range(len(cards)):
            if cards[i].is_joker():
                joker_index = i
        if joker_index > -1:
            joker = cards[joker_index]
            cards_without_joker = [card for card in cards if
                                   not card.is_joker()]
            bigger = max(cards_without_joker, key=lambda x: x.value)
            bigger_index = cards.index(bigger)
            if joker.value <= bigger.value:
                cards[0], cards[bigger_index] = cards[bigger_index], cards[0]
            for i in range(len(cards)):
                if cards[i].is_joker():
                    joker_index = i
            cards[-1], cards[joker_index] = cards[joker_index], cards[-1]


class JokerAnywhere(JokerPositionStrategy):
    @staticmethod
    def apply(cards):
        biggest = max(cards, key=lambda x: x.value)  # may or may not be a joker
        biggest_index = cards.index(biggest)
        cards[0], cards[biggest_index] = cards[biggest_index], cards[0]


class JokerValueStrategyInput(Input):
    def __init__(self, strategy=None):
        self._strategy = strategy

    def is_valid(self):
        if self._strategy is None:
            return False
        is_subclass = issubclass(self._strategy, JokerValueStrategy)
        is_abstract = issubclass(JokerValueStrategy, self._strategy)
        return is_subclass and not is_abstract

    @property
    def value(self):
        return self._strategy


class JokerValueStrategyTextInput(JokerValueStrategyInput):
    @classmethod
    def from_human(cls, player_name):
        number_to_strategy = {1: Thirteen, 2: SameAsMax, 3: RandomNumber,
                              4: NextBiggest}
        valid_input = False
        input_value = None
        while not valid_input:
            print(
                '\n{}, enter the number corresponding to the strategy you want.'.format(
                    player_name))
            print('Press 1 to set the value of Joker to 13.')
            print(
                'Press 2 to set the value of Joker to be equal to the biggest value in the deck.')
            print('Press 3 to set the value of Joker to be a random number.')
            print(
                'Press 4 to set the value of Joker to be the biggest value that is not in the deck.')
            prompt = 'What is your choice? '
            input_value = input(prompt)
            try:
                input_value = int(input_value)
                if input_value not in number_to_strategy:
                    raise ValueError('Input not among choices.')
            except ValueError:
                print('Invalid input.')
            else:
                valid_input = True
        strategy = number_to_strategy.get(input_value)
        return cls(strategy)


class JokerPositionStrategyInput(Input):
    def __init__(self, strategy=None):
        self._strategy = strategy

    def is_valid(self):
        if self._strategy is None:
            return False
        is_subclass = issubclass(self._strategy, JokerPositionStrategy)
        is_abstract = issubclass(JokerPositionStrategy, self._strategy)
        return is_subclass and not is_abstract

    @property
    def value(self):
        return self._strategy


class JokerPositionStrategyTextInput(JokerPositionStrategyInput):
    @classmethod
    def from_human(cls, player_name):
        number_to_strategy = {1: JokerFirst, 2: JokerLast, 3: JokerAnywhere}
        valid_input = False
        input_value = None
        while not valid_input:
            print(
                '\n{}, enter the number corresponding to the strategy you want.'.format(
                    player_name))
            print('Enter 1 to reveal the joker as soon as possible.')
            print('Enter 2 to hide the joker as long as possible.')
            print('Enter 3 to put joker anywhere.')
            prompt = 'What is your choice? '
            input_value = input(prompt)
            try:
                input_value = int(input_value)
                if input_value not in number_to_strategy:
                    raise ValueError('Input not among choices.')
            except ValueError:
                print('Invalid input.')
            else:
                valid_input = True
        strategy = number_to_strategy.get(input_value)
        return cls(strategy)


class OffenseDeckChoiceStrategy(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def apply(decks_me, decks_opponent, num_victory_me, num_shout_die_me,
              num_victory_opponent, num_shout_die_opponent):
        pass


class BiggestOffenseDeck(OffenseDeckChoiceStrategy):
    @staticmethod
    def apply(decks_me, decks_opponent, num_victory_me, num_shout_die_me,
              num_victory_opponent, num_shout_die_opponent):
        undisclosed_decks_me = [deck for deck in decks_me if
                                deck.is_undisclosed()]
        return max(undisclosed_decks_me, key=lambda x: x.index)


class DefenseDeckChoiceStrategy(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def apply(decks_me, decks_opponent, num_victory_me, num_shout_die_me,
              num_victory_opponent, num_shout_die_opponent, offense_deck=None):
        pass


class SmallestDefenseDeck(DefenseDeckChoiceStrategy):
    @staticmethod
    def apply(decks_me, decks_opponent, num_victory_me, num_shout_die_me,
              num_victory_opponent, num_shout_die_opponent, offense_deck=None):
        undisclosed_decks_opponent = [deck for deck in decks_opponent if
                                      deck.is_undisclosed()]
        return min(undisclosed_decks_opponent, key=lambda x: x.index)


class ActionChoiceStrategy(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def apply(decks_me, decks_opponent, num_victory_me, num_shout_die_me,
              num_victory_opponent, num_shout_die_opponent, round_, in_turn):
        pass


class SimpleActionChoiceStrategy(ActionChoiceStrategy):
    @staticmethod
    def apply(decks_me, decks_opponent, num_victory_me, num_shout_die_me,
              num_victory_opponent, num_shout_die_opponent, round_, in_turn):
        if not ComputerPlayer.undisclosed_values(decks_me):
            return constants.Action.DONE
        elif round_ == 1:
            odds_win, odds_draw, odds_lose = ComputerPlayer.get_chances(
                decks_me, decks_opponent)
            if in_turn:
                odds_lose += odds_draw
            else:
                odds_win += odds_draw
            if odds_lose > odds_win + .1:
                if random.random() < .7:
                    return constants.Action.DIE
                else:
                    return constants.Action.DARE
        elif round_ == 2:
            odds_win, odds_draw, odds_lose = ComputerPlayer.get_chances(
                decks_me, decks_opponent)
            if in_turn:
                odds_lose += odds_draw
            else:
                odds_win += odds_draw
            if num_shout_die_me < constants.MAX_DIE:
                if odds_lose > odds_win + .1:
                    if random.random() < .7:
                        return constants.Action.DIE
                    else:
                        return constants.Action.DARE
            return constants.Action.DARE
        elif round_ == 3:
            deck_in_duel_me = next(
                (deck for deck in decks_me if deck.is_in_duel()))
            deck_in_duel_opponent = next(
                (deck for deck in decks_opponent if
                 deck.is_in_duel()))
            sum_me = sum(card.value for card in deck_in_duel_me)
            sum_opponent = sum(
                card.value for card in deck_in_duel_opponent)
            if sum_me == sum_opponent:
                return constants.Action.DRAW
            else:
                return None
        else:
            raise Exception('Something went wrong.')


class DeckInput(Input):
    def __init__(self, deck=None):
        self._deck = deck

    def is_valid(self):
        return isinstance(self._deck, Deck)

    @property
    def value(self):
        return self._deck


class DeckTextInput(DeckInput):
    @classmethod
    def from_human(cls, player_name=None, is_opponent=None,
                   undisclosed_decks=None):
        user_input_to_deck = {deck.index: deck for deck in undisclosed_decks}
        valid_input = False
        input_value = None
        possessive = "your opponent's" if is_opponent else 'your'
        prompt = '{}, choose one of {} decks. (Enter the deck number): '.format(
            player_name, possessive)
        while not valid_input:
            input_value = input(constants.INDENT + prompt)
            try:
                input_value = int(input_value) - 1
                if input_value not in user_input_to_deck:
                    raise ValueError('Input not among choices.')
            except ValueError:
                choices_generator = (str(deck.index + 1) for deck in
                                     undisclosed_decks)
                choices_str = ', '.join(choices_generator)
                error_message = 'Enter a number among {}.\n'.format(
                    choices_str)
                prompt = error_message + prompt
            else:
                valid_input = True
        deck = user_input_to_deck.get(input_value)
        return cls(deck)


class DeckIndexInput(Input):
    def __init__(self, deck_index):
        self._deck_index = deck_index

    def is_valid(self, *args, **kwargs):
        return self._deck_index in range(constants.DECK_PER_PILE)

    @property
    def value(self):
        return self._deck_index


class OffenseDeckIndexInput(DeckIndexInput):
    pass


class DefenseDeckIndexInput(DeckIndexInput):
    pass


class Shout(object):
    def __init__(self, player, action):
        self._player = player
        self._action = action

    @property
    def player(self):
        return self._player

    @property
    def action(self):
        return self._action


class ShoutInput(Input):
    def __init__(self, shouts):
        self._shouts = shouts

    def is_valid(self, *args, **kwargs):
        try:
            iter(self._shouts)
        except TypeError:
            return False
        else:
            return all(isinstance(shout, Shout) for shout in self._shouts)

    @property
    def value(self):
        return self._shouts


class ShoutKeypressInput(ShoutInput):
    def __init__(self, keys_pressed):
        super().__init__(keys_pressed)
        self._keys_pressed = keys_pressed

    @classmethod
    def from_human(cls, keys_to_hook=None, timeout=0):
        def when_key_pressed(x):
            keyboard.unhook_key(x.name)
            keys_pressed.append(x.name)

        keys_pressed = []
        if keys_to_hook is None:
            keys_to_hook = []
        else:
            keys_to_hook = (key for key in keys_to_hook if key is not None)
        for key in keys_to_hook:
            keyboard.on_press_key(key, when_key_pressed)
        over = False
        start = time.time()
        while not over:
            over = time.time() - start > timeout
        keyboard.unhook_all()
        keys_str = ''.join(keys_pressed)
        return cls(keys_str)

    @property
    def value(self):
        return self._keys_pressed


class PlayerOrder(abc.ABC):
    def __init__(self, player1, player2):
        self._player1 = player1
        self._player2 = player2
        self._first = None
        self._second = None

    @property
    def players(self):
        return self._first, self._second


class RandomPlayerOrder(PlayerOrder):
    def __init__(self, player1, player2):
        super().__init__(player1, player2)
        if random.random() > .5:
            self._first = self._player1
            self._second = self._player2
        else:
            self._first = self._player2
            self._second = self._player1


class KeepOrder(PlayerOrder):
    def __init__(self, player1, player2):
        super().__init__(player1, player2)
        self._first = self._player1
        self._second = self._player2


class ReverseOrder(PlayerOrder):
    def __init__(self, player1, player2):
        super().__init__(player1, player2)
        self._first = self._player2
        self._second = self._player1


class Game(object):
    def __init__(self, player_red=None, player_black=None, over=False,
                 time_started=None, time_ended=None, winner=None, loser=None,
                 result=None, duels=None, *args):
        self.player_red = player_red  # takes the red pile and gets to go first
        self.player_black = player_black
        self._over = over
        if time_started is None:
            time_started = time.time()
        self.time_started = time_started
        self.time_ended = time_ended
        self.winner = winner
        self.loser = loser
        self.result = result
        self.duel_index = -1  # zero based
        if duels is None:
            duels = []
            for i in range(constants.DECK_PER_PILE):
                new_duel = Duel(player_red, player_black, i)
                duels.append(new_duel)
            self.duels = tuple(duels)
        self.duel_ongoing = None
        self.red_pile = RedPile().cards
        self.black_pile = BlackPile().cards
        num_computers = len(args)
        if num_computers in range(3):
            self._num_human_players = 2 - num_computers
        else:
            raise ValueError('Invalid number of computer players.')

    @property
    def players(self):
        return self.player_red, self.player_black

    def initialize_decks(self):
        for player in self.players:
            player.initialize_decks()

    def set_keys(self):
        self.player_red.set_keys()
        player_red_keys = list(self.player_red.key_settings.values())
        self.player_black.set_keys(blacklist=player_red_keys)

    def _open_next_cards(self):
        for player in self.players:
            player.open_next_card()

    def to_next_duel(self):
        self.duel_index += 1
        self.duel_ongoing = self.duels[self.duel_index]
        self.duel_ongoing.start()
        return self.duel_ongoing

    def is_over(self):
        return self._over

    def prepare(self):
        duel = self.duel_ongoing
        if self._num_human_players == 2:
            action_prompt = 'What will you two do?'
        else:
            action_prompt = 'What will you do?\nEnter your action!'
        if duel.offense.deck_in_duel is None:
            message = 'Duel #{} started! Time to choose the offense deck.'.format(
                duel.index + 1)
            duration = constants.Duration.BEFORE_DECK_CHOICE
        elif duel.defense.deck_in_duel is None:
            message = 'Time to choose the defense deck.'
            duration = constants.Duration.BEFORE_DECK_CHOICE
        elif duel.round_ in (1, 2):
            self._open_next_cards()
            duel.to_next_round()
            message = action_prompt
            duration = constants.Duration.BEFORE_ACTION
        else:
            message = 'Something went wrong.'
            duration = None
        return message, duration

    def accept(self):
        duel = self.duel_ongoing
        if duel.offense.deck_in_duel is None:
            return self._decide_offense_deck()
        elif duel.defense.deck_in_duel is None:
            return self._decide_defense_deck()
        elif duel.round_ in (1, 2):
            timeout = constants.Duration.ACTION
            return self._get_actions(timeout=timeout)
        elif duel.round_ == 3:
            timeout = constants.Duration.FINAL_ACTION
            return self._get_actions(timeout=timeout)
        else:
            raise ValueError('Invalid.')

    def _get_actions(self, timeout=0):
        duel = self.duel_ongoing
        round_ = duel.round_
        if all(isinstance(player, HumanPlayer) for player in self.players):
            keys = []
            for player in self.players:
                valid_actions = player.valid_actions(round_)
                for action in valid_actions:
                    key = player.key_settings.get(action)
                    keys.append(key)
            shout_input = ShoutKeypressInput.from_human(keys, timeout)
            return shout_input
        else:
            shouts = []
            for player in duel.players:
                valid_actions = player.valid_actions(round_)
                is_shout_valid = False
                shout = None
                in_turn = player == duel.offense
                opponent = duel.defense if in_turn else duel.offense
                decks_opponent = opponent.decks
                num_victory_opponent = opponent.num_victory
                num_shout_die_opponent = opponent.num_shout_die
                while not is_shout_valid:
                    shout = player.shout(decks_opponent, num_victory_opponent,
                                         num_shout_die_opponent, round_,
                                         in_turn)
                    action = shout.action
                    is_shout_valid = action in valid_actions
                shouts.append(shout)
            shout_input = ShoutInput(shouts)
            return shout_input

    def process(self, intra_duel_input):
        if isinstance(intra_duel_input, OffenseDeckIndexInput):
            return self.process_offense_deck_index_input(intra_duel_input)
        elif isinstance(intra_duel_input, DefenseDeckIndexInput):
            return self.process_defense_deck_index_input(intra_duel_input)
        elif isinstance(intra_duel_input, ShoutKeypressInput):
            return self.process_shout_keypress(intra_duel_input)
        elif isinstance(intra_duel_input, ShoutInput):
            return self.process_shout(intra_duel_input)
        else:
            raise ValueError('Invalid input')

    def process_shout_keypress(self, intra_duel_input):
        duel = self.duel_ongoing
        round_ = duel.round_
        # See who did which action
        shouts = []
        keys_pressed = intra_duel_input.value
        for key_pressed in keys_pressed:
            for player in self.players:
                valid_actions = player.valid_actions(round_)
                key_to_action = {key: action for action, key in
                                 player.key_settings.items()}
                action = key_to_action.get(key_pressed)
                if action in valid_actions:
                    shout = Shout(player, action)
                    shouts.append(shout)
        shout_input = ShoutInput(shouts)
        return self.process_shout(shout_input)

    def process_shout(self, shout_input):
        shouts = shout_input.value
        duel = self.duel_ongoing
        round_ = duel.round_
        # Get only the first shout for each player
        red_shout_heard = False
        black_shout_heard = False
        for shout in shouts:
            if not red_shout_heard and shout.player == self.player_red:
                red_shout_heard = True
                self.player_red.recent_action = shout.action
            elif not black_shout_heard and shout.player == self.player_black:
                black_shout_heard = True
                self.player_black.recent_action = shout.action
            if red_shout_heard and black_shout_heard:
                break
        # priority: done > die > draw > dare (then offense > defense)
        for player in duel.players:
            valid_actions = player.valid_actions(round_)
            if constants.Action.DONE in valid_actions:
                if player.recent_action == constants.Action.DONE:
                    player.num_shout_done += 1
                    if player.is_done():  # correct done
                        duel.end(constants.DuelState.ABORTED_BY_CORRECT_DONE)
                        self._end(constants.GameResult.DONE, winner=player)
                        message = "{0} is done, so Duel #{1} is aborted.\n{0} wins! The game has ended as {0} first shouted done correctly.".format(
                            player.name, duel.index + 1)
                        duration = constants.Duration.AFTER_GAME_ENDS
                        return message, duration
        for player in duel.players:
            valid_actions = player.valid_actions(round_)
            if constants.Action.DIE in valid_actions:
                if player.recent_action == constants.Action.DIE:
                    player.num_shout_die += 1
                    duel.end(constants.DuelState.DIED)
                    message = "{} died, so no one gets a point. Duel #{} ended.".format(
                        player.name, duel.index + 1)
                    duration = constants.Duration.AFTER_DUEL_ENDS
                    return message, duration
        for player in duel.players:
            valid_actions = player.valid_actions(round_)
            if constants.Action.DRAW in valid_actions:
                if player.recent_action == constants.Action.DRAW:
                    player.num_shout_draw += 1
                    if duel.is_drawn():  # correct draw
                        duel.end(constants.DuelState.DRAWN, player)
                        message = '{} shouted draw correctly and gets a point. Duel #{} ended.'.format(
                            player.name, duel.index + 1)
                        duration = constants.Duration.AFTER_DUEL_ENDS
                        if duel.winner.num_victory == constants.REQUIRED_WIN:
                            self._end(constants.GameResult.FINISHED,
                                      winner=duel.winner)
                            message += "\n{0} wins! The game has ended as {0} first scored {1} points.".format(
                                duel.winner.name, constants.REQUIRED_WIN)
                            duration = constants.Duration.AFTER_GAME_ENDS
                        return message, duration
        if round_ in (1, 2):
            duration = constants.Duration.BEFORE_CARD_OPEN
            message = "Ooh, double dare! Next cards will be opened in {} seconds!".format(
                duration)
            # do nothing and move on to next round to open next cards
            return message, duration
        elif round_ == 3:
            sum_offense = sum(card.value for card in duel.offense.deck_in_duel)
            sum_defense = sum(card.value for card in duel.defense.deck_in_duel)
            if sum_offense > sum_defense:
                duel.end(constants.DuelState.FINISHED, winner=duel.offense)
                message = '{0} has a greater sum, so {0} gets a point. Duel #{1} ended.'.format(
                    duel.winner.name, duel.index + 1)
            elif sum_offense < sum_defense:
                duel.end(constants.DuelState.FINISHED, winner=duel.defense)
                message = '{0} has a greater sum, so {0} gets a point. Duel #{1} ended.'.format(
                    duel.winner.name, duel.index + 1)
            else:
                duel.end(constants.DuelState.DRAWN, winner=duel.defense)
                message = "The sums are equal, but no one shouted draw, so the defense ({}) gets a point. Duel #{} ended.".format(
                    duel.winner.name, duel.index + 1)
            if duel.winner.num_victory == constants.REQUIRED_WIN:
                self._end(constants.GameResult.FINISHED, winner=duel.winner)
                message += "\n{0} wins! The game has ended as {0} first scored {1} points.".format(
                    duel.winner.name, constants.REQUIRED_WIN)
                duration = constants.Duration.AFTER_GAME_ENDS
                return message, duration
            else:
                duration = constants.Duration.AFTER_DUEL_ENDS
                return message, duration
        raise ValueError('Invalid round.')

    def process_offense_deck_index_input(self, intra_duel_input):
        duel = self.duel_ongoing
        offense = duel.offense
        index = intra_duel_input.value
        offense_deck = offense.decks[index]
        if offense_deck.is_undisclosed():
            duel.summon(offense_deck)
            message = 'Deck #{} chosen as the offense deck.'.format(index + 1)
        else:
            message = 'Choose an undisclosed deck.'
        duration = constants.Duration.AFTER_DECK_CHOICE
        return message, duration

    def process_defense_deck_index_input(self, intra_duel_input):
        index = intra_duel_input.value
        duel = self.duel_ongoing
        defense_deck = duel.defense.decks[index]
        if defense_deck.is_undisclosed():
            duel.summon(defense_deck=defense_deck)
            message = 'Deck #{} chosen as the defense deck.'.format(index + 1)
        else:
            message = 'Choose an undisclosed deck.'
        duration = constants.Duration.AFTER_DECK_CHOICE
        return message, duration

    def _decide_offense_deck(self):
        duel = self.duel_ongoing
        offense, defense = duel.players
        # Skip choosing deck in the last duel
        if self.duel_index == constants.DECK_PER_PILE - 1:
            offense_undisclosed_decks = offense.undisclosed_decks()
            deck = offense_undisclosed_decks[0]
        else:
            deck = offense.decide_offense_deck(defense.decks,
                                               defense.num_victory,
                                               defense.num_shout_die)
        return OffenseDeckIndexInput(deck.index)

    def _decide_defense_deck(self):
        duel = self.duel_ongoing
        offense, defense = duel.players
        # Skip choosing deck in the last duel
        if self.duel_index == constants.DECK_PER_PILE - 1:
            defense_undisclosed_decks = defense.undisclosed_decks()
            deck = defense_undisclosed_decks[0]
        else:
            deck = offense.decide_defense_deck(defense.decks,
                                               defense.num_victory,
                                               defense.num_shout_die,
                                               offense.deck_in_duel)
        return DefenseDeckIndexInput(deck.index)

    def _end(self, result, winner=None, loser=None):
        self._over = True
        self.result = result
        self.time_ended = time.time()
        self.winner = winner
        self.loser = loser
        if self.winner is None and self.loser is None:
            raise ValueError('Either winner or loser must be supplied.')
        elif self.winner is None:
            if self.loser == self.player_black:
                self.winner = self.player_red
            else:
                self.winner = self.player_black
        elif self.loser is None:
            if self.winner == self.player_black:
                self.loser = self.player_red
            else:
                self.loser = self.player_black

    def to_json(self):
        return jsonpickle.encode(self)


class DeckRandomizer(object):
    def __init__(self, pile, joker_value_strategy=Thirteen,
                 joker_position_strategy=JokerLast):
        self._pile = pile
        self._joker_value_strategy = joker_value_strategy
        self._joker_position_strategy = joker_position_strategy

    def pop(self):
        pile = list(self._pile)
        random.shuffle(pile)
        decks_previous = []
        for j in range(constants.DECK_PER_PILE):
            cards = []
            for k in range(constants.CARD_PER_DECK):
                new_card = pile.pop()
                cards.append(new_card)
            self._joker_value_strategy.apply(cards)
            self._joker_position_strategy.apply(cards)
            decks_previous.append(tuple(cards))
        decks_previous.sort(key=lambda x: x[0].value)
        decks = []
        for index, cards in enumerate(decks_previous):
            deck = Deck(cards, index=index)
            deck.delegate().open_up()
            decks.append(deck)
        return tuple(decks)


class Player(object):
    def __init__(self, name='', deck_in_duel_index=None, num_victory=0,
                 num_shout_die=0, num_shout_done=0, num_shout_draw=0,
                 decks=None, pile=None, key_settings=None,
                 alias=None, recent_action=None):
        self.name = name
        self._deck_in_duel_index = deck_in_duel_index
        self.deck_in_duel = None
        self.num_victory = num_victory
        self.num_shout_die = num_shout_die
        self.num_shout_done = num_shout_done
        self.num_shout_draw = num_shout_draw
        self.decks = decks
        self.pile = pile
        if key_settings is None:
            key_settings = {action: '' for action in constants.Action}
        self.key_settings = key_settings
        self.alias = alias
        self.recent_action = recent_action

    def valid_actions(self, round_):
        actions = [None, constants.Action.DONE]
        if round_ == 1:
            actions.append(constants.Action.DARE)
            if self.num_shout_die < constants.MAX_DIE:
                actions.append(constants.Action.DIE)
        elif round_ == 2:
            actions.append(constants.Action.DARE)
            if self.num_shout_die < constants.MAX_DIE:
                actions.append(constants.Action.DIE)
        elif round_ == 3:
            if self.num_shout_draw < constants.MAX_DRAW:
                actions.append(constants.Action.DRAW)
        else:
            raise ValueError('Something went wrong.')
        return actions

    def undisclosed_decks(self):
        return [deck for deck in self.decks if deck.is_undisclosed()]

    def take_pile(self, pile):
        if isinstance(pile, RedPile):
            self.pile = pile.cards
            self.alias = constants.PLAYER_RED
        elif isinstance(pile, BlackPile):
            self.pile = pile._cards
            self.alias = constants.PLAYER_BLACK
        else:
            raise ValueError('This is not a pile.')

    def initialize_decks(self, joker_value_strategy, joker_position_strategy):
        self.decks = DeckRandomizer(self.pile, joker_value_strategy,
                                    joker_position_strategy).pop()

    @abc.abstractmethod
    def set_keys(self, blacklist=None):
        pass

    @abc.abstractmethod
    def decide_offense_deck(self, decks_opponent, num_victory_opponent,
                            num_shout_die_opponent):
        pass

    @abc.abstractmethod
    def decide_defense_deck(self, decks_opponent, num_victory_opponent,
                            num_shout_die_opponent, offense_deck):
        pass

    def send_to_duel(self, deck, opponent_deck=None):
        self.deck_in_duel = deck
        self._deck_in_duel_index = deck.index
        deck.enter_duel(opponent_deck=opponent_deck)

    def open_next_card(self):
        deck = self.decks[self._deck_in_duel_index]
        if deck.card_to_open_index is None:
            deck.card_to_open_index = 1
        card_to_open = deck[deck.card_to_open_index]
        card_to_open.open_up()
        deck.card_to_open_index += 1
        if deck.card_to_open_index == 3:
            deck.card_to_open_index = None

    def is_done(self):
        disclosed_values = ComputerPlayer.disclosed_values(self.decks)
        num_disclosed_values = len(disclosed_values)
        num_all_values = len(constants.Rank)
        return num_disclosed_values == num_all_values

    def to_array(self):
        decks = [deck.to_array() for deck in self.decks]
        decks = list(itertools.chain.from_iterable(decks))
        num_victory = -1 if self.num_victory is None else self.num_victory
        num_shout_die = -1 if self.num_shout_die is None else self.num_shout_die
        if self._deck_in_duel_index is None:
            deck_in_duel_index = -1
        else:
            deck_in_duel_index = self._deck_in_duel_index
        others = [num_victory, num_shout_die, deck_in_duel_index]
        return numpy.array(decks + others)

    @classmethod
    def from_array(cls, array):
        decks_array = numpy.array(array[0:9 * 19])
        decks_reshaped = decks_array.reshape(9, -1)
        decks = [Deck.from_array(deck_array) for deck_array in decks_reshaped]
        num_victory = None if array[9 * 19] == -1 else array[9 * 19]
        num_shout_die = None if array[9 * 19 + 1] == -1 else array[9 * 19 + 1]
        deck_in_duel_index = None if array[9 * 19 + 2] == -1 else array[
            9 * 19 + 2]
        return cls(decks=decks, num_victory=num_victory,
                   num_shout_die=num_shout_die,
                   deck_in_duel_index=deck_in_duel_index)


class HumanPlayer(Player):
    def __init__(self, prompt, forbidden_name=''):
        super().__init__()
        self.name = NameTextInput.from_human(prompt, forbidden_name).value

    def set_keys(self, blacklist=None):
        key_settings_input = KeySettingsTextInput.from_human(self.name,
                                                             blacklist)
        self.key_settings = key_settings_input.value

    def decide_offense_deck(self, decks_opponent, num_victory_opponent,
                            num_shout_die_opponent):
        undisclosed_decks = self.undisclosed_decks()
        deck_input = DeckTextInput.from_human(self.name, False,
                                              undisclosed_decks)
        return deck_input.value

    def decide_defense_deck(self, decks_opponent, num_victory_opponent,
                            num_shout_die_opponent, offense_deck=None):
        undisclosed_decks = [deck for deck in decks_opponent if
                             deck.is_undisclosed()]
        deck_input = DeckTextInput.from_human(self.name, True,
                                              undisclosed_decks)
        return deck_input.value

    def shout(self, decks_opponent, num_victory_opponent,
              num_shout_die_opponent, round_, in_turn):
        allowed_actions = self.valid_actions(round_)
        keys_settings_in_list = ['{}: \'{}\''.format(action.name, key) for
                                 action, key in self.key_settings.items() if
                                 action in allowed_actions]
        do_nothing = 'Pass: \'Enter\''
        keys_settings_in_list.append(do_nothing)
        keys_settings_in_str = ', '.join(keys_settings_in_list)
        prompt = '{}, what will you do? ({})'.format(self.name,
                                                     keys_settings_in_str)
        shout_input = input(constants.INDENT + prompt)
        key_to_action = {key: action for action, key in
                         self.key_settings.items()}
        action = key_to_action.get(shout_input)
        return Shout(self, action)


class ComputerPlayer(Player):
    def __init__(self, forbidden_name='',
                 offense_deck_index_strategy=BiggestOffenseDeck,
                 defense_deck_index_strategy=SmallestDefenseDeck,
                 action_choice_strategy=SimpleActionChoiceStrategy):
        super().__init__()
        self.name = NameTextInput.auto_generate(forbidden_name).value
        self.offense_deck_index_strategy = offense_deck_index_strategy
        self.defense_deck_index_strategy = defense_deck_index_strategy
        self.action_choice_strategy = action_choice_strategy

    def set_keys(self, blacklist=None):
        if self.alias == constants.PLAYER_RED:
            self.key_settings = KeySettingsInput.bottom_left()
        else:
            self.key_settings = KeySettingsInput.top_right()

    def decide_offense_deck(self, decks_opponent, num_victory_opponent,
                            num_shout_die_opponent):
        strategy = self.offense_deck_index_strategy
        deck = strategy.apply(self.decks, decks_opponent, self.num_victory,
                              self.num_shout_die, num_victory_opponent,
                              num_shout_die_opponent)
        return deck

    def decide_defense_deck(self, decks_opponent, num_victory_opponent,
                            num_shout_die_opponent, offense_deck):
        strategy = self.defense_deck_index_strategy
        deck = strategy.apply(self.decks, decks_opponent, self.num_victory,
                              self.num_shout_die, num_victory_opponent,
                              num_shout_die_opponent, offense_deck)
        return deck

    @staticmethod
    def get_chances(decks_me, decks_opponent,
                    joker_value_strategy_me=SameAsMax):
        """get chances of winning, tying, and losing
        assuming both player use SameAsMax for joker value strategy
        """

        def guess_joker_value(delegate_value, joker_value_strategy=SameAsMax):
            """give an educated guess about the value of joker
            (There is no guarantee that the return value is correct.)
            """
            if joker_value_strategy == Thirteen:
                return 13
            elif joker_value_strategy == SameAsMax:
                return delegate_value
            elif joker_value_strategy == NextBiggest:
                return delegate_value - 1
            else:
                return random.randint(1, delegate_value)

        # get my hidden cards
        deck_in_duel_me = next(deck for deck in decks_me if deck.is_in_duel())
        num_opened = sum(1 for card in deck_in_duel_me if card.is_open())
        current_sum_me = sum(
            card.value for card in deck_in_duel_me if card.is_open())
        num_to_open = 3 - num_opened
        delegate_value_me = deck_in_duel_me.delegate().value
        hidden_cards_me = []
        for deck in decks_me:
            for card in deck:
                if not card.is_open():
                    if card.is_joker() or card.value <= delegate_value_me:
                        hidden_cards_me.append(card)
        # get the opponent's cards
        deck_in_duel_opponent = next(
            deck for deck in decks_opponent if deck.is_in_duel())
        current_sum_opponent = sum(
            card.value for card in deck_in_duel_opponent if
            card.is_open())
        delegate_value_opponent = deck_in_duel_opponent.delegate().value
        hidden_cards_opponent = []
        for deck in decks_opponent:
            for card in deck:
                if not card.is_open():
                    if card.is_joker() or card.value <= delegate_value_opponent:
                        hidden_cards_opponent.append(card)
        # calculate the odds
        num_win, num_lose, num_draw = 0, 0, 0
        candidates_me = itertools.combinations(hidden_cards_me, num_to_open)
        candidates_opponent = itertools.combinations(hidden_cards_opponent,
                                                     num_to_open)
        for cards_me in candidates_me:
            for cards_opponent in candidates_opponent:
                # get my sum
                sum_me = current_sum_me
                for card in cards_me:
                    if card.is_joker():
                        sum_me += guess_joker_value(delegate_value_me,
                                                    joker_value_strategy_me)
                    else:
                        sum_me += card.value
                # get opponent's sum
                sum_opponent = current_sum_opponent
                for card in cards_opponent:
                    if card.is_joker():
                        sum_opponent += guess_joker_value(
                            delegate_value_opponent)
                    else:
                        sum_opponent += card.value
                # compare
                if sum_me > sum_opponent:
                    num_win += 1
                elif sum_me == sum_opponent:
                    num_draw += 1
                else:
                    num_lose += 1
        total = num_win + num_draw + num_lose
        odds_win = round(num_win / total, 3)
        odds_draw = round(num_draw / total, 3)
        odds_lose = round(num_lose / total, 3)
        return odds_win, odds_draw, odds_lose

    @classmethod
    def undisclosed_values(cls, decks):
        values = set(rank.value for rank in constants.Rank)
        disclosed_values = set(cls.disclosed_values(decks))
        undisclosed_values = values.difference(disclosed_values)
        return tuple(undisclosed_values)

    @staticmethod
    def disclosed_values(decks):
        values = set()
        for deck in decks:
            if not deck.is_undisclosed():
                for card in deck.cards:
                    if card.is_open():
                        values.add(card.value)
        return tuple(values)

    def shout(self, decks_opponent, num_victory_opponent,
              num_shout_die_opponent, round_, in_turn):
        strategy = self.action_choice_strategy
        action = strategy.apply(self.decks, decks_opponent, self.num_victory,
                                self.num_shout_die, num_victory_opponent,
                                num_shout_die_opponent, round_, in_turn)
        return Shout(self, action)


class Card(object):
    def __init__(self, suit, colored, rank, value=None, open_=False):
        self.suit = suit
        self.colored = colored
        self.rank = rank
        self.value = value
        self._open = open_

    def __eq__(self, other):
        same_suit = self.suit == other.suit
        same_color = self.colored == other.colored
        same_value = self.value == other.value
        return same_suit and same_color and same_value

    def __repr__(self):
        if self.is_open():
            if self.suit is None:
                suit_symbol = '★' if self.colored else '☆'
            else:
                suit_symbol = self.suit.name[0]
            return '{} {}'.format(self.value, suit_symbol)
        else:
            return '?'

    def open_up(self):
        self._open = True

    def is_open(self):
        return self._open

    def is_joker(self):
        return self.suit is None

    def to_array(self):
        suit = -1 if self.suit is None else self.suit.value
        colored = -1 if self.colored is None else int(self.colored)
        rank = -1 if self.rank is None else constants.Rank[self.rank].value
        value = -1 if self.value is None else self.value
        open_ = -1 if self._open is None else int(self._open)
        list_ = [suit, colored, rank, value, open_]
        return numpy.array(list_)

    @classmethod
    def from_array(cls, array):
        suit, colored, rank, value, open_ = tuple(array)
        suit = None if suit == -1 else constants.Suit(suit)
        colored = None if colored == -1 else bool(colored)
        rank = None if rank == -1 else constants.Rank(rank)
        value = None if value == -1 else value
        open_ = None if open_ == -1 else bool(open_)
        return cls(suit, colored, rank, value, open_)


class Deck(object):
    def __init__(self, cards, state=constants.DeckState.UNDISCLOSED, index=None,
                 opponent_deck_index=None, card_to_open_index=None):
        self._state = state
        self._cards = cards
        self._index = index  # zero based
        self._opponent_deck_index = opponent_deck_index
        self.card_to_open_index = card_to_open_index

    def __repr__(self):
        return ' / '.join(repr(card) for card in self._cards)

    def __getitem__(self, index):
        return self._cards[index]

    @property
    def index(self):
        return self._index

    @property
    def cards(self):
        return self._cards

    def delegate(self):
        return self._cards[0]

    def is_undisclosed(self):
        return self._state == constants.DeckState.UNDISCLOSED

    def is_in_duel(self):
        return self._state == constants.DeckState.IN_DUEL

    def enter_duel(self, opponent_deck=None):
        self._state = constants.DeckState.IN_DUEL
        if opponent_deck is not None:
            self.meet_opponent(opponent_deck)
            opponent_deck.meet_opponent(self)

    def meet_opponent(self, opponent_deck):
        self._opponent_deck_index = opponent_deck.index

    def finish(self):
        self._state = constants.DeckState.FINISHED

    def to_array(self):
        if self._cards is None:
            cards_flattened = []
        else:
            cards_generator = (card.to_array() for card in self._cards)
            cards = numpy.array(cards_generator)
            cards_flattened = cards.flatten()
        state = -1 if self._state is None else self._state.value
        index = -1 if self._index is None else self._index
        if self._opponent_deck_index is None:
            opponent_deck_index = -1
        else:
            opponent_deck_index = self._opponent_deck_index
        if self.card_to_open_index is None:
            card_to_open_index = -1
        else:
            card_to_open_index = self.card_to_open_index
        list_ = [*cards_flattened, state, index, opponent_deck_index,
                 card_to_open_index]
        return numpy.array(list_)

    @classmethod
    def from_array(cls, array):
        cards = [array[0:5], array[5:10], array[10:15]]
        state = array[15]
        index = array[16]
        opponent_deck_index = array[17]
        card_to_open_index = array[18]
        cards_flattened = numpy.array(cards).flatten()
        if cards_flattened:
            cards = [Card.from_array(card_array) for card_array in cards]
        else:
            cards = None
        state = None if state == -1 else constants.DeckState(state)
        index = None if index == -1 else index
        if opponent_deck_index == -1:
            opponent_deck_index = None
        if card_to_open_index == -1:
            card_to_open_index = None
        return cls(cards, state, index, opponent_deck_index, card_to_open_index)


class Duel(object):
    def __init__(self, player_red, player_black, index, time_started=None,
                 round_=1, over=False, time_ended=None, winner=None,
                 loser=None, state=constants.DuelState.UNSTARTED, offense=None,
                 defense=None):
        self.player_red = player_red
        self.player_black = player_black
        self._index = index
        if time_started is None:
            self.time_started = time.time()
        else:
            self.time_started = time_started
        self._round = round_
        self._over = over
        self.time_ended = time_ended
        self.winner = winner
        self.loser = loser
        self._state = state
        if offense is None:
            if self._index % 2 == 0:
                self.offense = self.player_red
            else:
                self.offense = self.player_black
        else:
            self.offense = offense
        if defense is None:
            if self._index % 2 == 0:
                self.defense = self.player_black
            else:
                self.defense = self.player_red
        else:
            self.defense = defense

    @property
    def players(self):
        return self.offense, self.defense

    @property
    def index(self):
        return self._index

    @property
    def round_(self):
        return self._round

    def to_next_round(self):
        self._round += 1

    def start(self):
        self._state = constants.DuelState.ONGOING

    def summon(self, offense_deck=None, defense_deck=None):
        offense, defense = self.players
        if offense_deck is not None:
            offense.send_to_duel(offense_deck)
        elif defense_deck is not None:
            if offense_deck is None:
                offense_deck = offense.deck_in_duel
            defense.send_to_duel(defense_deck, opponent_deck=offense_deck)
        else:
            raise Exception(
                'Either the offense deck or the defense deck must be supplied.')

    def is_drawn(self):
        sum_offense = sum(card.value for card in self.offense.deck_in_duel)
        sum_defense = sum(card.value for card in self.defense.deck_in_duel)
        return sum_offense == sum_defense

    def is_over(self):
        return self._over

    def end(self, state, winner=None, loser=None):
        self._over = True
        self.time_ended = time.time()
        if state.value not in range(3, 10):
            raise ValueError('Invalid DeckState.')
        self._state = state
        self.winner = winner
        self.loser = loser
        if self.winner is None and self.loser is None:
            if state not in (constants.DuelState.DIED,
                             constants.DuelState.ABORTED_BY_CORRECT_DONE):
                raise ValueError('Either winner or loser must be supplied.')
        else:
            if winner is None:
                if loser == self.offense:
                    self.winner = self.defense
                else:
                    self.winner = self.offense
            elif loser is None:
                if winner == self.offense:
                    self.loser = self.offense
                else:
                    self.loser = self.defense
            self.winner.num_victory += 1
        for player in self.players:
            player.deck_in_duel.finish()
            for card in player.deck_in_duel:
                card.open_up()
            player.deck_in_duel = None
            player.recent_action = None


class PlayersSetup(object):
    def __init__(self, num_human_players):
        self.num_human_players = num_human_players

    def run(self):
        if self.num_human_players == 0:
            class1_name = sys.argv[1]
            class1 = globals().get(class1_name)
            is_subclass = issubclass(class1, ComputerPlayer)
            if not is_subclass or class1 == ComputerPlayer:
                raise ValueError('Invalid class name for computer player.')
            player1 = class1()
            class2_name = sys.argv[2]
            class2 = globals().get(class2_name)
            is_subclass = issubclass(class2, ComputerPlayer)
            if not is_subclass or class2 == ComputerPlayer:
                raise ValueError('Invalid class name for computer player.')
            forbidden_name = player1.name
            player2 = class2(forbidden_name)
        elif self.num_human_players == 1:
            class1_name = sys.argv[1]
            class1 = globals().get(class1_name)
            is_subclass = issubclass(class1, ComputerPlayer)
            if not is_subclass or class1 == ComputerPlayer:
                raise ValueError('Invalid class name for computer player.')
            player1 = class1()
            human_player1_prompt = 'Player 1, enter your name: '
            forbidden_name = player1.name
            player2 = HumanPlayer(human_player1_prompt, forbidden_name)
        elif self.num_human_players == 2:
            human_player1_prompt = 'Player 1, enter your name: '
            player1 = HumanPlayer(human_player1_prompt)
            human_player2_prompt = 'Player 2, enter your name: '
            forbidden_name = player1.name
            player2 = HumanPlayer(human_player2_prompt, forbidden_name)
        else:
            raise ValueError('Invalid number of human players.')
        return player1, player2


class Pile(object):
    pass


class RedPile(Pile):
    def __init__(self):
        red_joker = Card(None, True, constants.JOKER, None, False)
        cards = [red_joker]
        red_suits = (suit for suit in constants.Suit if suit.value % 2 == 0)
        for suit in red_suits:
            for rank in constants.Rank:
                card = Card(suit, True, rank.name, rank.value, False)
                cards.append(card)
        self._cards = tuple(cards)

    @property
    def cards(self):
        return self._cards


class BlackPile(Pile):
    def __init__(self):
        black_joker = Card(None, False, constants.JOKER, None, False)
        cards = [black_joker]
        black_suits = (suit for suit in constants.Suit if suit.value % 2 == 1)
        for suit in black_suits:
            for rank in constants.Rank:
                card = Card(suit, False, rank.name, rank.value, False)
                cards.append(card)
        self._cards = cards

    @property
    def cards(self):
        return self._cards


class OutputHandler(object):
    def __init__(self):
        self.states = []
        self.messages = []

    def save_and_display(self, game_state_in_json, message, duration):
        self.save(game_state_in_json, message)
        self.display(game_state_in_json, message, duration)

    def save(self, game_state_in_json, message):
        self.states.append(game_state_in_json)
        self.messages.append(message)

    @staticmethod
    def display(game_state_in_json=None, message='', duration=0):
        print('{:-^135}'.format(str()))
        if game_state_in_json is None and message:
            message_delimited = message.split('\n')
            print('Message:  {}'.format(message_delimited[0]))
            for line in message_delimited[1:]:
                print('{}{}'.format(constants.INDENT, line))
            time.sleep(duration)
            return
        game = jsonpickle.decode(game_state_in_json)
        duel = game.duel_ongoing
        row_format = '{:^15}' * constants.DECK_PER_PILE
        red_role = '' if duel is None else (
            'Offense' if game.player_red == duel.offense else 'Defense')

        red_name = '{} ({})'.format(game.player_red.name, game.player_red.alias)
        red_stats = 'Score {} / Die {}'.format(game.player_red.num_victory,
                                               game.player_red.num_shout_die)
        red_first_line = '{:^30}{:^75}{:^30}'.format(red_role, red_name,
                                                     red_stats)
        print(red_first_line)
        red_decks = game.player_red.decks
        red_numbers = (('< #{} >' if deck.is_in_duel() else '#{}').format(
            deck.index + 1) for deck in red_decks)
        red_number_line = row_format.format(*red_numbers)
        print(red_number_line)
        red_undisclosed_delegates = (
            repr(deck[0]) if deck.is_undisclosed() else '' for deck in
            red_decks)
        print(row_format.format(*red_undisclosed_delegates))
        red_opened_delegates = (
            '' if deck.is_undisclosed() else repr(deck[0]) for deck in
            red_decks)
        print(row_format.format(*red_opened_delegates))
        red_seconds = ('' if deck.is_undisclosed() else repr(deck[1]) for
                       deck in red_decks)
        print(row_format.format(*red_seconds))
        red_lasts = ('' if deck.is_undisclosed() else repr(deck[2]) for
                     deck in red_decks)
        print(row_format.format(*red_lasts))
        print()
        print('{:^135}'.format(
            '' if duel is None else '[Duel #{}]'.format(duel.index + 1)))
        print()
        black_decks = game.player_black.decks
        black_lasts = ('' if deck.is_undisclosed() else repr(deck[2]) for
                       deck in black_decks)
        print(row_format.format(*black_lasts))
        black_seconds = ('' if deck.is_undisclosed() else repr(deck[1])
                         for deck in black_decks)
        print(row_format.format(*black_seconds))
        black_opened_delegates = (
            '' if deck.is_undisclosed() else repr(deck[0]) for
            deck in black_decks)
        print(row_format.format(*black_opened_delegates))
        black_undisclosed_delegate = (
            repr(deck[0]) if deck.is_undisclosed() else '' for
            deck in black_decks)
        print(row_format.format(*black_undisclosed_delegate))
        black_numbers = (
            ('< #{} >' if deck.is_in_duel() else '#{}').format(
                deck.index + 1) for deck in black_decks)
        black_number_line = row_format.format(*black_numbers)
        print(black_number_line)
        black_role = '' if duel is None else (
            'Offense' if game.player_black == duel.offense else 'Defense')
        black_name = '{} (Player Black)'.format(game.player_black.name)
        black_stats = 'Win {} / Die {}'.format(game.player_black.num_victory,
                                               game.player_black.num_shout_die)
        black_first_line = '{:^30}{:^75}{:^30}'.format(black_role, black_name,
                                                       black_stats)
        print(black_first_line)
        if message:
            message_delimited = message.split('\n')
            print('Message:  {}'.format(message_delimited[0]))
            for line in message_delimited[1:]:
                print('{}{}'.format(constants.INDENT, line))
        time.sleep(duration)

    @staticmethod
    def extract_file_name(game_state_in_json):
        game = jsonpickle.decode(game_state_in_json)
        red_class = game.player_red.__class__.__name__
        red_name = game.player_red.name
        black_class = game.player_black.__class__.__name__
        black_name = game.player_black.name
        time_started_str = game.time_started
        time_started_float = float(time_started_str)
        datetime_started = datetime.datetime.fromtimestamp(time_started_float)
        datetime_str = datetime.datetime.strftime(datetime_started,
                                                  '%Y%m%d%H%M%S')
        file_name = '{}({}){}({}){}.json'.format(red_class, red_name,
                                                 black_class, black_name,
                                                 datetime_str)
        return file_name

    @staticmethod
    def export_json_to_file(game_state_json, file_path, final_state_only=False):
        with open(file_path, 'w') as file:
            if final_state_only:
                final_state = game_state_json[-1:]
                json.dump(final_state, file)
            else:
                json.dump(game_state_json, file)

    def export_game_states(self, file_location=None, file_name=None,
                           final_state_only=False):
        if not self.states:
            raise Exception('No game states found in this OutputHandler.')
        if file_location is None:
            current_file_path = os.path.abspath(__file__)
            current_directory_path = os.path.dirname(current_file_path)
            directory_name = 'json'
            file_location = os.path.join(current_directory_path, directory_name)
            if not os.path.exists(file_location):
                os.makedirs(file_location)
        if file_name is None:
            last_game_state = self.states[-1]
            file_name = self.extract_file_name(last_game_state)
        file_path = os.path.join(file_location, file_name)
        self.export_json_to_file(self.states, file_path, final_state_only)

    def import_from_json(self, file_path):
        with open(file_path) as file:
            content = file.read()
            self.states = jsonpickle.decode(content)


if __name__ == '__main__':
    pass
