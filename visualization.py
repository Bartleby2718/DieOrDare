import constants
import itertools
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import os


class Plotter(object):
    def __init__(self, path_to_csv_file):
        data = np.genfromtxt(path_to_csv_file, delimiter=',', dtype=[
            ('epoch', 'i'), ('loss', 'f'), ('episode', 'i'), ('result', 'i'),
            ('reason', 'i'), ('duel', 'i'), ('time', 'f'), ('color', 'i')], )
        self.epoch = data['epoch']
        self.loss = data['loss']
        self.episode = data['episode']
        self.result = data['result']
        self.reason = data['reason']
        self.duel = data['duel']
        self.time = data['time']
        self.color = data['color']
        self.data_size = len(self.epoch)

    @staticmethod
    def moving_average(array_like, window):
        """calculate the moving average of a mutable sequence"""
        cumulative_sum = np.cumsum(np.insert(array_like, 0, 0))
        first_part_removed = cumulative_sum[window:]
        last_part_removed = cumulative_sum[:-window]
        return (first_part_removed - last_part_removed) / float(window)

    def plot_epoch_vs_loss(self, logarithmic_scale=True):
        """plot loss against epoch, optionally using a log scale for y-axis"""
        plt.plot(self.epoch, self.loss, color='r', label='loss')
        plt.xlabel('epoch')
        plt.ylabel('loss')
        if logarithmic_scale:
            plt.yscale('log')
        plt.title('epoch vs loss')
        plt.legend()
        plt.show()

    def plot_epoch_vs_time(self, window):
        """plot time against epoch"""
        moving_average_time = self.moving_average(self.time, window)
        plt.plot(self.epoch, self.time, color='r', label='time elapsed')
        plt.plot(self.epoch[window - 1:], moving_average_time, color='b',
                 label='{}-epoch mov. avg.'.format(window))
        mean = np.mean(self.time)
        epoch_min = min(self.epoch)
        epoch_max = max(self.epoch)
        plt.hlines(y=mean, xmin=epoch_min, xmax=epoch_max, colors='g',
                   linestyles='solid', label='cum. avg.', zorder=10)
        plt.xlabel('epoch')
        plt.ylabel('time (seconds)')
        plt.title('epoch vs time')
        plt.legend()
        plt.show()

    def plot_epoch_vs_episode(self, window):
        """plot episode against epoch"""
        plt.plot(self.epoch, self.episode, color='r',
                 label='number of episodes')
        moving_average_episodes = self.moving_average(self.episode, window)
        plt.plot(self.epoch[window - 1:], moving_average_episodes, color='b',
                 label='{}-epoch mov. avg.'.format(window))
        mean = np.mean(self.episode)
        epoch_min = min(self.epoch)
        epoch_max = max(self.epoch)
        plt.hlines(y=mean, xmin=epoch_min, xmax=epoch_max, colors='g',
                   linestyles='solid', label='cum. avg.', zorder=10)
        plt.xlabel('epoch')
        plt.ylabel('episode')
        plt.title('epoch vs episode')
        plt.legend()
        plt.show()

    def plot_epoch_vs_duel(self, window):
        """plot duel against epoch"""
        plt.plot(self.epoch, self.duel, color='r', label='number of duels')
        moving_average_duels = self.moving_average(self.duel, window)
        plt.plot(self.epoch[window - 1:], moving_average_duels, color='b',
                 label='{}-epoch mov. avg.'.format(window))
        mean = np.mean(self.duel)
        epoch_min = min(self.epoch)
        epoch_max = max(self.epoch)
        plt.hlines(y=mean, xmin=epoch_min, xmax=epoch_max, colors='g',
                   linestyles='solid', label='cum. avg.', zorder=10)
        plt.xlabel('epoch')
        plt.ylabel('duel')
        plt.title('epoch vs duel')
        plt.legend()
        plt.show()

    def plot_epoch_vs_winning_percentage_cumulative(self):
        """plot winning percentage against epoch"""
        percent_formatter = mticker.PercentFormatter(1.0)
        fig, ax = plt.subplots()
        ax.yaxis.set_major_formatter(percent_formatter)
        plt.minorticks_on()

        games_won = np.cumsum(self.result)
        winning_percentage = games_won / self.epoch
        plt.plot(self.epoch, winning_percentage, color='k', label='won')

        results = (0, 1)  # 0: lost, 1: won
        num_results = len(results)
        reasons = {
            constants.GameResult.ABORTED_BY_WRONG_CHOICE.value: 0,
            constants.GameResult.FINISHED.value: 1,
            constants.GameResult.DONE.value: 2
        }
        num_reasons = len(reasons)
        table = np.zeros((num_results, num_reasons, self.data_size))
        for index, (result, reason) in enumerate(zip(self.result, self.reason)):
            table[result][reasons.get(reason)][index] = 1
        for i, j in itertools.product(results, reasons.values()):
            table[i][j] = np.cumsum(table[i][j]) / self.epoch
        plt.plot(self.epoch, table[0][0], color='r', label='lost/aborted')
        plt.plot(self.epoch, table[0][1], color='g', label='lost/finished')
        plt.plot(self.epoch, table[0][2], color='b', label='lost/done')
        plt.plot(self.epoch, table[1][0], color='c', label='won/aborted')
        plt.plot(self.epoch, table[1][1], color='m', label='won/finished')
        plt.plot(self.epoch, table[1][2], color='y', label='won/done')
        plt.xlabel('epoch')
        plt.ylabel('percentage')
        plt.title('percentage by result')
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_epoch_vs_winning_percentage_moving_average(self, window):
        """plot winning percentage against epoch"""
        percent_formatter = mticker.PercentFormatter(1.0)
        fig, ax = plt.subplots()
        ax.yaxis.set_major_formatter(percent_formatter)
        plt.minorticks_on()

        plt.plot(self.epoch[window - 1:],
                 self.moving_average(self.result, window), color='k',
                 label='{}-epoch won'.format(window))

        results = (0, 1)  # 0: lost, 1: won
        num_results = len(results)
        reasons = {
            constants.GameResult.ABORTED_BY_WRONG_CHOICE.value: 0,
            constants.GameResult.FINISHED.value: 1,
            constants.GameResult.DONE.value: 2
        }
        num_reasons = len(reasons)
        table = np.zeros((num_results, num_reasons, self.data_size))
        for index, (result, reason) in enumerate(zip(self.result, self.reason)):
            table[result][reasons.get(reason)][index] = 1
        plt.plot(self.epoch[window - 1:],
                 self.moving_average(table[0][0], window), color='r',
                 label='{}-epoch lost/aborted'.format(window))
        plt.plot(self.epoch[window - 1:],
                 self.moving_average(table[0][1], window), color='g',
                 label='{}-epoch lost/finished'.format(window))
        plt.plot(self.epoch[window - 1:],
                 self.moving_average(table[0][2], window), color='b',
                 label='{}-epoch lost/done'.format(window))
        plt.plot(self.epoch[window - 1:],
                 self.moving_average(table[1][0], window), color='c',
                 label='{}-epoch won/aborted'.format(window))
        plt.plot(self.epoch[window - 1:],
                 self.moving_average(table[1][1], window), color='m',
                 label='{}-epoch won/finished'.format(window))
        plt.plot(self.epoch[window - 1:],
                 self.moving_average(table[1][2], window), color='y',
                 label='{}-epoch won/done'.format(window))
        plt.xlabel('epoch')
        plt.ylabel('percentage')
        plt.title('percentage by result/reason')
        # plt.legend()
        plt.grid(True)
        plt.show()


# TODO: duel vs time

if __name__ == '__main__':
    current_directory = os.path.dirname(os.path.realpath(__file__))
    csv_file_path = os.path.join(current_directory, 'sample.csv')
    plotter = Plotter(csv_file_path)
    plotter.plot_epoch_vs_loss(logarithmic_scale=True)
    plotter.plot_epoch_vs_time(window=20)
    plotter.plot_epoch_vs_episode(window=20)
    plotter.plot_epoch_vs_duel(window=20)
    plotter.plot_epoch_vs_winning_percentage_cumulative()
    plotter.plot_epoch_vs_winning_percentage_moving_average(window=300)
