import abc
import constants
import datetime
import functools
import itertools
import jsonpickle
import keyboard
import numpy
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

    @abc.abstractmethod
    def pop(self):
        pass


class NameInput(Input):
    def __init__(self, name=None):
        self.name = name

    def is_valid(self):
        if self.name is None:
            return False
        return self.name.isalnum()

    @Input.validate
    def pop(self):
        return self.name


class NameTextInput(NameInput):
    @classmethod
    def from_human(cls, prompt, forbidden_name=''):
        name = input(prompt)
        while not name.isalnum() or name == forbidden_name:
            if name == forbidden_name:
                print("You can't use {}. Choose another name.".format(
                    forbidden_name))
            else:
                print('Only alphanumeric characters are allowed.')
            name = input(prompt)
        return cls(name)

    @classmethod
    def auto_generate(cls, forbidden_name):
        name = 'Computer{}'.format(random.randint(1, 999999))
        if name == forbidden_name:
            name += 'a'
        return cls(name)


class KeySettingsInput(Input):
    def __init__(self, key_settings=None):
        self.key_settings = key_settings

    def is_valid(self):
        if self.key_settings is None:
            return False
        all_actions_set = all(
            self.key_settings.get(action) is not None for action in
            constants.Action)
        num_keys = len(set(self.key_settings.keys()))
        num_values = len(set(self.key_settings.values()))
        all_keys_distinct = num_keys == num_values
        return all_actions_set and all_keys_distinct

    @Input.validate
    def pop(self):
        return self.key_settings

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
        key_settings = {constants.Action.DARE: '', constants.Action.DIE: '',
                        constants.Action.DONE: '', constants.Action.DRAW: ''}
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
                card.value = max(constants.Rank)
                break


class SameAsMax(JokerValueStrategy):
    @staticmethod
    def apply(cards):
        if any([card.is_joker() for card in cards]):
            joker = [card for card in cards if card.is_joker()].pop()
            cards_without_joker = [card for card in cards if card != joker]
            biggest = max(cards_without_joker, key=lambda x: x.value)
            joker.value = biggest.value


class RandomNumber(JokerValueStrategy):
    @staticmethod
    def apply(cards):
        for card in cards:
            if card.is_joker():
                card.value = random.randint(1, max(constants.Rank))
                break


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
        self.strategy = strategy

    def is_valid(self):
        if self.strategy is None:
            return False
        is_subclass = issubclass(self.strategy, JokerValueStrategy)
        is_abstract = issubclass(JokerValueStrategy, self.strategy)
        return is_subclass and not is_abstract

    @Input.validate
    def pop(self):
        return self.strategy


class JokerValueStrategyTextInput(JokerValueStrategyInput):
    @classmethod
    def from_human(cls, player_name):
        number_to_strategy = {1: Thirteen, 2: SameAsMax, 3: RandomNumber}
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
        return cls(number_to_strategy.get(input_value))


class JokerPositionStrategyInput(Input):
    def __init__(self, strategy=None):
        self.strategy = strategy

    def is_valid(self):
        if self.strategy is None:
            return False
        is_subclass = issubclass(self.strategy, JokerPositionStrategy)
        is_abstract = issubclass(JokerPositionStrategy, self.strategy)
        return is_subclass and not is_abstract

    @Input.validate
    def pop(self):
        return self.strategy


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
        return cls(number_to_strategy.get(input_value))


class DeckInput(Input):
    def __init__(self, deck=None):
        self.deck = deck

    def is_valid(self):
        return isinstance(self.deck, Deck)

    @Input.validate
    def pop(self):
        return self.deck


class DeckTextInput(DeckInput):
    @classmethod
    def from_human(cls, player_name=None, is_opponent=None,
                   undisclosed_decks=None):
        user_input_to_deck = dict(
            {deck.index: deck for deck in undisclosed_decks})
        valid_input = False
        input_value = None
        possessive = "your opponent's" if is_opponent else 'your'
        prompt = '{}{}, choose one of {} deck (Enter the deck number): '.format(
            constants.INDENT, player_name, possessive)
        while not valid_input:
            input_value = input(prompt)
            try:
                input_value = int(input_value) - 1
                if input_value not in user_input_to_deck:
                    raise ValueError('Input not among choices.')
            except ValueError:
                choices_generator = [str(deck.index + 1) for deck in
                                     undisclosed_decks]
                choices_str = ', '.join(choices_generator)
                prompt = 'Invalid input. Enter a number among {}.'.format(
                    choices_str)
            else:
                valid_input = True
        return cls(user_input_to_deck.get(input_value))


class DeckChoiceInput(Input):
    def __init__(self, deck_index):
        self.deck_index = deck_index

    def is_valid(self, *args, **kwargs):
        return self.deck_index in range(constants.DECK_PER_PILE)

    def pop(self):
        return self.deck_index


class OffenseDeckChoiceInput(DeckChoiceInput):
    pass


class DefenseDeckChoiceInput(DeckChoiceInput):
    pass


class Shout(object):
    def __init__(self, player, action):
        self.player = player
        self.action = action


class ShoutInput(Input):
    def __init__(self, shouts):
        self.shouts = shouts

    def is_valid(self, *args, **kwargs):
        try:
            iter(self.shouts)
        except TypeError:
            return False
        else:
            return all(isinstance(shout, Shout) for shout in self.shouts)

    def pop(self):
        return self.shouts


class ShoutKeypressInput(ShoutInput):
    def __init__(self, keys_pressed):
        super().__init__(keys_pressed)
        self.keys_pressed = keys_pressed

    @classmethod
    def from_human(cls, keys_to_hook=None, timeout=0):
        def when_key_pressed(x):
            keyboard.unhook_key(x.name)
            keys_pressed.append(x.name)

        keys_pressed = []
        if keys_to_hook is None:
            keys_to_hook = []
        else:
            keys_to_hook = [key for key in keys_to_hook if key is not None]
        for key in keys_to_hook:
            keyboard.on_press_key(key, when_key_pressed)
        over = False
        start = time.time()
        while not over:
            over = time.time() - start > timeout
        keyboard.unhook_all()
        keys_str = ''.join([keyboard_event for keyboard_event in keys_pressed])
        return cls(keys_str)

    def pop(self):
        return self.keys_pressed


class PlayerOrder(abc.ABC):
    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2
        self.first = None
        self.second = None

    def pop(self):
        return self.first, self.second


class RandomPlayerOrder(PlayerOrder):
    def __init__(self, player1, player2):
        super().__init__(player1, player2)
        if random.random() > .5:
            self.first = self.player1
            self.second = self.player2
        else:
            self.first = self.player2
            self.second = self.player1


class KeepOrder(PlayerOrder):
    def __init__(self, player1, player2):
        super().__init__(player1, player2)
        self.first = self.player1
        self.second = self.player2


class ReverseOrder(PlayerOrder):
    def __init__(self, player1, player2):
        super().__init__(player1, player2)
        self.first = self.player2
        self.second = self.player1


class Game(object):
    def __init__(self, player_red=None, player_black=None, over=False,
                 time_started=None, time_ended=None, winner=None, loser=None,
                 result=None, duels=None, *args):
        self.player_red = player_red  # takes the red pile and gets to go first
        self.player_black = player_black
        self.over = over
        if time_started is None:
            self.time_started = time.time()
        else:
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

        red_joker = Card(None, True, constants.JOKER, None)
        red_pile = [red_joker]
        for suit in constants.RED_SUITS:
            for rank in constants.Rank:
                new_card = Card(suit, True, rank.name, rank.value, False)
                red_pile.append(new_card)
        self.red_pile = red_pile

        black_joker = Card(None, False, constants.JOKER, None, False)
        black_pile = [black_joker]
        for suit in constants.BLACK_SUITS:
            for rank in constants.Rank:
                new_card = Card(suit, False, rank.name, rank.value, False)
                black_pile.append(new_card)
        self.black_pile = black_pile

        num_computers = len(args)
        if num_computers in range(3):
            self.num_human_players = 2 - num_computers
        else:
            raise ValueError('Invalid number of computer players.')

    def players(self):
        return self.player_red, self.player_black

    def initialize_decks(self):
        for player in self.players():
            player.initialize_decks()

    def set_keys(self):
        self.player_red.set_keys()
        player_red_keys = list(self.player_red.key_settings.values())
        self.player_black.set_keys(blacklist=player_red_keys)

    def open_next_cards(self):
        for player in self.players():
            player.open_next_card()

    def to_next_duel(self):
        self.duel_index += 1
        self.duel_ongoing = self.duels[self.duel_index]
        self.duel_ongoing.state = constants.DuelState.ONGOING
        return self.duel_ongoing

    def is_over(self):
        return self.over

    def prepare(self):
        duel = self.duel_ongoing
        if self.num_human_players == 2:
            action_prompt = 'What will you two do?\nPress the keys!'
        else:
            action_prompt = 'What will you do?\nEnter your action!'
        if duel.offense.deck_in_duel is None:
            message = 'Duel #{} started!'.format(duel.index + 1)
            message += '\n{}, choose one of your decks.'.format(
                duel.offense.name)
            duration = constants.DELAY_BEFORE_DECK_CHOICE
        elif duel.defense.deck_in_duel is None:
            message = '{}, choose one of your opponent\'s decks.'.format(
                duel.offense.name)
            duration = constants.DELAY_BEFORE_DECK_CHOICE
        elif duel.round_ in (1, 2):
            self.open_next_cards()
            duel.round_ += 1
            message = action_prompt
            duration = constants.DELAY_BEFORE_ACTION
        else:
            message = 'Something went wrong.'
            duration = None
        return message, duration

    def accept(self):
        duel = self.duel_ongoing
        if duel.offense.deck_in_duel is None:
            return self.decide_decks_for_duel(is_opponent=False)
        elif duel.defense.deck_in_duel is None:
            return self.decide_decks_for_duel(is_opponent=True)
        elif duel.round_ in (1, 2):
            timeout = constants.TIME_LIMIT_FOR_ACTION
            return self.get_actions(timeout=timeout)
        elif duel.round_ == 3:
            timeout = constants.TIME_LIMIT_FOR_FINAL_ACTION
            return self.get_actions(timeout=timeout)
        else:
            raise ValueError('Invalid.')

    def get_actions(self, timeout=0):
        duel = self.duel_ongoing
        round_ = duel.round_
        if all([isinstance(player, HumanPlayer) for player in self.players()]):
            keys = []
            for player in self.players():
                valid_actions = player.valid_actions(round_)
                for action in valid_actions:
                    key = player.key_settings.get(action)
                    keys.append(key)
            shout_input = ShoutKeypressInput.from_human(keys, timeout)
            return shout_input
        else:
            shouts = []
            for player in duel.players():
                valid_actions = player.valid_actions(round_)
                is_shout_valid = False
                shout = None
                while not is_shout_valid:
                    shout = player.shout(round_)
                    action = shout.action
                    is_shout_valid = action in valid_actions
                shouts.append(shout)
            shout_input = ShoutInput(shouts)
            return shout_input

    def process(self, intra_duel_input):
        if isinstance(intra_duel_input, OffenseDeckChoiceInput):
            return self.process_offense_deck_choice_input(intra_duel_input)
        elif isinstance(intra_duel_input, DefenseDeckChoiceInput):
            return self.process_defense_deck_choice_input(intra_duel_input)
        elif isinstance(intra_duel_input, ShoutKeypressInput):
            return self.process_shout_keypress(intra_duel_input)
        elif isinstance(intra_duel_input, ShoutInput):
            return self.process_shout(intra_duel_input)
        else:
            return ValueError('Invalid input')

    def process_shout_keypress(self, intra_duel_input):
        duel = self.duel_ongoing
        round_ = duel.round_
        # See who did which action
        shouts = []
        keys_pressed = intra_duel_input.pop()
        for key_pressed in keys_pressed:
            for player in self.players():
                valid_actions = player.valid_actions(round_)
                key_to_action = dict(
                    {key: action for action, key in
                     player.key_settings.items()})
                action = key_to_action.get(key_pressed)
                if action in valid_actions:
                    shout = Shout(player, action)
                    shouts.append(shout)
        shout_input = ShoutInput(shouts)
        return self.process_shout(shout_input)

    def process_shout(self, shout_input):
        shouts = shout_input.pop()
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
        for player in duel.players():
            valid_actions = player.valid_actions(round_)
            if constants.Action.DONE in valid_actions:
                if player.recent_action == constants.Action.DONE:
                    player.num_shout_done += 1
                    if player.is_done():  # correct done
                        duel.end(constants.DuelState.ABORTED_BY_CORRECT_DONE)
                        self.end(constants.GameResult.DONE, winner=player)
                        message = "{0} is done, so Duel #{1} is aborted.\n{0} wins! The game has ended as {0} first shouted done correctly.".format(
                            player.name, duel.index + 1)
                        duration = constants.DELAY_AFTER_GAME_ENDS
                        return message, duration
        for player in duel.players():
            valid_actions = player.valid_actions(round_)
            if constants.Action.DIE in valid_actions:
                if player.recent_action == constants.Action.DIE:
                    player.num_shout_die += 1
                    duel.end(constants.DuelState.DIED)
                    message = "{} died, so no one gets a point.\nDuel #{} ended.".format(
                        player.name, duel.index + 1)
                    duration = constants.DELAY_AFTER_DUEL_ENDS
                    return message, duration
        for player in duel.players():
            valid_actions = player.valid_actions(round_)
            if constants.Action.DRAW in valid_actions:
                if player.recent_action == constants.Action.DRAW:
                    player.num_shout_draw += 1
                    if duel.is_drawn():  # correct draw
                        duel.end(constants.DuelState.DRAWN, player)
                        message = "The sums are equal, but no one shouted draw, so the defense ({}) gets a point.\nDuel #{}:ended.".format(
                            duel.winner.name, duel.index + 1)
                        duration = constants.DELAY_AFTER_DUEL_ENDS
                        if duel.winner.num_victory == constants.REQUIRED_WIN:
                            self.end(constants.GameResult.FINISHED,
                                     winner=duel.winner)
                            message += "{0} wins!\nThe game has ended as {0} first scored {1} points.".format(
                                duel.winner.name, constants.REQUIRED_WIN)
                            duration = constants.DELAY_AFTER_GAME_ENDS
                        return message, duration
        if round_ in [1, 2]:
            message = "Ooh, double dare! Let's open the next cards."
            duration = constants.DELAY_BEFORE_CARD_OPEN
            message += "\nCards will be opened in {} seconds!".format(duration)
            # do nothing and move on to next round to open next cards
            return message, duration
        elif round_ == 3:
            sum_offense = sum([card.value for card in
                               duel.offense.deck_in_duel.cards])
            sum_defense = sum([card.value for card in
                               duel.defense.deck_in_duel.cards])
            if sum_offense > sum_defense:
                duel.end(constants.DuelState.FINISHED, winner=duel.offense)
            elif sum_offense < sum_defense:
                duel.end(constants.DuelState.FINISHED, winner=duel.defense)
            else:
                duel.end(constants.DuelState.DRAWN, winner=duel.defense)
            if duel.winner.num_victory == constants.REQUIRED_WIN:
                self.end(constants.GameResult.FINISHED, winner=duel.winner)
                message = "{0} wins!\nThe game has ended as {0} first scored {1} points.".format(
                    duel.winner.name, constants.REQUIRED_WIN)
                duration = constants.DELAY_AFTER_GAME_ENDS
                return message, duration
            else:
                message = "{} wins and gets a point.\nDuel #{} ended.".format(
                    duel.winner.name, duel.index + 1)
                duration = constants.DELAY_AFTER_DUEL_ENDS
                return message, duration
        return ValueError('Invalid round.')

    def process_offense_deck_choice_input(self, intra_duel_input):
        duel = self.duel_ongoing
        offense = duel.offense
        index = intra_duel_input.pop()
        deck = offense.decks[index]
        if deck.is_undisclosed():
            offense.deck_in_duel = deck
            deck.state = constants.DeckState.IN_DUEL
            offense.deck_in_duel_index = offense.deck_in_duel.index
            message = 'Deck #{} chosen as the offense deck.'.format(index + 1)
        else:
            message = 'Invalid deck choice. Choose an undisclosed deck.'
        duration = constants.DELAY_AFTER_DECK_CHOICE
        return message, duration

    def process_defense_deck_choice_input(self, intra_duel_input):
        index = intra_duel_input.pop()
        duel = self.duel_ongoing
        offense = duel.offense
        defense = duel.defense
        deck = defense.decks[index]
        if deck.is_undisclosed():
            defense.deck_in_duel = deck
            deck.state = constants.DeckState.IN_DUEL
            defense.deck_in_duel_index = defense.deck_in_duel.index
            offense.deck_in_duel.opponent_deck_index = defense.deck_in_duel.index
            defense.deck_in_duel.opponent_deck_index = offense.deck_in_duel.index
            message = 'Deck #{} chosen as the defense deck.'.format(index + 1)
        else:
            message = 'Invalid deck choice. choose an undisclosed deck.'
        duration = constants.DELAY_AFTER_DECK_CHOICE
        return message, duration

    def decide_decks_for_duel(self, is_opponent):
        duel = self.duel_ongoing
        offense, defense = duel.players()
        if is_opponent:
            player = defense
            class_ = DefenseDeckChoiceInput
        else:
            player = offense
            class_ = OffenseDeckChoiceInput
        # Skip choosing deck in the last duel
        if self.duel_index == constants.DECK_PER_PILE - 1:
            deck = player.undisclosed_decks().pop()
        else:
            deck = offense.decide_deck_for_duel(defense.decks, is_opponent)
        return class_(deck.index)

    def end(self, result, winner=None, loser=None):
        self.over = True
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
            if self.loser == self.player_black:
                self.winner = self.player_red
            else:
                self.winner = self.player_black

    def to_json(self):
        return jsonpickle.encode(self)


class DeckRandomizer(object):
    def __init__(self, pile, joker_value_strategy=Thirteen,
                 joker_position_strategy=JokerLast):
        self.pile = pile
        self.joker_value_strategy = joker_value_strategy
        self.joker_position_strategy = joker_position_strategy

    def pop(self):
        random.shuffle(self.pile)
        decks = []
        for j in range(constants.DECK_PER_PILE):
            cards = []
            for k in range(constants.CARD_PER_DECK):
                new_card = self.pile.pop()
                cards.append(new_card)
            self.joker_value_strategy.apply(cards)
            self.joker_position_strategy.apply(cards)
            new_deck = Deck(cards)
            new_deck.delegate().open_up()
            decks.append(new_deck)
        decks.sort(key=lambda x: x.delegate().value)
        for deck in decks:
            deck.index = decks.index(deck)
        return tuple(decks)


class Player(object):
    def __init__(self, name='', deck_in_duel_index=None, num_victory=0,
                 num_shout_die=0, num_shout_done=0, num_shout_draw=0,
                 decks=None, pile=None, key_settings=None,
                 alias=None, recent_action=None):
        self.name = name
        self.deck_in_duel_index = deck_in_duel_index
        self.deck_in_duel = None
        self.num_victory = num_victory
        self.num_shout_die = num_shout_die
        self.num_shout_done = num_shout_done
        self.num_shout_draw = num_shout_draw
        self.decks = decks
        self.pile = pile
        if key_settings is None:
            self.key_settings = {action: '' for action in constants.Action}
        else:
            self.key_settings = key_settings
        self.alias = alias
        self.recent_action = recent_action

    def valid_actions(self, round_):
        actions = [None, constants.Action.DONE]
        if round_ == 1:
            actions.append(constants.Action.DARE)
            if self.num_shout_die < constants.MAX_DIE:  # TODO: too early?
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
        return list([deck for deck in self.decks if deck.is_undisclosed()])

    def take_pile(self, pile):
        if isinstance(pile, RedPile):
            self.pile = pile.cards
            self.alias = constants.PLAYER_RED
        elif isinstance(pile, BlackPile):
            self.pile = pile.cards
            self.alias = constants.PLAYER_BLACK
        else:
            raise ValueError('This is not a pile.')

    def initialize_decks(self, joker_value_strategy, delegate_strategy):
        random.shuffle(self.pile)
        decks = []
        for j in range(constants.DECK_PER_PILE):
            cards = []
            for k in range(constants.CARD_PER_DECK):
                new_card = self.pile.pop()
                cards.append(new_card)
            joker_value_strategy.apply(cards)
            delegate_strategy.apply(cards)
            new_deck = Deck(cards)
            new_deck.delegate().open_up()
            decks.append(new_deck)
        decks.sort(key=lambda x: x.delegate().value)
        for deck in decks:
            deck.index = decks.index(deck)
        self.decks = tuple(decks)

    @abc.abstractmethod
    def set_keys(self, blacklist=None):
        pass

    @abc.abstractmethod
    def decide_delegate(self, cards):
        pass

    @abc.abstractmethod
    def decide_deck_for_duel(self, opponent_decks, is_opponent):
        pass

    def open_next_card(self):
        deck = self.decks[self.deck_in_duel_index]
        if deck.card_to_open_index is None:
            deck.card_to_open_index = 1
        card_to_open = deck.cards[deck.card_to_open_index]
        card_to_open.open_up()
        deck.card_to_open_index += 1
        if deck.card_to_open_index == 3:
            deck.card_to_open_index = None

    def is_done(self):
        values = set()
        for deck in self.decks:
            if not deck.is_undisclosed():
                for card in deck.cards:
                    if card.is_open():
                        values.add(card.value)
        return len(values) == len(constants.Rank)

    def to_array(self):
        decks = [deck.to_array() for deck in self.decks]
        decks = list(itertools.chain.from_iterable(decks))
        num_victory = -1 if self.num_victory is None else self.num_victory
        num_shout_die = -1 if self.num_shout_die is None else self.num_shout_die
        deck_in_duel_index = -1 if self.deck_in_duel_index is None else self.deck_in_duel_index
        others = [num_victory, num_shout_die, deck_in_duel_index]
        return numpy.array(decks + others)

    @classmethod
    def from_array(cls, array):
        decks_array = numpy.array(array[0:9 * 19])
        decks_reshaped = decks_array.reshape(9, -1)
        decks = list(
            [Deck.from_array(deck_array) for deck_array in decks_reshaped])
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
        self.name = NameTextInput.from_human(prompt, forbidden_name).pop()

    def set_keys(self, blacklist=None):
        if blacklist is None:
            blacklist = []
        print('\n{}, decide the set of keys you will use.'.format(self.name))
        for action in self.key_settings:
            prompt = '{}, which key will you use to indicate {}? '.format(
                self.name, action.name)
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
                    self.name, action.name)
                key = input(prompt)
                is_single = len(key) == 1
                is_lower = key.islower()
                is_not_duplicate = key not in blacklist
                is_valid_key = is_single and is_lower and is_not_duplicate
            self.key_settings[action] = key
            blacklist.append(key)

    def decide_delegate(self, cards):
        JokerAnywhere.apply(cards)
        return tuple(cards)

    def decide_deck_for_duel(self, opponent_decks, is_opponent):
        decks = opponent_decks if is_opponent else self.decks
        undisclosed_decks = [deck for deck in decks if deck.is_undisclosed()]
        return DeckTextInput.from_human(self.name, is_opponent,
                                        undisclosed_decks).pop()

    def shout(self, round_):
        allowed_actions = self.valid_actions(round_)
        keys_settings_in_list = list(
            ['{}: \'{}\''.format(action.name, key) for action, key in
             self.key_settings.items() if action in allowed_actions])
        do_nothing = 'Pass: \'Enter\''
        keys_settings_in_list.append(do_nothing)
        keys_settings_in_str = ', '.join(keys_settings_in_list)
        prompt = '{}, what will you do? ({})'.format(self.name,
                                                     keys_settings_in_str)
        shout_input = input(prompt)
        key_to_action = dict(
            {key: action for action, key in self.key_settings.items()})
        action = key_to_action.get(shout_input)
        return Shout(self, action)


class ComputerPlayer(Player):
    def __init__(self, forbidden_name=''):
        super().__init__()
        self.name = NameTextInput.auto_generate(forbidden_name).pop()

    def set_keys(self, blacklist=None):
        if self.alias == constants.PLAYER_RED:
            self.key_settings = {constants.Action.DARE: 'z',
                                 constants.Action.DIE: 'x',
                                 constants.Action.DONE: 'c',
                                 constants.Action.DRAW: 'v'}
        else:
            self.key_settings = {constants.Action.DARE: 'u',
                                 constants.Action.DIE: 'i',
                                 constants.Action.DONE: 'o',
                                 constants.Action.DRAW: 'p'}

    @abc.abstractmethod
    def decide_delegate(self, cards):
        pass

    @abc.abstractmethod
    def decide_deck_for_duel(self, opponent_decks, is_opponent):
        pass

    @staticmethod
    def get_chances(decks_me, delegate_me, decks_opponent, delegate_opponent,
                    num_open):
        """get chances of winning, tying, losing, and unknown.
        :return: a 4-tuple containing the chances of winning, tying, losing, and unknown
        """
        # get the value of my delegate and the opponent's
        hidden_cards_me = []
        for deck in decks_me:
            for card in deck.cards:
                if not card.is_open() and card.value <= delegate_me.value:
                    hidden_cards_me.append(card)
        opponent_hidden_cards = []
        for deck in decks_opponent:
            for card in deck.cards:
                if not card.is_open() and card.value <= delegate_opponent.value:
                    opponent_hidden_cards.append(card)

        # calculate the odds that you will lose the duel
        win, lose, draw, unknown = 0, 0, 0, 0
        candidates_me = itertools.combinations(hidden_cards_me, num_open)
        opponent_candidates = itertools.combinations(opponent_hidden_cards,
                                                     num_open)
        for cards_me in candidates_me:
            for opponent_cards in opponent_candidates:
                sum_me = sum([card.value for card in cards_me])
                opponent_sum = sum([card.value for card in opponent_cards])
                # joker may still be hidden
                if any([card.suit is None for card in cards_me]) or any(
                        [card.suit is None for card in opponent_cards]):
                    unknown += 1
                elif sum_me > opponent_sum:
                    win += 1
                elif sum_me == opponent_sum:
                    draw += 1
                elif sum_me < opponent_sum:
                    lose += 1
                else:
                    raise Exception('Something is wrong.')
        num_candidates_me = sum(1 for candidate in candidates_me)
        num_candidates_opponent = sum(1 for candidate in opponent_candidates)
        total = num_candidates_me * num_candidates_opponent
        odds_win = round(win / total, 3)
        odds_draw = round(draw / total, 3)
        odds_lose = round(lose / total, 3)
        odds_unknown = round(unknown / total, 3)
        return odds_win, odds_draw, odds_lose, odds_unknown

    @staticmethod
    def get_smallest_undisclosed_deck(decks):
        return min([deck for deck in decks if deck.is_undisclosed()],
                   key=lambda x: x.index)

    @staticmethod
    def undisclosed_values(decks):
        values = []
        for deck in decks:
            for card in deck.cards:
                if deck.is_undisclosed() or not card.is_open():
                    values.append(card.value)
        return tuple(set(values))

    @staticmethod
    def opened_values(decks):
        values = []
        for deck in decks:
            for card in deck.cards:
                if not deck.is_undisclosed() and card.is_open():
                    values.append(card.value)
        return tuple(set(values))

    @abc.abstractmethod
    def shout(self, round_):
        pass


class DumbComputerPlayer(ComputerPlayer):
    def decide_delegate(self, cards):
        JokerFirst.apply(cards)
        return cards

    def decide_deck_for_duel(self, opponent_decks, is_opponent):
        if is_opponent:
            undisclosed_decks = [deck for deck in opponent_decks if
                                 deck.is_undisclosed()]
            return min(undisclosed_decks, key=lambda x: x.index)
        else:
            undisclosed_decks = [deck for deck in self.decks if
                                 deck.is_undisclosed()]
            return max(undisclosed_decks, key=lambda x: x.index)

    def shout(self, round_):
        allowed_actions = self.valid_actions(round_)
        random_action = random.choice(allowed_actions)
        return Shout(self, random_action)


class Card(object):
    def __init__(self, suit, colored, rank, value=None, open_=False):
        self.suit = suit
        self.colored = colored
        self.rank = rank
        self.value = value
        self.open_ = open_

    def __eq__(self, other):
        same_suit = self.suit == other.suit
        same_color = self.colored == other.colored
        same_value = self.value == other.value
        return same_suit and same_color and same_value

    def __repr__(self):
        if self.is_open():
            if self.suit is None:
                return '{} {}'.format(self.value, '★' if self.colored else '☆')
            else:
                return '{} {}'.format(self.value, self.suit.name[0])
        else:
            return '?'

    def open_up(self):
        self.open_ = True

    def is_open(self):
        return self.open_

    def is_joker(self):
        return self.suit is None

    def to_array(self):
        suit = -1 if self.suit is None else self.suit.value
        colored = -1 if self.colored is None else int(self.colored)
        rank = -1 if self.rank is None else constants.Rank[self.rank].value
        value = -1 if self.value is None else self.value
        open_ = -1 if self.open_ is None else int(self.open_)
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
        self.state = state
        self.cards = cards
        self.index = index  # zero based
        self.opponent_deck_index = opponent_deck_index
        self.card_to_open_index = card_to_open_index

    def __repr__(self):
        return ' / '.join([repr(card) for card in self.cards])

    def delegate(self):
        return self.cards[0]

    def is_undisclosed(self):
        return self.state == constants.DeckState.UNDISCLOSED

    def is_in_duel(self):
        return self.state == constants.DeckState.IN_DUEL

    def to_array(self):
        if self.cards is None:
            cards_flattened = []
        else:
            cards_generator = [card.to_array() for card in self.cards]
            cards = numpy.array(cards_generator)
            cards_flattened = cards.flatten()
        state = -1 if self.state is None else self.state.value
        index = -1 if self.index is None else self.index
        if self.opponent_deck_index is None:
            opponent_deck_index = -1
        else:
            opponent_deck_index = self.opponent_deck_index
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
            cards = list([Card.from_array(card_array) for card_array in cards])
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
        self.index = index
        if time_started is None:
            self.time_started = time.time()
        else:
            self.time_started = time_started
        self.round_ = round_
        self.over = over
        self.time_ended = time_ended
        self.winner = winner
        self.loser = loser
        self.state = state
        if offense is None:
            if self.index % 2 == 0:
                self.offense = self.player_red
            else:
                self.offense = self.player_black
        else:
            self.offense = offense
        if defense is None:
            if self.index % 2 == 0:
                self.defense = self.player_black
            else:
                self.defense = self.player_red
        else:
            self.defense = defense

    def players(self):
        return self.offense, self.defense

    def is_drawn(self):
        sum_offense = sum(
            card.value for card in self.offense.deck_in_duel.cards)
        sum_defense = sum(
            card.value for card in self.defense.deck_in_duel.cards)
        return sum_offense == sum_defense

    def is_over(self):
        return self.over

    def end(self, state, winner=None, loser=None):
        self.over = True
        self.time_ended = time.time()
        self.state = state
        if state.value not in range(3, 10):
            raise ValueError('Invalid DeckState.')
        self.winner = winner
        self.loser = loser
        if self.winner is None and self.loser is None:
            if state not in [constants.DuelState.DIED,
                             constants.DuelState.ABORTED_BY_CORRECT_DONE]:
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
        for player in self.players():
            player.deck_in_duel.state = constants.DeckState.FINISHED
            for card in player.deck_in_duel.cards:
                card.open_up()
            player.deck_in_duel = None


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
    def __init__(self):
        self.cards = None

    def pop(self):
        return self.cards


class RedPile(Pile):
    def __init__(self):
        super().__init__()
        red_joker = Card(None, True, constants.JOKER, None, False)
        cards = [red_joker]
        for suit in constants.RED_SUITS:
            for rank in constants.Rank:
                card = Card(suit, True, rank.name, rank.value, False)
                cards.append(card)
        self.cards = cards


class BlackPile(Pile):
    def __init__(self):
        super().__init__()
        black_joker = Card(None, False, constants.JOKER, None, False)
        cards = [black_joker]
        for suit in constants.BLACK_SUITS:
            for rank in constants.Rank:
                card = Card(suit, False, rank.name, rank.value, False)
                cards.append(card)
        self.cards = cards


class OutputHandler(object):
    def __init__(self):
        self.states = []
        self.messages = []

    def display(self, game_state_in_json=None, message='', duration=0):
        print('{:-^135}'.format(str()))
        self.states.append(game_state_in_json)
        self.messages.append(message)
        if game_state_in_json is None:
            if message:
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
        red_numbers = [('< #{} >' if deck.is_in_duel() else '#{}').format(
            deck.index + 1) for deck in red_decks]
        red_number_line = row_format.format(*red_numbers)
        print(red_number_line)
        red_undisclosed_delegates = [
            repr(deck.cards[0]) if deck.is_undisclosed() else '' for deck in
            red_decks]
        print(row_format.format(*red_undisclosed_delegates))
        red_opened_delegates = [
            '' if deck.is_undisclosed() else repr(deck.cards[0]) for deck in
            red_decks]
        print(row_format.format(*red_opened_delegates))
        red_seconds = ['' if deck.is_undisclosed() else repr(deck.cards[1]) for
                       deck in red_decks]
        print(row_format.format(*red_seconds))
        red_lasts = ['' if deck.is_undisclosed() else repr(deck.cards[2]) for
                     deck in red_decks]
        print(row_format.format(*red_lasts))
        print()
        print('{:^135}'.format(
            '' if duel is None else '[Duel #{}]'.format(duel.index + 1)))
        print()
        black_decks = game.player_black.decks
        black_lasts = ['' if deck.is_undisclosed() else repr(deck.cards[2]) for
                       deck in black_decks]
        print(row_format.format(*black_lasts))
        black_seconds = ['' if deck.is_undisclosed() else repr(deck.cards[1])
                         for deck in black_decks]
        print(row_format.format(*black_seconds))
        black_opened_delegates = [
            '' if deck.is_undisclosed() else repr(deck.cards[0]) for
            deck in black_decks]
        print(row_format.format(*black_opened_delegates))
        black_undisclosed_delegate = [
            repr(deck.cards[0]) if deck.is_undisclosed() else '' for
            deck in black_decks]
        print(row_format.format(*black_undisclosed_delegate))
        black_numbers = [
            '< #{} >'.format(
                deck.index + 1) if deck.is_in_duel() else '#{}'.format(
                deck.index + 1) for deck in black_decks]
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

    def export_to_json(self, last_game_state_in_json=None):
        if last_game_state_in_json is None:
            last_game_state_in_json = self.states[-1]
        last_game = jsonpickle.decode(last_game_state_in_json)
        red_class = last_game.player_red.__class__.__name__
        red_name = last_game.player_red.name
        black_class = last_game.player_black.__class__.__name__
        black_name = last_game.player_black.name
        time_started_str = last_game.time_started
        time_started_float = float(time_started_str)
        datetime_started = datetime.datetime.fromtimestamp(time_started_float)
        datetime_str = datetime.datetime.strftime(datetime_started,
                                                  '%Y%m%d%H%M%S')
        file_name = '{}({}){}({}){}.json'.format(red_class, red_name,
                                                 black_class, black_name,
                                                 datetime_str)
        content = jsonpickle.encode(self.states)
        with open(file_name, 'w') as file:
            file.write(content)

    def import_from_json(self, file_name):
        with open(file_name) as file:
            content = file.read()
            self.states = jsonpickle.decode(content)


if __name__ == '__main__':
    pass
