import matplotlib.pyplot as plt
import numpy as np
import os

current_directory = os.path.dirname(os.path.realpath(__file__))
csv_file_path = os.path.join(current_directory, 'sample.csv')
data = np.genfromtxt(csv_file_path, delimiter=',',
                     names=['epoch', 'loss', 'episode', 'result', 'reason',
                            'duel', 'time', 'color'])

# TODO: epoch vs loss (logarithmic y-axis)
plt.plot(data['epoch'], data['loss'], color='r', label='sample')
plt.ticklabel_format(style='sci', axis='loss', scilimits=(0, 0))
plt.xlabel('epoch')
plt.ylabel('loss')
plt.title('epoch vs loss')
plt.legend()
plt.show()

# TODO: epoch vs time
plt.plot(data['epoch'], data['time'], color='r', label='sample')
plt.xlabel('epoch')
plt.ylabel('time')
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
