import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import os


class Plotter(object):
    def __init__(self, path_to_csv_file):
        data = np.genfromtxt(path_to_csv_file, delimiter=',',
                             names=['epoch', 'loss', 'episode', 'result',
                                    'reason', 'duel', 'time', 'color'])
        self.epoch = data['epoch']
        self.loss = data['loss']
        self.episode = data['episode']
        self.result = data['result']
        self.reason = data['reason']
        self.duel = data['duel']
        self.time = data['time']
        self.color = data['color']

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

    def plot_epoch_vs_winning_percentage(self, window):
        """plot winning percentage against epoch"""
        percent_formatter = mticker.PercentFormatter(1.0)
        fig, ax = plt.subplots()
        ax.yaxis.set_major_formatter(percent_formatter)
        plt.minorticks_on()

        games_won = np.cumsum(self.result)
        winning_percentage = np.true_divide(games_won, self.epoch)
        plt.plot(self.epoch, winning_percentage, color='r',
                 label='cum. mov. avg.')

        winning_percentage_windowed = self.moving_average(self.result, window)
        plt.plot(self.epoch[window - 1:], winning_percentage_windowed,
                 color='b', label='{}-epoch mov. avg.'.format(window))

        mean = np.mean(self.result)
        epoch_min = min(self.epoch)
        epoch_max = max(self.epoch)
        plt.hlines(y=mean, xmin=epoch_min, xmax=epoch_max, colors='g',
                   linestyles='solid', label='avg.', zorder=10)
        plt.xlabel('epoch')
        plt.ylabel('winning percentage')
        plt.title('epoch vs winning percentage')
        plt.legend()
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
    plotter.plot_epoch_vs_winning_percentage(window=100)
