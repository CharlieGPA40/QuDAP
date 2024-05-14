import matplotlib.pyplot as plt

# Sample y data - could be any list of numbers
y_data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]

# Plotting only y data; Matplotlib uses the index of each data point as the x value
plt.plot(y_data)

# Adding title and labels
plt.title('Plot of Y Data Using Index as X Axis')
plt.xlabel('Index of Y Data')
plt.ylabel('Y Data Value')

# Display the plot
plt.show()
