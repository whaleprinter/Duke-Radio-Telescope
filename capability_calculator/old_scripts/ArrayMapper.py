import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patheffects as pe
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "posters" / "fall-2026"))
import poster_style as ps
FIG_DIR = Path(__file__).resolve().parents[2] / "posters" / "fall-2026" / "figures"

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

# --- 4. Background Map Placement ---
# DukeMap.png edges in FEET relative to A1, hand-calibrated in MapOverlay.py,
# where the map is scaled so A1-A2 is exactly 250 ft. Convert with that same
# scale so the map lines up with the antennas the same way here (in meters).
MAP_EXTENT_FT = [-1250, 1200, -884, 800]   # left, right, bottom, top
ft_per_m = 250.0 / np.hypot(x_m[1] - x_m[0], y_m[1] - y_m[0])
map_extent_m = [v / ft_per_m for v in MAP_EXTENT_FT]

# --- 5. Plot the Array Geometry ---
ps.use()
fig, ax = plt.subplots(figsize=ps.figsize(aspect=0.75))

try:
    ax.imshow(mpimg.imread('DukeMap.png'), extent=map_extent_m, zorder=0)
except FileNotFoundError:
    print("Warning: 'DukeMap.png' not found. Plotting without background map.")

# Antennas
ax.scatter(x_m, y_m, c=ps.ROYAL, marker='o', s=140, edgecolor='white', linewidth=1.5, zorder=3)

# Label each antenna (A3's label goes to the left of its dot so it doesn't collide with A1)
# Label each antenna (A1, A2, etc.) with a white halo so it reads over the map
halo = [pe.withStroke(linewidth=4, foreground='white')]
for i in range(num_antennas):
    ax.annotate(f"A{i+1}", (x_m[i], y_m[i]), textcoords="offset points",
                xytext=(-12, -8) if i == 2 else (0, 12),
                ha='right' if i == 2 else 'center', fontsize=18, color=ps.NAVY,
                path_effects=halo, zorder=4)

# Longest baseline: the one thing to notice
ax.plot([x_m[p1_idx], x_m[p2_idx]], [y_m[p1_idx], y_m[p2_idx]],
        '--', color=ps.RUST, linewidth=3, path_effects=halo,
        label=f'Max baseline ($B_{{max}}$ = {max_b:.0f} m)', zorder=2)

ps.title(ax, 'Interferometer Array Geometry', pad=40)
ax.set_xlabel('East-West Distance (m)')
ax.set_ylabel('North-South Distance (m)')

# Equal scale on both axes, cropped to the array with some margin
pad = 60
ax.set_aspect('equal')
# (clamped to the map so there's no blank band past its edge)
ax.set_xlim(max(x_m.min() - pad, map_extent_m[0]), min(x_m.max() + pad, map_extent_m[1]))
ax.set_ylim(max(y_m.min() - pad, map_extent_m[2]), min(y_m.max() + pad, map_extent_m[3]))
ax.grid(False)

leg = ax.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.85, edgecolor='none')

plt.tight_layout()
ps.save(fig, FIG_DIR / "array_geometry")
plt.show()
