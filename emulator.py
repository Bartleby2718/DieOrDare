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
    print("\nAll right, {} and {}. Let's get started!\nLet's flip a coin to decide who will be the Player Red!".format(
        player1.name, player2.name))
    player_red, player_black = RandomPlayerOrder(player1, player2).pop()
    ranks = constants.Rank
    red_joker = Card(None, True, constants.JOKER, None, False)
    red_suits = constants.RED_SUITS
    player_red.pile = [red_joker] + [Card(suit, True, rank.name, rank.value, False) for suit in red_suits for rank in ranks]
    player_red.alias = constants.PLAYER_RED
    black_joker = Card(None, False, constants.JOKER, None, False)
    black_suits = constants.BLACK_SUITS
    player_black.pile = [black_joker] + [Card(suit, False, rank.name, rank.value, False) for suit in black_suits for rank in ranks]
    player_black.alias = constants.PLAYER_BLACK
    print('{}, you are the Player Red, so you will go first.'.format(player_red.name))
    print('{}, you are the Player Black.'.format(player_black.name))

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
    # player_red.joker_location_strategy = JokerPositionStrategyTextInput.from_human(player_red.name).pop()
    player_red.joker_location_strategy = JokerLast
    # player_black.joker_location_strategy = JokerPositionStrategyTextInput.from_human(player_black.name).pop()
    player_black.joker_location_strategy = JokerLast
    game = Game(player_red, player_black)
    # initialize decks
    player_red.decks = DeckRandomizer(player_red.pile, player_red.joker_value_strategy,
                                      player_red.joker_location_strategy).pop()
    player_black.decks = DeckRandomizer(player_black.pile, player_black.joker_value_strategy,
                                        player_black.joker_location_strategy).pop()




    while not game.is_over():
        duel = game.to_next_duel()
        while not duel.is_over():
            duel.to_next_round()
            message, duration = game.prepare()
            output_handler.display(game.to_json(), message, duration)
            user_input = game.accept()
            message, duration = game.process(user_input)
            output_handler.display(game.to_json(), message, duration)







    while not game.over:
        game.duel_index += 1
        duel = Duel(game.player_red, game.player_black, game.duel_index)
        # round 1
        message = 'Starting Duel {}...\n{}, your turn!'.format(duel.index, duel.offense.name)
        duration = constants.DELAY_AFTER_TURN_NOTICE
        game.duel_ongoing = duel
        output_handler.display(jsonpickle.encode(game), message, duration)
        game.decide_decks_for_duel()
        output_handler.display(jsonpickle.encode(game), 'The two decks have been chosen!')
        # round 2
        duel.open_next_cards()
        output_handler.display(jsonpickle.encode(game))
        duel.get_and_process_input()
        output_handler.display(jsonpickle.encode(game))
        # round 3
        duel.open_next_cards()
        output_handler.display(jsonpickle.encode(game))
        if not duel.over:
            duel.get_and_process_final_input()
            output_handler.display(jsonpickle.encode(game))
        game.cleanup_duel()
    ending_message = 'Game!\nCongratulations! {} has won the Game! (Reason: {})'.format(game.winner.name, game.result.name)
    output_handler.display(jsonpickle.encode(game), ending_message)
    # output_handler.export_to_json()
    # for player in game.players():
    #     for deck in player.decks:
    #         deck.state = constants.DeckState.FINISHED
    #         for card in deck.cards:
    #             card.open_up()
    # output_handler.display(jsonpickle.encode(game))


if __name__ == '__main__':
    main()
