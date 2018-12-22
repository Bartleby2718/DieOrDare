from die_or_dare import *
import keras
import tensorflow


class ReinforcementLearningAgent(ComputerPlayer):
    choices = {
        # 0~8: OffenseDeckIndexInput (9)
        0: OffenseDeckIndexInput(0),
        1: OffenseDeckIndexInput(1),
        2: OffenseDeckIndexInput(2),
        3: OffenseDeckIndexInput(3),
        4: OffenseDeckIndexInput(4),
        5: OffenseDeckIndexInput(5),
        6: OffenseDeckIndexInput(6),
        7: OffenseDeckIndexInput(7),
        8: OffenseDeckIndexInput(8),
        # 9~17: DefenseDeckIndexInput (9)
        9: DefenseDeckIndexInput(0),
        10: DefenseDeckIndexInput(1),
        11: DefenseDeckIndexInput(2),
        12: DefenseDeckIndexInput(3),
        13: DefenseDeckIndexInput(4),
        14: DefenseDeckIndexInput(5),
        15: DefenseDeckIndexInput(6),
        16: DefenseDeckIndexInput(7),
        17: DefenseDeckIndexInput(8),
        # 18~22: Action (5)
        18: constants.Action.IDLE,
        19: constants.Action.DARE,
        20: constants.Action.DIE,
        21: constants.Action.DONE,
        22: constants.Action.DRAW,
    }

    def __init__(self, name=None, initial_epsilon=0.0, weights_file_name=None,
                 architecture_file_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = 'Smarty' if name is None else name
        model = None
        if architecture_file_name is None:
            try:
                with open(architecture_file_name) as architecture_file:
                    architecture_json = json.load(architecture_file)
                    model = keras.models.model_from_json(architecture_json)
            except:
                pass
        if model is None:
            model = keras.models.Sequential()
            game_to_array_length = 349  # TODO: programmatically attain this value
            model.add(keras.layers.core.Dense(game_to_array_length,
                                              input_shape=(
                                                  game_to_array_length,)))
            model.add(keras.layers.advanced_activations.ReLU())
            model.add(keras.layers.core.Dense(game_to_array_length))
            model.add(keras.layers.advanced_activations.ReLU())
            num_choices = 2 * constants.DECK_PER_PILE + len(constants.Action)
            model.add(keras.layers.core.Dense(num_choices))
        model.compile(optimizer='adam', loss='mse')
        self.model = model
        self.epsilon = None
        self.initial_epsilon = initial_epsilon
        self.epsilon_multiplier = None
        self.total_reward = None
        self.intelligence = None
        self.weights_file_name = weights_file_name
        # open model weights and architecture if available
        if weights_file_name is not None:
            if os.path.exists(weights_file_name):  # .h5
                self.model.load_weights(weights_file_name)
        self.architecture_file_name = architecture_file_name

    def reset_rl_data(self):
        self.total_reward = 0
        self.intelligence = ArtificialIntelligence(self.model)

    def train(self, opponent, n_epoch=100, data_size=50, epsilon_multiplier=1.0,
              save_result=False, suppress_output=False, save_all=True,
              weights_file_name='new.h5',
              architecture_file_name='new.json'):

        train_start = datetime.datetime.now()

        # initialize history
        win_history = []  # history of win/lose game
        hsize = 10  # history window size
        win_rate = 0.0
        epoch = None
        self.epsilon = self.initial_epsilon
        # epoch for loop
        for epoch in range(n_epoch):
            game_start = time.time()
            output_handler = OutputHandler()
            self.epsilon *= epsilon_multiplier
            loss = 0.0
            # restart game
            for player in [self, opponent]:
                if isinstance(player, ReinforcementLearningAgent):
                    player.reset_rl_data()
                player.reset()
            intelligence = self.intelligence

            # red/black decision
            if not suppress_output:
                message = "All right, {} and {}. Let's get started!".format(
                    self.name, opponent.name)
                message += '\nLet\'s flip a coin to decide who will be the Player Red!'
                duration = constants.Duration.BEFORE_COIN_TOSS
                output_handler.display(message=message, duration=duration)

            player_red, player_black = RandomPlayerOrder(self, opponent).players
            if not suppress_output:
                message = '{}, you are the Player Red, so you will go first.'.format(
                    player_red.name)
                message += '\n{}, you are the Player Black.'.format(
                    player_black.name)
                duration = constants.Duration.AFTER_COIN_TOSS
                output_handler.display(message=message, duration=duration)

            game = DoDGameRL(player_red, player_black)
            game.distribute_piles()
            game.build_decks()

            if not suppress_output:
                message = "Let's start DieOrDare!\nHere we go!"
                duration = constants.Duration.BEFORE_GAME_START
                output_handler.display(message=message, duration=duration)

            # get initial environment state (1d array)
            by_red = self == game.player_red
            envstate = game.observe(by_red)

            n_episodes = 0
            while not game.is_over():
                duel = game.to_next_duel()
                while not duel.is_over():
                    message, duration = game.prepare()
                    if save_all or save_result:
                        output_handler.save(game.to_json(), message)
                    if not suppress_output:
                        output_handler.display(game.to_json(), message,
                                               duration)

                    # previous environment state
                    prev_envstate = envstate
                    reward_before = self.total_reward
                    # get next action
                    user_input = game.accept(prev_envstate)
                    # Apply action, get reward and new envstate
                    message, duration = game.process(user_input)
                    if save_all or save_result:
                        output_handler.save(game.to_json(), message)
                    if not suppress_output:
                        output_handler.display(game.to_json(), message,
                                               duration)
                    by_red = self == game.player_red
                    envstate = game.observe(by_red)
                    reward_after = self.total_reward
                    reward = reward_after - reward_before

                    # Store episode (experience)
                    if isinstance(user_input, OffenseDeckIndexInput):
                        choice = user_input.value
                    elif isinstance(user_input, DefenseDeckIndexInput):
                        choice = constants.DECK_PER_PILE + user_input.value
                    else:
                        choice = 2 * constants.DECK_PER_PILE + self.recent_action.value
                    episode = [prev_envstate, choice, reward, envstate,
                               game.is_over()]
                    intelligence.memorize(episode)
                    n_episodes += 1

                    # Train neural network model
                    inputs, targets = intelligence.get_data(data_size=data_size)
                    self.model.fit(inputs, targets, epochs=8, batch_size=16,
                                   verbose=0)
                    loss = self.model.evaluate(inputs, targets, verbose=0)
            if game.winner == self:
                win_history.append(1)
            else:
                win_history.append(0)
            game_time = time.time() - game_start
            if save_all:
                output_handler.export_game_states(final_state_only=False)
            elif save_result:
                output_handler.export_game_states(final_state_only=True)

            # record epoch
            # if len(win_history) > hsize:
            #     win_rate = sum(win_history[-hsize:]) / hsize
            training_time = (
                    datetime.datetime.now() - train_start).total_seconds()
            # template = "Epoch: {:02d}/{:02d} | Loss: {:03.4f} | Episodes: {:02} | Win : {:0} | Result: {} in Duel #{} | Game time: {:.2f} | Total time: {:.2f}"
            # print(template.format(epoch + 1, n_epoch, loss, n_episodes,
            #                       sum(win_history), game.result.name,
            #                       game.duel_index + 1, game_time,
            #                       training_time))
            columns = (
                epoch + 1, loss, n_episodes, win_history[-1], game.result.name,
                game.duel_index + 1, game_time, self.alias)
            print(','.join(str(elem) for elem in columns))
            # if sum(win_history[-hsize:]) == hsize:
            #     print("Reached 100%% win rate at epoch: %d" % (epoch,))
            #     break
            # elif win_rate > 0.9:
            #     self.epsilon = 0.05

        # Save model weights and architecture
        self.model.save_weights(weights_file_name)
        with open(architecture_file_name, 'w') as outfile:
            json.dump(self.model.to_json(), outfile)

    def decide_offense_deck_index(self, decks_opponent, points_opponent,
                                  num_shout_die_opponent, prev_envstate=None):
        # If there's only one undisclosed value and that's a delegate, choose it
        undisclosed_values = ComputerPlayer.undisclosed_values(self.decks)
        delegate_values = (deck.delegate.value for deck in self.decks)
        if len(undisclosed_values) == 1:
            undisclosed_value = undisclosed_values[0]
            if undisclosed_value in delegate_values:
                deck = AnyOffenseDeck.apply(self.decks)
                return deck.index
        elif numpy.random.rand() > self.epsilon:
            deck_index = numpy.argmax(self.intelligence.predict(prev_envstate))
            if deck_index in range(constants.DECK_PER_PILE):
                deck = self.decks[deck_index]
                if deck.is_undisclosed():
                    return deck_index
        deck = AnyOffenseDeck.apply(self.decks)
        return deck.index

    def decide_defense_deck_index(self, decks_opponent, points_opponent,
                                  num_shout_die_opponent, prev_envstate=None):
        # If there's only one undisclosed value and that's a delegate, ignore it
        undisclosed_values = ComputerPlayer.undisclosed_values(decks_opponent)
        undisclosed_delegate_values = set(deck.delegate.value for deck in
                                          decks_opponent if
                                          deck.is_undisclosed())
        if len(undisclosed_values) == 1:
            undisclosed_value = undisclosed_values[0]
            if len(undisclosed_delegate_values) == 1:
                deck = AnyDefenseDeck.apply(self.decks)
            else:
                candidates = [deck for deck in decks_opponent if
                              deck.delegate.value != undisclosed_value]
                deck = SmallestDefenseDeck.apply(candidates)
            return deck.index
        elif numpy.random.rand() > self.epsilon:
            deck_index = numpy.argmax(self.intelligence.predict(prev_envstate))
            deck_index -= constants.DECK_PER_PILE
            if deck_index in range(constants.DECK_PER_PILE):
                deck = decks_opponent[deck_index]
                if deck.is_undisclosed():
                    return deck_index
        deck = AnyDefenseDeck.apply(decks_opponent)
        return deck.index

    def shout(self, decks_opponent, points_opponent,
              num_shout_die_opponent, round_, in_turn, duel_index,
              prev_envstate=None):
        # TODO: 해당 듀얼을 invalidate 할 필요가 없고 승리 확률이 100%면 die 금지
        # TODO: 상대는 done 이고 die 가 남으면 해당 듀얼을 die 로 invalidate
        valid_actions = self.valid_actions(round_)
        if not ComputerPlayer.undisclosed_values(self.decks):
            action = constants.Action.DONE
            return Shout(self, action)
        if duel_index < 4:
            valid_actions.remove(constants.Action.DONE)
        if round_ == 3:
            # TODO: round 2여도 확률 100%면
            sum_offense = sum(card.value for card in self.deck_in_duel)
            deck_in_duel_opponent = [deck for deck in decks_opponent
                                     if deck.is_in_duel()][0]
            sum_defense = sum(card.value for card in deck_in_duel_opponent)
            if sum_offense == sum_defense:
                action = constants.Action.DRAW
            else:
                action = constants.Action.IDLE
            return Shout(self, action)
        elif not ComputerPlayer.undisclosed_values(decks_opponent):
            if constants.Action.DIE in valid_actions:
                action = constants.Action.DIE
                return Shout(self, action)
        action_index = numpy.argmax(self.intelligence.predict(prev_envstate))
        action_index -= 2 * constants.DECK_PER_PILE
        if action_index in range(len(constants.Action)):
            action = constants.Action(action_index)
        else:
            action = random.choice(valid_actions)
        return Shout(self, action)


class ReinforcementLearningGame(abc.ABC):
    """boilerplate for RL on a single-player score-less game"""

    @abc.abstractmethod
    def build_model(self, state_size, num_actions, *args, **kwargs):
        pass

    @abc.abstractmethod
    def reset(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def available_actions(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def perform(self, action, *args, **kwargs):
        pass

    @abc.abstractmethod
    def update(self, action, *args, **kwargs):
        pass

    @abc.abstractmethod
    def reward(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def observe(self, *args, **kwargs):
        """returns the environment state in an 1d array"""
        pass

    # @abc.abstractmethod
    # def play(self, *args, **kwargs):
    #     pass


class ArtificialIntelligence(abc.ABC):
    def __init__(self, model, max_memory=50, discount=1.0):
        # TODO: change discount factor?
        self.model = model
        self.max_memory = max_memory
        self.discount = discount
        self.memory = list()
        self.num_actions = model.output_shape[-1]

    def memorize(self, episode):
        self.memory.append(episode)
        if len(self.memory) > self.max_memory:
            del self.memory[0]

    def predict(self, environment_state):
        return self.model.predict(environment_state)[0]

    def get_data(self, data_size=10):
        initial_episode = self.memory[0]
        initial_envstate = initial_episode[0]
        env_size = initial_envstate.shape[1]
        mem_size = len(self.memory)
        data_size = min(mem_size, data_size)
        inputs = numpy.zeros((data_size, env_size))
        targets = numpy.zeros((data_size, self.num_actions))
        for i, j in enumerate(
                numpy.random.choice(range(mem_size), data_size, replace=False)):
            envstate, action, reward, envstate_next, game_over = self.memory[j]
            inputs[i] = envstate
            targets[i] = self.predict(envstate)
            # Q_sa = derived policy = max quality env/action = max_a' Q(s', a')
            q_sa = numpy.max(self.predict(envstate_next))
            if game_over:
                targets[i, action] = reward
            else:
                # reward + gamma * max_a' Q(s', a')
                targets[i, action] = reward + self.discount * q_sa
        return inputs, targets


class DoDGameRL(Game):
    def __init__(self, player_red, player_black):
        super().__init__(player_red, player_black)

    def _end(self, result, winner=None, loser=None):
        super()._end(result, winner, loser)
        if isinstance(self.winner, ReinforcementLearningAgent):
            self.winner.total_reward += 1

    def observe(self, by_red):
        if by_red:
            red = list(self.player_red.to_array())
            black_decks = self.player_black.decks_public()
            black_points = self.player_black.points
            black_num_shout_die = self.player_black.num_shout_die
            black_deck_in_duel_index = self.player_black.deck_in_duel_index

            decks = [deck.to_array() for deck in black_decks]
            decks = list(itertools.chain.from_iterable(decks))
            points = -1 if black_points is None else black_points
            if black_num_shout_die is None:
                num_shout_die = -1
            else:
                num_shout_die = black_num_shout_die
            if black_deck_in_duel_index is None:
                deck_in_duel_index = -1
            else:
                deck_in_duel_index = black_deck_in_duel_index
            others = [points, num_shout_die, deck_in_duel_index]
            black = decks + others
            common = [self.duel_index % 2]
            result = numpy.array([*red, *black, *common])
            return result.reshape((1, -1))
        else:
            black = list(self.player_black.to_array())
            red_decks = self.player_red.decks_public()
            red_points = self.player_red.points
            red_num_shout_die = self.player_red.num_shout_die
            red_deck_in_duel_index = self.player_red.deck_in_duel_index

            decks = [deck.to_array() for deck in red_decks]
            decks = list(itertools.chain.from_iterable(decks))
            points = -1 if red_points is None else red_points
            if red_num_shout_die is None:
                num_shout_die = -1
            else:
                num_shout_die = red_num_shout_die
            if red_deck_in_duel_index is None:
                deck_in_duel_index = -1
            else:
                deck_in_duel_index = red_deck_in_duel_index
            others = [points, num_shout_die, deck_in_duel_index]
            red = decks + others
            common = [self.duel_index % 2]
            result = numpy.array([*red, *black, *common])
            return result.reshape((1, -1))

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
        for player in self.players:
            if player.recent_action not in player.valid_actions(round_):
                if isinstance(player, ReinforcementLearningAgent):
                    player.total_reward -= 1
                    duel.end(constants.DuelState.ABORTED_BY_WRONG_CHOICE)
                    self._end(constants.GameResult.ABORTED_BY_WRONG_CHOICE)
                    message = '{} made a wrong choice, so Duel #{} is aborted.'.format(
                        player.name, duel.index + 1)
                    message += '\nGame aborted because a wrong choice was made.'
                    duration = constants.Duration.AFTER_GAME_ENDS
                    return message, duration
        # priority: die > done > draw > dare (then offense > defense)
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
            if constants.Action.DRAW in valid_actions:
                if player.recent_action == constants.Action.DRAW:
                    player.num_shout_draw += 1
                    if duel.is_drawn():  # correct draw
                        duel.end(constants.DuelState.DRAWN, player)
                        message = '{} shouted draw correctly and gets a point. Duel #{} ended.'.format(
                            player.name, duel.index + 1)
                        duration = constants.Duration.AFTER_DUEL_ENDS
                        if duel.winner.points == constants.REQUIRED_POINTS:
                            self._end(constants.GameResult.FINISHED,
                                      winner=duel.winner)
                            message += "\n{0} wins! The game has ended as {0} first scored {1} points.".format(
                                duel.winner.name, constants.REQUIRED_POINTS)
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
            if duel.winner.points == constants.REQUIRED_POINTS:
                self._end(constants.GameResult.FINISHED, winner=duel.winner)
                message += "\n{0} wins! The game has ended as {0} first scored {1} points.".format(
                    duel.winner.name, constants.REQUIRED_POINTS)
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
        try:
            if index not in range(constants.DECK_PER_PILE):
                raise IndexError('Index out of range.')
            offense_deck = offense.decks[index]
            if not offense_deck.is_undisclosed():
                raise AssertionError('Choose an undisclosed deck.')
        except (IndexError, AssertionError) as e:
            if isinstance(offense, ReinforcementLearningAgent):
                offense.total_reward -= 1
                duel.end(constants.DuelState.ABORTED_BY_WRONG_CHOICE)
                self._end(constants.GameResult.ABORTED_BY_WRONG_CHOICE)
                message = '{} made a wrong choice, so Duel #{} is aborted.'.format(
                    offense.name, duel.index + 1)
                message += '\nGame aborted because a wrong choice was made.'
                duration = constants.Duration.AFTER_GAME_ENDS
            else:
                message = e.args[0]
                duration = constants.Duration.AFTER_DECK_CHOICE
        else:
            duel.summon(offense_deck=offense_deck)
            message = 'Deck #{} chosen as the offense deck.'.format(index + 1)
            duration = constants.Duration.AFTER_DECK_CHOICE
        return message, duration

    def process_defense_deck_index_input(self, intra_duel_input):
        duel = self.duel_ongoing
        offense = duel.offense
        defense = duel.defense
        index = intra_duel_input.value
        try:
            if index not in range(constants.DECK_PER_PILE):
                raise IndexError('Index out of range.')
            defense_deck = defense.decks[index]
            if not defense_deck.is_undisclosed():
                raise AssertionError('Choose an undisclosed deck.')
        except (IndexError, AssertionError) as e:
            if isinstance(offense, ReinforcementLearningAgent):
                offense.total_reward -= 1
                duel.end(constants.DuelState.ABORTED_BY_WRONG_CHOICE)
                self._end(constants.GameResult.ABORTED_BY_WRONG_CHOICE)
                message = '{} made a wrong choice, so Duel #{} is aborted.'.format(
                    offense.name, duel.index + 1)
                message += '\nGame aborted because a wrong choice was made.'
                duration = constants.Duration.AFTER_GAME_ENDS
            else:
                message = e.args[0]
                duration = constants.Duration.AFTER_DECK_CHOICE
        else:
            duel.summon(defense_deck=defense_deck)
            message = 'Deck #{} chosen as the defense deck.'.format(index + 1)
            duration = constants.Duration.AFTER_DECK_CHOICE
        return message, duration


if __name__ == '__main__':
    agent = ReinforcementLearningAgent(
        initial_epsilon=0.0,
        joker_value_strategy=Thirteen
    )
    k = 0
    while True:
        k += 1
        # print('Starting batch #{}'.format(k))
        opponent = AntiDie()
        agent.train(
            opponent,
            n_epoch=1000000,
            save_result=False,
            suppress_output=True,
            save_all=False,
            epsilon_multiplier=1,
        )
