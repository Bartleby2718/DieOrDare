import die_or_dare
import inspect
import jsonpickle
import os


def stringify(argument):
    if argument is None:
        return str()
    elif isinstance(argument, int):
        return str(argument)
    elif isinstance(argument, str):
        return argument
    elif inspect.isclass(argument):
        return argument.__name__
    else:
        raise Exception('This is not accepted')


def main():
    current_file_path = os.path.abspath(__file__)
    current_directory_path = os.path.dirname(current_file_path)
    directory_name = 'json'
    input_directory_path = os.path.join(current_directory_path, directory_name)
    output_file_name = 'analysis.csv'
    output_file_path = os.path.join(input_directory_path, output_file_name)
    with open(output_file_path, 'w') as output:
        column_names = ('winner_class', 'loser_class', 'winner_alias',
                        'game_result', 'duel_index',
                        'winner_joker_value_strategy',
                        'loser_joker_value_strategy',
                        'winner_joker_position_strategy',
                        'loser_joker_position_strategy')
        output.write(','.join(column_names) + '\n')
        for file_name in os.listdir(input_directory_path):
            if file_name.endswith('.json'):
                output_handler = die_or_dare.OutputHandler()
                file_path = os.path.join(input_directory_path, file_name)
                output_handler.import_from_json(file_path)
                final_state = output_handler.states[-1]
                game = jsonpickle.decode(final_state)
                winner = game.winner
                loser = game.loser
                winner_class = winner.__class__
                loser_class = loser.__class__
                winner_alias = winner.alias
                game_result = game.result.name
                duel_index = game.duel_index
                winner_joker_value_strategy = winner.joker_value_strategy
                loser_joker_value_strategy = loser.joker_value_strategy
                winner_joker_position_strategy = winner.joker_position_strategy
                loser_joker_position_strategy = loser.joker_position_strategy
                row = (winner_class, loser_class, winner_alias, game_result,
                       duel_index, winner_joker_value_strategy,
                       loser_joker_value_strategy,
                       winner_joker_position_strategy,
                       loser_joker_position_strategy)
                row_str = (stringify(element) for element in row)
                output.write(','.join(row_str) + '\n')
    print('Done!')


if __name__ == '__main__':
    main()
