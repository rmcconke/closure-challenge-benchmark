# import matplotlib.pyplot as plt

# # use plt.Axes(figure, [left, bottom, width, height])
# # where each value in the frame is between 0 and 1

# # left
# figure = plt.figure(figsize=(10,3))
# ax1 = plt.Axes(figure, [.1, .1, .25, .80])
# figure.add_axes(ax1)
# ax1.plot([1, 2, 3], [1, 2, 3])

# # middle
# ax2 = plt.Axes(figure, [.4, .1, .25, .80])
# figure.add_axes(ax2)
# ax2.plot([1, 2, 3], [1, 2, 3])

# # right
# ax3= plt.Axes(figure, [.7, .1, .25, .99])
# figure.add_axes(ax3)
# ax3.plot([1, 2, 3], [1, 2, 3])

# plt.show()
import matplotlib.pyplot as plt
import numpy as np

# Fixing random state for reproducibility
np.random.seed(19680801)

plt.subplot(211)
plt.imshow(np.random.random((100, 100)))
plt.subplot(212)
plt.imshow(np.random.random((100, 100)))

plt.subplots_adjust(bottom=0.1, right=0.8, top=0.9)
cax = plt.axes((0.85, 0.1, 0.075, 0.8))
plt.colorbar(cax=cax)

plt.show()