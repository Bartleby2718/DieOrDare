import matplotlib.pyplot as plt
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


# TODO: epoch vs duel
# TODO: loss vs result
# TODO: loss vs reason
# TODO: loss vs duel
# TODO: loss vs color
# TODO: duel vs time
# TODO: epoch vs winning percentage

if __name__ == '__main__':
    current_directory = os.path.dirname(os.path.realpath(__file__))
    csv_file_path = os.path.join(current_directory, 'sample.csv')
    plotter = Plotter(csv_file_path)
    plotter.plot_epoch_vs_loss(logarithmic_scale=True)
    plotter.plot_epoch_vs_time(window=20)
    plotter.plot_epoch_vs_episode(window=20)
