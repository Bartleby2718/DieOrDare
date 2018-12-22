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

epoch = data['epoch']
loss = data['loss']
episode = data['episode']
result = data['result']
reason = data['reason']
duel = data['duel']
time = data['time']
color = data['color']

# epoch vs loss (logarithmic y-axis)
plt.plot(epoch, loss, color='r', label='loss')
plt.xlabel('epoch')
plt.ylabel('loss')
plt.yscale('log')
plt.title('epoch vs loss')
plt.legend()
plt.show()

# epoch vs time
window = 20
moving_average_time = moving_average(time, window)
plt.plot(epoch, time, color='r', label='time elapsed')
plt.plot(epoch[window - 1:], moving_average_time, color='b',
         label='{}-epoch mov. avg.'.format(window))
mean = np.mean(time)
epoch_min = min(epoch)
epoch_max = max(epoch)
plt.hlines(y=mean, xmin=epoch_min, xmax=epoch_max, colors='g',
           linestyles='solid', label='cum. avg.')
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
