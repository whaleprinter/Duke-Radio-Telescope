import numpy as np
import matplotlib.pyplot as plt

# Constants
EARTH_RADIUS = 6371000.0  # Mean Earth Radius in meters

# --- 1. Load Data ---
try:
    # Read the CSV file
    data = np.loadtxt('antenna_locations.txt', delimiter=',')
    lats_deg = data[:, 0]
    lons_deg = data[:, 1]
except Exception as e:
    print("Error: Could not load 'antenna_locations.txt'.")
    print("Ensure the file exists and is formatted strictly as: lat, lon")
    exit()

# --- 2. Convert to Local Cartesian (Meters) ---
# Convert degrees to radians
lats_rad = np.radians(lats_deg)
lons_rad = np.radians(lons_deg)

# Set the first antenna as the (0,0) origin point
ref_lat = lats_rad[0]
ref_lon = lons_rad[0]

# Calculate local X and Y in meters
y_m = EARTH_RADIUS * (lats_rad - ref_lat)
x_m = EARTH_RADIUS * (lons_rad - ref_lon) * np.cos((ref_lat + lats_rad) / 2.0)

# --- 3. Find the Maximum Baseline ---
max_b = 0
p1_idx, p2_idx = 0, 0
num_antennas = len(x_m)

for i in range(num_antennas):
    for j in range(i + 1, num_antennas):
        dist = np.sqrt((x_m[i] - x_m[j])**2 + (y_m[i] - y_m[j])**2)
        if dist > max_b:
            max_b = dist
            p1_idx = i
            p2_idx = j

# --- 4. Plot the Array Geometry ---
plt.figure(figsize=(10, 8))

# Plot the antennas as red dots
plt.scatter(x_m, y_m, c='red', marker='o', s=100, edgecolor='black', zorder=3)

# Label each antenna (A1, A2, etc.)
for i in range(num_antennas):
    plt.annotate(f"A{i+1}", (x_m[i], y_m[i]), textcoords="offset points", 
                 xytext=(0, 10), ha='center', fontsize=9, fontweight='bold')

# Draw a dashed blue line between the two antennas forming the longest baseline
plt.plot([x_m[p1_idx], x_m[p2_idx]], [y_m[p1_idx], y_m[p2_idx]], 
         'b--', linewidth=1.5, label=f'Max Baseline ($B_{{max}}$ = {max_b:.1f} m)', zorder=2)

# Graph styling
plt.title('Interferometer Array Geometry', fontsize=14)
plt.xlabel('East-West Distance (meters)')
plt.ylabel('North-South Distance (meters)')

# Add origin axes for reference
plt.axhline(0, color='gray', linestyle='-', linewidth=0.5, zorder=1)
plt.axvline(0, color='gray', linestyle='-', linewidth=0.5, zorder=1)

# CRITICAL: This ensures 100 meters on the X axis is physically the same 
# visual length as 100 meters on the Y axis, preventing distortion.
plt.axis('equal') 

plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.show()