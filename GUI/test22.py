import numpy as np
import matplotlib.pyplot as plt

# Sample data: Replace this with your actual data
x = np.linspace(0, 10, 1000)
y = np.piecewise(x, [x < 5, x >= 5], [lambda x: np.sin(x), lambda x: 2 * np.sin(x)])

# Compute the first derivative of the curve
dy_dx = np.gradient(y, x)

# Set a threshold to identify points with abrupt changes
threshold = np.mean(np.abs(dy_dx)) + 2 * np.std(np.abs(dy_dx))

# Identify points with abrupt changes
abrupt_change_points = np.where(np.abs(dy_dx) > threshold)[0]

# Segment the curve based on abrupt change points
segments = []
start = 0
for point in abrupt_change_points:
    segments.append((start, point))
    start = point + 1
segments.append((start, len(x) - 1))

# Plot the original curve and the segments
plt.figure(figsize=(10, 6))
plt.plot(x, y, label='Original Curve')

for (start, end) in segments:
    if start != end:
        plt.plot(x[start:end+1], y[start:end+1], label=f'Segment {start}-{end}')

plt.axhline(y=threshold, color='r', linestyle='--', label='Threshold')
plt.axhline(y=-threshold, color='r', linestyle='--')
plt.legend()
plt.xlabel('X')
plt.ylabel('Y')
plt.title('Curve Segmentation')
plt.show()

# Optionally, print segments information
for i, (start, end) in enumerate(segments):
    segment_type = "Abrupt" if i in abrupt_change_points else "Slow"
    print(f"Segment {i}: {segment_type} change from index {start} to {end}")
