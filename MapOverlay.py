import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# --- 1. Load Data ---
try:
    data = np.loadtxt('antenna_locations.txt', delimiter=',')
    lats_deg = data[:, 0]
    lons_deg = data[:, 1]
except Exception as e:
    print("Error: Could not load 'antenna_locations.txt'.")
    exit()

# --- 2. Convert to Local Cartesian (Raw Math) ---
lats_rad = np.radians(lats_deg)
lons_rad = np.radians(lons_deg)

# Set Antenna 1 as the exact (0,0) origin point
ref_lat = lats_rad[0]
ref_lon = lons_rad[0]

# Calculate rough local X and Y (Equirectangular projection)
EARTH_RADIUS = 6371000.0
y_raw = EARTH_RADIUS * (lats_rad - ref_lat)
x_raw = EARTH_RADIUS * (lons_rad - ref_lon) * np.cos((ref_lat + lats_rad) / 2.0)

# --- 3. Scale to the 250ft Baseline ---
# Calculate the raw, unscaled distance between A1 (index 0) and A2 (index 1)
raw_a1_a2_dist = np.sqrt((x_raw[1] - x_raw[0])**2 + (y_raw[1] - y_raw[0])**2)

# Create a scaling factor to force that distance to be exactly 250
scale_factor = 250.0 / raw_a1_a2_dist

# Apply the scale factor. Now all coordinates are perfectly scaled in FEET.
x_ft = x_raw * scale_factor
y_ft = y_raw * scale_factor

print(f"Calibration successful: A1 to A2 distance is now {np.sqrt((x_ft[1] - x_ft[0])**2 + (y_ft[1] - y_ft[0])**2):.2f} feet.")

# --- 4. Plotting and Image Overlay ---
fig, ax = plt.subplots(figsize=(12, 10))

# ==========================================
# CALIBRATION ZONE: Tweak these 4 numbers!
# These represent the physical boundaries of your image in FEET 
# relative to Antenna 1 at (0,0). You will need to guess and check 
# these until the map aligns with the red dots.
# ==========================================
img_left   = -1250   # How many feet to the left of A1 the image starts
img_right  =  1200  # How many feet to the right of A1 the image ends
img_bottom = -884  # How many feet below A1 the image starts
img_top    =  800   # How many feet above A1 the image ends

try:
    # Load the background image
    img = mpimg.imread('DukeMap.png')
    
    # Display the image using the extent boundaries defined above
    ax.imshow(img, extent=[img_left, img_right, img_bottom, img_top], zorder=1)
except FileNotFoundError:
    print("Warning: 'DukeMap.png' not found. Plotting points without background.")

# Plot the scaled antennas as red dots on top (zorder=2 ensures they are above the image)
ax.scatter(x_ft, y_ft, c='red', marker='o', s=80, edgecolor='black', zorder=2)

# Label each antenna 
for i in range(len(x_ft)):
    ax.annotate(f"A{i+1}", (x_ft[i], y_ft[i]), textcoords="offset points", 
                 xytext=(0, 8), ha='center', fontsize=10, fontweight='bold', 
                 color='black', backgroundcolor='white')

# Graph styling
ax.set_title('Interferometer Array Layout', fontsize=14)
ax.set_xlabel('East-West Distance (feet)')
ax.set_ylabel('North-South Distance (feet)')

# Draw origin axes to clearly show Antenna 1 at (0,0)
ax.axhline(0, color='yellow', linestyle='-', linewidth=1, zorder=3, alpha=0.5)
ax.axvline(0, color='yellow', linestyle='-', linewidth=1, zorder=3, alpha=0.5)

plt.axis('equal') # Prevents distortion
plt.show()