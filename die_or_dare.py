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
                print("You can't use {}. Choose another name.".format(forbidden_name))
            else:
                print("Only alphanumeric characters are allowed for the player's name.")
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
        all_actions_set = all([self.key_settings.get(action) is not None for action in constants.Action])
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
        key_settings = {constants.Action.DARE: '', constants.Action.DIE: '', constants.Action.DONE: '',
                        constants.Action.DRAW: ''}
        blacklist = blacklist or []
        print('\n{}, decide the set of keys you will use.'.format(player_name))
        for action in key_settings:
            key = input('{}, which key will you use to indicate {}? '.format(player_name, action.name))
            is_valid_key = len(key) == 1 and key.islower() and key not in blacklist
            while not is_valid_key:
                if key in blacklist:
                    print("You can't use the following key(s): {}".format(', '.join(blacklist)))
                else:
                    print('Use a single lowercase alphabet.')
                key = input('{}, which key will you use to indicate {}? '.format(player_name, action.name))
                is_valid_key = len(key) == 1 and key.islower() and key not in blacklist
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
                card.value = constants.HIGHEST_VALUE
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
                card.value = random.randint(1, constants.HIGHEST_VALUE)
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
            cards_without_joker = [card for card in cards if not card.is_joker()]
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
            cards_without_joker = [card for card in cards if not card.is_joker()]
            non_joker_bigger = max(cards_without_joker, key=lambda x: x.value)
            non_joker_bigger_index = cards.index(non_joker_bigger)
            if joker.value <= non_joker_bigger.value:
                cards[0], cards[non_joker_bigger_index] = cards[non_joker_bigger_index], cards[0]
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
        return issubclass(self.strategy, JokerValueStrategy) and not issubclass(JokerValueStrategy, self.strategy)

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
            print('\n{}, enter the number corresponding to the strategy you want.'.format(player_name))
            print('Press 1 to set the value of Joker to 13.')
            print('Press 2 to set the value of Joker to be equal to the biggest value in the deck.')
            print('Press 3 to set the value of Joker to be a random number.')
            input_value = input('What is your choice? ')
            try:
                input_value = int(input_value)
                assert number_to_strategy.get(input_value) is not None
            except (ValueError, AssertionError):
                print('Invalid input.')
            else:
                valid_input = True
        return cls(number_to_strategy.get(input_value))


class JokerPositionStrategyInput(Input):
    def __init__(self, strategy=None):
        self.strategy = strategy

    def is_valid(self):
        return issubclass(self.strategy, JokerPositionStrategy) and not issubclass(JokerPositionStrategy, self.strategy)

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
            print('\n{}, enter the number corresponding to the strategy you want.'.format(player_name))
            print('Enter 1 to reveal the joker as soon as possible.')
            print('Enter 2 to hide the joker as long as possible.')
            print('Enter 3 to put joker anywhere.')
            input_value = input('What is your choice? ')
            try:
                input_value = int(input_value)
                assert number_to_strategy.get(input_value) is not None
            except (ValueError, AssertionError):
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
    def from_human(cls, player_name=None, is_opponent=None, undisclosed_decks=None):
        user_input_to_deck = dict({deck.index: deck for deck in undisclosed_decks})
        valid_input = False
        input_value = None
        possessive = "your opponent's" if is_opponent else 'your'
        prompt = '{}, choose one of {} deck (Enter the deck number): '.format(player_name, possessive)
        while not valid_input:
            input_value = input(prompt)
            try:
                input_value = int(input_value) - 1
                assert user_input_to_deck.get(input_value) is not None
            except (ValueError, AssertionError):
                print('Invalid input. Enter a number among {}.'.format(
                    ', '.join([str(deck.index + 1) for deck in undisclosed_decks])))
            else:
                valid_input = True
        return cls(user_input_to_deck.get(input_value))


class DeckChoiceInput(Input):
    def __init__(self, offense_deck, defense_deck):
        self.offense_deck = offense_deck
        self.defense_deck = defense_deck

    def is_valid(self, *args, **kwargs):
        pass

    def pop(self):
        return self.offense_deck, self.defense_deck


class ActionInput(Input):
    def __init__(self, shouts):
        self.keys_pressed = shouts

    def is_valid(self, *args, **kwargs):
        pass

    def pop(self):
        pass


class IgnoredInput(Input):
    def is_valid(self, *args, **kwargs):
        pass

    def pop(self):
        pass


class Shout(object):
    def __init__(self, player, action):
        self.player = player
        self.action = action


class ActionKeypressInput(ActionInput):
    def __init__(self, keys_pressed):
        self.keys_pressed = keys_pressed

    @classmethod
    def from_human(cls, keys_to_hook=None, timeout=0):
        def when_key_pressed(x):
            keys_pressed.append(x.namme)
            keyboard.unhook(x.name)

        keys_pressed = []
        keys_to_hook = [] if keys_to_hook is None else keys_to_hook
        for key in keys_to_hook:
            keyboard.on_press_key(key, lambda x: when_key_pressed(x))
        over = False
        start = time.time()
        while not over:
            # TODO: exit immediately if non-dare action or double dare is found
            over = time.time() - start > timeout
        keyboard.unhook_all()
        return cls(''.join([keyboard_event.name for keyboard_event in keys_pressed]))

    def is_valid(self, *args, **kwargs):
        pass

    def pop(self):
        return self.keys_pressed


class PlayerOrder(abc.ABC):
    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2
        self.first = None
        self.second = None

    def pop(self):
        for player in [self.first, self.second]:
            if player.__class__ == Player or not issubclass(type(player), Player):
                raise NotImplementedError()
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
    def __init__(self, player_red=None, player_black=None, over=False, time_started=None, time_ended=None,
                 winner=None, loser=None, result=None, duels=None, *args):
        self.player_red = player_red  # takes the red pile and gets to go first
        self.player_black = player_black
        self.over = over
        self.time_started = time_started or time.time()
        self.time_ended = time_ended
        self.winner = winner
        self.loser = loser
        self.result = result
        self.duel_index = -1  # zero based
        if duels is None:
            duels = []
            for i in range(constants.DECK_PER_PILE):
                if i % 2 == 0:
                    new_duel = Duel(player_red, player_black, i)
                else:
                    new_duel = Duel(player_black, player_red, i)
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
        self.valid_actions = {1: (constants.Action.DONE,),
                              2: (constants.Action.DONE, constants.Action.DIE, constants.Action.DARE),
                              3: (constants.Action.DONE, constants.Action.DRAW), }
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
            human_player1_prompt = 'Player 1, enter your name: '
            forbidden_name = player1.name
            player2 = HumanPlayer(human_player1_prompt, forbidden_name)
        else:
            human_player1_prompt = 'Player 1, enter your name: '
            player1 = HumanPlayer(human_player1_prompt)
            human_player2_prompt = 'Player 2, enter your name: '
            forbidden_name = player1.name
            player2 = HumanPlayer(human_player2_prompt, forbidden_name)
        print("\nAll right, {} and {}. Let's get started!".format(player1.name, player2.name))
        print("Let's flip a coin to decide who will be the Player Red!")
        self.player_red, self.player_black = RandomPlayerOrder(player1, player2).pop()
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

    def open_next_cards(self):
        if self.is_over():
            print("\nLet's open the last cards anyway.\n")
        else:
            print("Cards will be opened in {} seconds!\n".format(constants.DELAY_BEFORE_CARD_OPEN))
            time.sleep(constants.DELAY_BEFORE_CARD_OPEN)
        for player in self.players():
            player.open_next_card()

    def to_next_duel(self):
        self.duel_index += 1
        self.duel_ongoing = self.duels[self.duel_index]
        return self.duel_ongoing

    def is_over(self):
        return self.over

    def prepare(self):
        duel = self.duel_ongoing
        duel.to_next_round()
        if duel.round_ == 0:
            duel.start()
        elif duel.round_ == 1:
            pass  # delegate is always open
        elif duel.round_ == 2:
            self.open_next_cards()
        elif duel.round_ == 3:
            self.open_next_cards()
        return '', constants.DELAY_AFTER_DUEL_ENDS

    def accept(self):
        duel_round = self.duel_ongoing.round_
        if duel_round == 0:
            return self.decide_decks_for_duel()
        else:
            if duel_round in range(1, 4):
                valid_actions = self.valid_actions.get(duel_round)
                return self.get_actions(valid_actions)
            else:
                raise ValueError()

    def get_actions(self, valid_actions, timeout=0):
        keys = ''
        for player in self.players():
            if player.num_shout_die < constants.MAX_DIE and constants.Action.DIE in valid_actions:
                key = player.key_settings.get(constants.Action.DIE)
                keys += key
            if player.num_shout_done < constants.MAX_DONE and constants.Action.DONE in valid_actions:
                key = player.key_settings.get(constants.Action.DONE)
                keys += key
            if player.num_shout_draw < constants.MAX_DRAW and constants.Action.DRAW in valid_actions:
                key = player.key_settings.get(constants.Action.DRAW)
                keys += key
        return ActionKeypressInput.from_human(keys, timeout)

    def process(self, intra_duel_input):
        duel = self.duel_ongoing
        if isinstance(intra_duel_input, DeckChoiceInput):
            return self.process_deck_choice_input(intra_duel_input)
        elif isinstance(intra_duel_input, ActionInput):  # TODO: extract method
            # See who did which action
            shouts = []
            valid_actions = self.valid_actions.get(duel.round_)
            keys_pressed = intra_duel_input.pop()
            for player in self.players():
                # Note: `key` is not the key as in key-value pair.
                key_to_action = dict({key: action for action, key in player.key_settings.items()})
                for key in keys_pressed:
                    action = key_to_action.get(key)
                    if action in valid_actions:
                        shout = Shout(player, action)
                        shouts.append(shout)

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

            # priority: done > die , draw > dare (offense > defense if not specified)
            if constants.Action.DONE in valid_actions:
                for player in duel.players():
                    if player.recent_action == constants.Action.DONE:
                        player.num_shout_done += 1
                        if player.is_done():  # correct done
                            duel.end(constants.DuelState.ABORTED_BY_CORRECT_DONE, player)
                            self.end(constants.GameResult.DONE, winner=player)
                            message = "Duel #{0}: {1} is done, so this duel is aborted.\n{1} wins! The game has ended as {1} first shouted done correctly.".format(
                                duel.index + 1, player.name)
                            duration = constants.DELAY_AFTER_GAME_ENDS
                            return message, duration
            if constants.Action.DIE in valid_actions:
                for player in duel.players():
                    if player.recent_action == constants.Action.DIE:
                        player.num_shout_die += 1
                        duel.end(constants.DuelState.DIED, player)
                        message = "Duel #{}: {} died, so no one gets a point.".format(duel.index + 1, player.name)
                        duration = constants.DELAY_AFTER_DUEL_ENDS
                        return message, duration
            if constants.Action.DRAW in valid_actions:
                for player in duel.players():
                    if player.recent_action == constants.Action.DRAW:
                        # TODO: automate done and draw for non human
                        player.num_shout_draw += 1
                        if duel.is_drawn():  # correct draw
                            duel.end(constants.DuelState.DRAWN, player)
                            message = "Duel #{}: The sums are equal, but no one shouted draw, so the defense ({}) gets a point.".format(
                                self.duel_index + 1, self.winner.name)
                            duration = constants.DELAY_AFTER_DUEL_ENDS
                            return message, duration
            # TODO effectively a double dare (modify the else statement below)
            # if all inputs are invalid, if last round...
            #      message += 'All right. No actions.'
            #      if not last round:
            #          message += '\nNo action counts as a dare'
            # else:
            #     message += "Ooh, double dare! Let's open the next cards."
            # something like self.end(constants.DuelState.DRAWN, winner=self.defense)
            if constants.Action.DARE in valid_actions:
                if all(player.just_shouted_dare() for player in self.players()):
                    # TODO: if all cards open:
                    message = "Ooh, double dare! Let's open the next cards."
                    duration = constants.DELAY_BEFORE_CARD_OPEN
                    return message, duration
            else:
                if all([card.is_open() for card in duel.offense.deck_in_duel.cards]):
                    sum_offense = sum([card.value for card in duel.offense.deck_in_duel.cards])
                    sum_defense = sum([card.value for card in duel.defense.deck_in_duel.cards])
                    if sum_offense > sum_defense:
                        duel.end(constants.DuelState.FINISHED, winner=duel.offense)
                    elif sum_offense < sum_defense:
                        duel.end(constants.DuelState.FINISHED, winner=duel.defense)
                    else:
                        duel.end(constants.DuelState.DRAWN, winner=duel.defense)
                    if duel.winner.num_victory == constants.REQUIRED_WIN:
                        self.end(constants.GameResult.FINISHED, winner=duel.winner)
                        message = "{0} wins! The game has ended as {0} first scored {1} points.".format(
                            self.winner.name, constants.REQUIRED_WIN)
                        duration = 0
                        return message, duration
            message = ''
            duration = constants.DELAY_BEFORE_CARD_OPEN
            # do nothing and move on to next rou d to open next cards
            return message, duration
        else:
            return ValueError('Invalid input')

    def process_deck_choice_input(self, intra_duel_input):
        offense = self.duel_ongoing.offense
        defense = self.duel_ongoing.defense
        offense.deck_in_duel, defense.deck_in_duel = intra_duel_input.pop()

        offense.deck_in_duel_index = offense.deck_in_duel.index
        defense.deck_in_duel_index = offense.deck_in_duel.index

        offense.deck_in_duel.state = constants.DeckState.IN_DUEL
        defense.deck_in_duel.state = constants.DeckState.IN_DUEL

        offense.deck_in_duel.opponent_deck_index = defense.deck_in_duel.index
        defense.deck_in_duel.opponent_deck_index = offense.deck_in_duel.index
        message = 'The two decks have been chosen.'
        duration = 3
        return message, duration

    def decide_decks_for_duel(self):
        duel = self.duel_ongoing
        # Skip choosing deck in the last duel
        if self.duel_index == constants.DECK_PER_PILE - 1:
            offense_deck = duel.offense.undisclosed_decks().pop()
            defense_deck = duel.defense.undisclosed_decks().pop()
        else:
            offense_deck, defense_deck = duel.offense.decide_decks_for_duel(duel.defense.decks)
        return DeckChoiceInput(offense_deck, defense_deck)

    def cleanup_duel(self):
        duel_state = self.duel_ongoing.state
        # identify why the duel ended
        if duel_state in [constants.DuelState.DRAWN, constants.DuelState.FINISHED]:
            for player in self.players():
                if player.num_victory == constants.REQUIRED_WIN:
                    self.end(constants.GameResult.FINISHED, winner=player)
                    print("{0} wins! The game has ended as {0} first scored {1} points.".format(player.name,
                                                                                                constants.REQUIRED_WIN))
                    break
        elif duel_state == constants.DuelState.ABORTED_BY_CORRECT_DONE:
            self.end(constants.GameResult.DONE, winner=self.duel_ongoing.player_shouted)
            print("{0} wins! The game has ended as {0} first shouted done correctly.".format(self.winner.name))
        elif duel_state == constants.DuelState.ABORTED_BY_WRONG_DONE:
            self.end(constants.GameResult.FORFEITED_BY_WRONG_DONE, loser=self.duel_ongoing.player_shouted)
            print("{} wins! The game has ended as {} shouted done wrong.".format(self.winner.name, self.loser.name))
        elif duel_state == constants.DuelState.ABORTED_BY_WRONG_DRAW:
            self.end(constants.GameResult.FORFEITED_BY_WRONG_DRAW, loser=self.duel_ongoing.player_shouted)
            print("{} wins! The game has ended as {} shouted draw wrong.".format(self.winner.name, self.loser.name))

        # cleanup
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

    def to_json(self):
        return jsonpickle.encode(self)


class RoundInput(Input):
    def __init__(self, round_):
        self.round_ = round_

    def is_valid(self, *args, **kwargs):
        return self.round_ in 1, 2, 3

    @abc.abstractmethod
    def pop(self):
        pass


class DeckRandomizer(object):
    def __init__(self, pile, joker_value_strategy=Thirteen, joker_location_strategy=JokerLast):
        self.pile = pile
        self.joker_value_strategy = joker_value_strategy
        self.joker_location_strategy = joker_location_strategy

    def pop(self):
        random.shuffle(self.pile)
        decks = []
        for j in range(constants.DECK_PER_PILE):
            cards = []
            for k in range(constants.CARD_PER_DECK):
                cards.append(self.pile.pop())
            self.joker_value_strategy.apply(cards)
            self.joker_location_strategy.apply(cards)
            new_deck = Deck(cards)
            new_deck.delegate().open_up()
            decks.append(new_deck)
        decks.sort(key=lambda x: x.delegate().value)
        for deck in decks:
            deck.index = decks.index(deck)
        return tuple(decks)


class Player(object):
    def __init__(self, name='', deck_in_duel_index=None, num_victory=0, num_shout_die=0, num_shout_done=0,
                 num_shout_draw=0, decks=None, pile=None, key_settings=None, alias=None, recent_action=None):
        self.name = name
        self.deck_in_duel_index = deck_in_duel_index
        self.deck_in_duel = None
        self.num_victory = num_victory
        self.num_shout_die = num_shout_die
        self.num_shout_done = num_shout_done
        self.num_shout_draw = num_shout_draw
        self.decks = decks
        self.pile = pile
        self.key_settings = key_settings or {action: '' for action in constants.Action}
        self.alias = alias
        self.recent_action = recent_action

    def undisclosed_decks(self):
        return list([deck for deck in self.decks if deck.is_undisclosed()])

    def initialize_decks(self, joker_value_strategy, delegate_strategy):
        random.shuffle(self.pile)
        decks = []
        for j in range(constants.DECK_PER_PILE):
            cards = []
            for k in range(constants.CARD_PER_DECK):
                cards.append(self.pile.pop())
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
    def decide_decks_for_duel(self, opponent_decks):
        pass

    def open_next_card(self):
        deck = self.decks[self.deck_in_duel_index]
        card_to_open = deck.cards[deck.card_to_open_index]
        card_to_open.open_up()
        if deck.card_to_open_index == 1:
            deck.card_to_open_index += 1
        elif deck.card_to_open_index == 2:
            deck.card_to_open_index = None

    def is_done(self):
        values = {}
        for deck in self.decks:
            if deck.state != constants.DeckState.UNDISCLOSED:
                for card in deck.cards:
                    if card.is_open():
                        values.add(card.value)
        return len(values) == constants.NUM_CARD

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
        decks = list(Deck.from_array(deck_array) for deck_array in decks_reshaped)
        num_victory = None if array[9 * 19] == -1 else array[9 * 19]
        num_shout_die = None if array[9 * 19 + 1] == -1 else array[9 * 19 + 1]
        deck_in_duel_index = None if array[9 * 19 + 2] == -1 else array[9 * 19 + 2]
        return cls(decks=decks, num_victory=num_victory, num_shout_die=num_shout_die,
                   deck_in_duel_index=deck_in_duel_index)


class HumanPlayer(Player):
    def __init__(self, prompt, forbidden_name=''):
        super().__init__()
        self.name = NameTextInput.from_human(prompt, forbidden_name).pop()

    def set_keys(self, blacklist=None):
        blacklist = blacklist or []
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
        my_undisclosed_decks = self.undisclosed_decks()
        offense_deck = DeckTextInput.from_human(self.name, False, my_undisclosed_decks).pop()

        # Display chance of winning
        # print('The chance of winning/tying/losing/unknown for each deck is:')
        # for opponent_deck in opponent_decks:
        #     if opponent_deck.is_undisclosed():
        #         my_delegate = offense_deck.delegate()
        #         opponent_delegate = opponent_deck.delegate()
        #         print('Deck #{}: {} - {}'.format(opponent_deck.index + 1, opponent_deck.delegate(),
        #                                          ComputerPlayer.get_chances(self.decks, my_delegate, opponent_decks,
        #                                                                     opponent_delegate, 2)))

        # Choose defense deck
        opponent_undisclosed_decks = [deck for deck in opponent_decks if deck.is_undisclosed()]
        defense_deck = DeckTextInput.from_human(self.name, True, opponent_undisclosed_decks).pop()
        return offense_deck, defense_deck


class ComputerPlayer(Player):
    def __init__(self, forbidden_name=''):
        super().__init__()
        self.name = NameTextInput.auto_generate(forbidden_name).pop()

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
    def get_chances(my_decks, my_delegate, opponent_decks, opponent_delegate, num_open):
        """get chances of winning, tying, losing, and unknown.
        :return: a 4-tuple containing the chances of winning, tying, losing, and unknown
        """
        # get the value of my delegate and the opponent's
        my_hidden_cards = []
        for deck in my_decks:
            for card in deck.cards:
                if not card.is_open() and card.value <= my_delegate.value:
                    my_hidden_cards.append(card)
        opponent_hidden_cards = []
        for deck in opponent_decks:
            for card in deck.cards:
                if not card.is_open() and card.value <= opponent_delegate.value:
                    opponent_hidden_cards.append(card)

        # calculate the odds that you will lose the duel
        win, lose, draw, unknown = 0, 0, 0, 0
        my_candidates = list(itertools.combinations(my_hidden_cards, num_open))
        opponent_candidates = list(itertools.combinations(opponent_hidden_cards, num_open))
        for my_cards in my_candidates:
            for opponent_cards in opponent_candidates:
                # joker may still be hidden
                if any([card.suit is None for card in my_cards]) or any([card.suit is None for card in opponent_cards]):
                    unknown += 1
                elif sum([card.value for card in my_cards]) > sum([card.value for card in opponent_cards]):
                    win += 1
                elif sum([card.value for card in my_cards]) == sum([card.value for card in opponent_cards]):
                    draw += 1
                elif sum([card.value for card in my_cards]) < sum([card.value for card in opponent_cards]):
                    lose += 1
                else:
                    raise Exception('Something is wrong.')
        total = len(my_candidates) * len(opponent_candidates)
        odds_win = round(win / total, 3)
        odds_draw = round(draw / total, 3)
        odds_lose = round(lose / total, 3)
        odds_unknown = round(unknown / total, 3)
        return odds_win, odds_draw, odds_lose, odds_unknown

    @staticmethod
    def get_smallest_undisclosed_deck(decks):
        return min([deck for deck in decks if deck.is_undisclosed()], key=lambda x: x.index)

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
        my_min_deck = self.get_smallest_undisclosed_deck(self.decks)
        opponent_min_deck = self.get_smallest_undisclosed_deck(opponent_decks)
        return my_min_deck, opponent_min_deck


class Card(object):
    def __init__(self, suit, colored, rank, value=None, open_=False):
        self.suit = suit
        self.colored = colored
        self.rank = rank
        self.value = value
        self.open_ = open_

    def __eq__(self, other):
        return self.suit == other.suit and self.colored == other.colored and self.value == other.value

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
    def __init__(self, cards, state=constants.DeckState.UNDISCLOSED, index=None, opponent_deck_index=None,
                 card_to_open_index=1):
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
        cards = [] if self.cards is None else numpy.array([card.to_array() for card in self.cards]).flatten()
        state = -1 if self.state is None else self.state.value
        index = -1 if self.index is None else self.index
        opponent_deck_index = -1 if self.opponent_deck_index is None else self.opponent_deck_index
        card_to_open_index = -1 if self.card_to_open_index is None else self.card_to_open_index
        list_ = [*cards, state, index, opponent_deck_index, card_to_open_index]
        return numpy.array(list_)

    @classmethod
    def from_array(cls, array):
        cards = [array[0:5], array[5:10], array[10:15]]
        state = array[15]
        index = array[16]
        opponent_deck_index = array[17]
        card_to_open_index = array[18]
        cards_flattened = numpy.array(cards).flatten()
        if cards_flattened == []:
            cards = None
        else:
            cards = list([Card.from_array(card_array) for card_array in cards])
        state = None if state == -1 else constants.DeckState(state)
        index = None if index == -1 else index
        opponent_deck_index = None if opponent_deck_index == -1 else opponent_deck_index
        card_to_open_index = None if card_to_open_index == -1 else card_to_open_index
        return cls(cards, state, index, opponent_deck_index, card_to_open_index)


class Duel(object):
    def __init__(self, player_red, player_black, index, time_started=None, round_=-1, over=False, time_ended=None,
                 player_shouted=None, winner=None, loser=None, state=constants.DuelState.UNSTARTED, offense=None,
                 defense=None):
        self.player_red = player_red
        self.player_black = player_black
        self.index = index
        self.time_started = time_started or time.time()
        self.round_ = round_
        self.over = over
        self.time_ended = time_ended
        self.player_shouted = player_shouted
        self.winner = winner
        self.loser = loser
        self.state = state
        if self.index % 2 == 0:
            self.offense = offense or self.player_red
            self.defense = defense or self.player_black
        else:
            self.offense = offense or self.player_black
            self.defense = defense or self.player_red

    def start(self):
        self.state = constants.DuelState.ONGOING

    def players(self):
        return self.offense, self.defense

    def is_drawn(self):
        sum_offense = sum([card.value for card in self.offense.deck_in_duel.cards])
        sum_defense = sum([card.value for card in self.defense.deck_in_duel.cards])
        return sum_offense == sum_defense

    def is_over(self):
        return self.over

    def to_next_round(self):
        self.round_ += 1
        for player in self.players():
            player.recent_action = None

    def is_ongoing(self):
        return self.state == constants.DuelState.ONGOING

    def is_finished(self):
        return self.state not in [constants.DuelState.UNSTARTED, constants.DuelState.ONGOING]

    def display_decks(self):
        row_format = '{:^15}' * constants.DECK_PER_PILE
        red_first_line = '{:^105}{:^30}'.format('{} ({})'.format(self.player_red.name, self.player_red.alias),
                                                'Score {} / Die {}'.format(self.player_red.num_victory,
                                                                           self.player_red.num_shout_die))
        print(red_first_line)
        red_numbers = [
            '< #{} >'.format(deck.index + 1) if deck.is_in_duel() else '#{}'.format(deck.index + 1)
            for deck in self.player_red.decks]
        red_number_line = row_format.format(*red_numbers)
        print(red_number_line)
        red_undisclosed_delegates = [repr(deck.cards[0]) if deck.is_undisclosed() else '' for deck in
                                     self.player_red.decks]
        print(row_format.format(*red_undisclosed_delegates))
        red_opened_delegates = ['' if deck.is_undisclosed() else repr(deck.cards[0]) for deck in
                                self.player_red.decks]
        print(row_format.format(*red_opened_delegates))
        red_seconds = ['' if deck.is_undisclosed() else repr(deck.cards[1]) for deck in
                       self.player_red.decks]
        print(row_format.format(*red_seconds))
        red_lasts = ['' if deck.is_undisclosed() else repr(deck.cards[2]) for deck in
                     self.player_red.decks]
        print(row_format.format(*red_lasts))
        print()
        black_lasts = ['' if deck.is_undisclosed() else repr(deck.cards[2]) for deck in
                       self.player_black.decks]
        print(row_format.format(*black_lasts))
        black_seconds = ['' if deck.is_undisclosed() else repr(deck.cards[1]) for deck in
                         self.player_black.decks]
        print(row_format.format(*black_seconds))
        black_opened_delegates = ['' if deck.is_undisclosed() else repr(deck.cards[0]) for deck in
                                  self.player_black.decks]
        print(row_format.format(*black_opened_delegates))
        black_undisclosed_delegate = [repr(deck.cards[0]) if deck.is_undisclosed() else '' for deck in
                                      self.player_black.decks]
        print(row_format.format(*black_undisclosed_delegate))
        black_numbers = [
            ('< #{} >' if deck.is_in_duel() else '#{}').format(deck.index + 1) for deck in self.player_black.decks]
        black_number_line = row_format.format(*black_numbers)
        print(black_number_line)
        black_first_line = '{:^105}{:^30}'.format('{} (Player Black)'.format(self.player_black.name),
                                                  'Score {} / Die {}'.format(self.player_black.num_victory,
                                                                             self.player_black.num_shout_die))
        print(black_first_line)
        if not self.is_over():
            for player in self.players():
                undisclosed_values = ComputerPlayer.undisclosed_values(player.decks)
                if not undisclosed_values:
                    print("{}'s all values open! Shout done!".format(player.name))
                elif len(undisclosed_values) <= 3:
                    print("{}'s undisclosed values: {}".format(player.name, undisclosed_values))

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
            raise ValueError('Invalid action.')

    def process_no_shouts(self):
        """compare the sums and decides the winner"""
        print('All right. No actions.')
        sum_red = sum([card.value for card in self.player_red.deck_in_duel.cards])
        sum_black = sum([card.value for card in self.player_black.deck_in_duel.cards])
        if sum_red > sum_black:
            self.end(constants.DuelState.FINISHED, winner=self.player_red)
        elif sum_red < sum_black:
            self.end(constants.DuelState.FINISHED, winner=self.player_black)
        else:
            self.end(constants.DuelState.DRAWN, winner=self.defense)

    def process_double_dare(self):
        """do nothing if both users have dared after the second cards are open"""
        print('Ooh, double dare!')
        pass

    def process_shout_die(self, player_shouted):
        player_shouted.num_shout_die += 1
        self.end(constants.DuelState.DIED, player_shouted)

    def process_shout_done(self, player_shouted):
        player_shouted.num_shout_done += 1
        values = set(
            [card.value for deck in player_shouted.decks if deck.state != constants.DeckState.UNDISCLOSED for card in
             deck.cards if card.is_open()])
        if len(values) == len(constants.Rank):
            self.end(constants.DuelState.ABORTED_BY_CORRECT_DONE, player_shouted)
        else:
            if player_shouted.num_shout_done > constants.MAX_DONE:
                self.end(constants.DuelState.ABORTED_BY_WRONG_DONE, player_shouted)
            else:
                print("That was a wrong done, but you'll have one more chance.")

    def process_shout_draw(self, player_shouted):
        player_shouted.num_shout_draw += 1
        player_red_deck_sum = sum([card.value for card in self.player_red.deck_in_duel.cards])
        player_black_deck_sum = sum([card.value for card in self.player_black.deck_in_duel.cards])
        if player_red_deck_sum == player_black_deck_sum:
            self.end(constants.DuelState.DRAWN, winner=player_shouted)
        else:
            if player_shouted.num_shout_draw > constants.MAX_DRAW:
                self.end(constants.DuelState.ABORTED_BY_WRONG_DRAW, player_shouted)
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
        red_undisclosed_values = ComputerPlayer.undisclosed_values(self.player_red.decks)
        red_right_before_done = len(red_opened_values) == constants.NUM_CARD - 1 and len(red_undisclosed_values) == 1
        black_opened_values = ComputerPlayer.opened_values(self.player_black.decks)
        black_undisclosed_values = ComputerPlayer.undisclosed_values(self.player_black.decks)
        black_right_before_done = len(black_opened_values) == constants.NUM_CARD - 1 and len(
            black_undisclosed_values) == 1
        if red_right_before_done and black_right_before_done:
            self.end(constants.DuelState.ABORTED_BEFORE_DOUBLE_DONE, winner=self.player_black)

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
        # num_open = len([card for card in self.offense.deck_in_duel.cards if card.is_open()])
        # offense_delegate = self.offense.deck_in_duel.delegate()
        # defense_delegate = self.defense.deck_in_duel.delegate()
        # print(self.offense.name,
        #       ComputerPlayer.get_chances(self.offense.decks, offense_delegate, self.defense.decks, defense_delegate,
        #                                  num_open))
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

    def end(self, state, player_shouted=None, winner=None, loser=None):
        self.over = True
        self.time_ended = time.time()
        self.state = state
        self.player_shouted = player_shouted
        self.winner = winner
        self.loser = loser
        if winner is None and loser is None:
            if state == constants.DuelState.DIED:
                print("Duel #{}: {} died, so no one gets a point.".format(self.index + 1, self.player_shouted.name))
            elif state == constants.DuelState.DRAWN:
                self.winner = self.defense
                self.loser = self.offense
                self.winner.num_victory += 1
                print("Duel #{}: The sums are equal, but no one shouted draw, so the defense ({}) gets a point.".format(
                    self.index + 1, self.winner.name))
            elif state == constants.DuelState.ABORTED_BY_CORRECT_DONE:
                print("Duel #{}: {} is done, so this duel is aborted.".format(self.index + 1, self.player_shouted.name))
            elif state == constants.DuelState.ABORTED_BY_WRONG_DONE:
                print(
                    "Duel #{}: {} shouted done wrong, so this duel is aborted.".format(self.index + 1,
                                                                                       self.player_shouted.name))
            elif state == constants.DuelState.ABORTED_BY_WRONG_DRAW:
                print(
                    "Duel #{}: {} shouted draw wrong, so this duel is aborted.".format(self.index + 1,
                                                                                       self.player_shouted.name))
            else:
                raise ValueError('At least one of winner or loser must be supplied.')
        else:
            if winner is None:
                self.winner = self.defense if loser == self.offense else self.offense
            if loser is None:
                self.loser = self.offense if winner == self.offense else self.defense
            self.winner.num_victory += 1
            print("Duel #{}: {} wins and gets a point.".format(self.index + 1, self.winner.name))


class PlayersSetup(object):
    def __init__(self, num_human_players):
        self.num_human_players = num_human_players

    def run(self):
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
            print(globals())
            if type(class1) in ['NoneType', 'ComputerPlayer'] or not issubclass(class1, ComputerPlayer):
                raise ValueError('Invalid class name for computer player')
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
        red_numbers = [('< #{} >' if deck.is_in_duel() else '#{}').format(
            deck.index + 1) for deck in red_decks]
        red_number_line = row_format.format(*red_numbers)
        print(red_number_line)
        red_undisclosed_delegates = [repr(deck.cards[0]) if deck.is_undisclosed() else '' for deck in
                                     red_decks]
        print(row_format.format(*red_undisclosed_delegates))
        red_opened_delegates = ['' if deck.is_undisclosed() else repr(deck.cards[0]) for deck in
                                red_decks]
        print(row_format.format(*red_opened_delegates))
        red_seconds = ['' if deck.is_undisclosed() else repr(deck.cards[1]) for deck in
                       red_decks]
        print(row_format.format(*red_seconds))
        red_lasts = ['' if deck.is_undisclosed() else repr(deck.cards[2]) for deck in
                     red_decks]
        print(row_format.format(*red_lasts))
        print()
        print('{:^135}'.format('' if duel is None else '[Duel #{}]'.format(duel.index + 1)))
        print()
        black_decks = game.player_black.decks
        black_lasts = ['' if deck.is_undisclosed() else repr(deck.cards[2]) for deck in
                       black_decks]
        print(row_format.format(*black_lasts))
        black_seconds = ['' if deck.is_undisclosed() else repr(deck.cards[1]) for deck in
                         black_decks]
        print(row_format.format(*black_seconds))
        black_opened_delegates = ['' if deck.is_undisclosed() else repr(deck.cards[0]) for
                                  deck in black_decks]
        print(row_format.format(*black_opened_delegates))
        black_undisclosed_delegate = [repr(deck.cards[0]) if deck.is_undisclosed() else '' for
                                      deck in black_decks]
        print(row_format.format(*black_undisclosed_delegate))
        black_numbers = [
            '< #{} >'.format(deck.index + 1) if deck.is_in_duel() else '#{}'.format(
                deck.index + 1) for deck in black_decks]
        black_number_line = row_format.format(*black_numbers)
        print(black_number_line)
        black_fense = '' if duel is None else (
            'Offense' if game.player_black == duel.offense else 'Defense')
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
        time_started_str = last_game.time_started
        time_started_float = float(time_started_str)
        datetime_started = datetime.datetime.fromtimestamp(time_started_float)
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
    while not game.is_over():
        duel = game.to_next_duel()
        while not duel.is_over():
            duel.to_next_round()
            message, duration = game.prepare()
            output_handler.display(game.to_json(), message, duration)
            user_input = game.accept()
            message, duration = game.process(user_input)
            output_handler.display(game.to_json(), message, duration)
            # game.decide_decks_for_duel()
            # duel.display_decks()
            # duel.open_next_cards()
            # duel.display_decks()
            # duel.get_and_process_input()
            # duel.display_decks()
            # duel.open_next_cards()
            # duel.display_decks()
            # if not duel.over:
            #     duel.get_and_process_final_input()
        game.cleanup_duel()
    game.display_result()

# TODO pile 어떻게? player, game, constants
# TODO flag 도입해야 모든 시점을 표현할 수 있을 듯?
