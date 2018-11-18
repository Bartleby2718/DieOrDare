from die_or_dare import *


def main():
    output_handler = OutputHandler()

    ### player initialization
    # print("I want to know your names first.")
    player1 = DumbComputerPlayer()
    # player1 = HumanPlayer('Player 1, enter your name: ')
    player2 = DumbComputerPlayer(player1.name)
    # player2 = HumanPlayer('Player 2, enter your name: ', player1.name)
    # num_human_players = 2 - len(sys.argv[1:])
    # player1, player2 = PlayersSetup(num_human_players).run()

    ### red/black decision
    message = "All right, {} and {}. Let's get started!".format(player1.name,
                                                                player2.name)
    message += '\nLet\'s flip a coin to decide who will be the Player Red!'
    duration = constants.DELAY_BEFORE_COIN_TOSS
    output_handler.display(message=message, duration=duration)

    # player_red, player_black = RandomPlayerOrder(player1, player2).pop()
    player_red, player_black = player1, player2

    red_pile = RedPile()
    player_red.take_pile(red_pile)
    black_pile = BlackPile()
    player_black.take_pile(black_pile)

    message = '{}, you are the Player Red, so you will go first.'.format(
        player_red.name)
    message += '\n{}, you are the Player Black.'.format(player_black.name)
    duration = constants.DELAY_AFTER_COIN_TOSS
    output_handler.display(message=message, duration=duration)

    ### key settings
    player_red.key_settings = KeySettingsInput.bottom_left()
    # player_red.key_settings = KeySettingsTextInput.from_human(player_red.name).pop()
    player_black.key_settings = KeySettingsInput.top_right()
    # blacklist = list(player_red.key_settings.values())
    # player_black.key_settings = KeySettingsTextInput.from_human(player_black.name, blacklist).pop()

    ### joker value strategy
    # player_red.joker_value_strategy = JokerValueStrategyTextInput.from_human(player_red.name).pop()
    player_red.joker_value_strategy = SameAsMax
    # player_black.joker_value_strategy = JokerValueStrategyTextInput.from_human(player_black.name).pop()
    player_black.joker_value_strategy = SameAsMax

    ### delegate strategy
    # player_red.joker_position_strategy = JokerPositionStrategyTextInput.from_human(player_red.name).pop()
    player_red.joker_position_strategy = JokerLast
    # player_black.joker_position_strategy = JokerPositionStrategyTextInput.from_human(player_black.name).pop()
    player_black.joker_position_strategy = JokerLast

    # initialize decks
    player_red.decks = DeckRandomizer(player_red.pile,
                                      player_red.joker_value_strategy,
                                      player_red.joker_position_strategy).pop()
    player_black.decks = DeckRandomizer(player_black.pile,
                                        player_black.joker_value_strategy,
                                        player_black.joker_position_strategy).pop()

    message = "Let's start DieOrDare!\nHere we go!"
    duration = constants.DELAY_BEFORE_GAME_START
    output_handler.display(message=message, duration=duration)

    game = Game(player_red, player_black)

    while not game.is_over():
        duel = game.to_next_duel()
        while not duel.is_over():
            message, duration = game.prepare()
            output_handler.display(game.to_json(), message, duration)
            user_input = game.accept()
            message, duration = game.process(user_input)
            output_handler.display(game.to_json(), message, duration)

    # output_handler.export_to_json()
    # for player in game.players():
    #     for deck in player.decks:
    #         deck.state = constants.DeckState.FINISHED
    #         for card in deck.cards:
    #             card.open_up()
    # output_handler.display(jsonpickle.encode(game))


if __name__ == '__main__':
    main()
