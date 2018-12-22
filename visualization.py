import matplotlib.pyplot as plt
import numpy as np
import os


def moving_average(array_like, window):
    cumulative_sum = np.cumsum(np.insert(array_like, 0, 0))
    return (cumulative_sum[window:] - cumulative_sum[:-window]) / float(window)


current_directory = os.path.dirname(os.path.realpath(__file__))
csv_file_path = os.path.join(current_directory, 'sample.csv')
data = np.genfromtxt(csv_file_path, delimiter=',',
                     names=['epoch', 'loss', 'episode', 'result', 'reason',
                            'duel', 'time', 'color'])

# epoch vs loss (logarithmic y-axis)
plt.plot(data['epoch'], data['loss'], color='r', label='loss')
plt.xlabel('epoch')
plt.ylabel('loss')
plt.yscale('log')
plt.title('epoch vs loss')
plt.legend()
plt.show()

# TODO: epoch vs time
window = 20
moving_average_time = moving_average(data['time'], window)
plt.plot(data['epoch'], data['time'], color='r', label='time elapsed')
plt.plot(data['epoch'][window - 1:], moving_average_time, color='b',
         label='{}-epoch mov. avg.'.format(window))
plt.xlabel('epoch')
plt.ylabel('time (seconds)')
plt.title('epoch vs time')
plt.legend()
plt.show()

# TODO: epoch vs episode
# TODO: epoch vs duel
# TODO: loss vs result
# TODO: loss vs reason
# TODO: loss vs duel
# TODO: loss vs color
# TODO: duel vs time
# TODO: epoch vs winning percentage
