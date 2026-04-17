import numpy as np
import matplotlib.pyplot as plt

# --- Parameters ---
WAVELENGTH = 0.21  # meters
EARTH_RADIUS = 6371000.0  # meters
IMAGE_FOV_DEG = 1.0  # How wide of a patch of sky to simulate (degrees)
PIXELS = 500  # Resolution of the simulated image (500x500)

# --- 1. Load and Convert Geometry ---
try:
    data = np.loadtxt('antenna_locations.txt', delimiter=',')
    lats_rad = np.radians(data[:, 0])
    lons_rad = np.radians(data[:, 1])
except Exception as e:
    print("Error loading 'antenna_locations.txt'.")
    exit()

ref_lat = lats_rad[0]
ref_lon = lons_rad[0]

y_m = EARTH_RADIUS * (lats_rad - ref_lat)
x_m = EARTH_RADIUS * (lons_rad - ref_lon) * np.cos((ref_lat + lats_rad) / 2.0)
num_ants = len(x_m)

# --- 2. Map to 2D Fourier Space (UV Plane) ---
u_coords = []
v_coords = []
baseline_labels = []

for i in range(num_ants):
    for j in range(i + 1, num_ants):
        u = (x_m[i] - x_m[j]) / WAVELENGTH
        v = (y_m[i] - y_m[j]) / WAVELENGTH
        
        # Add both (u,v) and (-u,-v) 
        u_coords.extend([u, -u])
        v_coords.extend([v, -v])
        
        # Track which antennas made this point for the UI
        baseline_labels.extend([f"Antennas {i+1} \u2192 {j+1}", f"Antennas {j+1} \u2192 {i+1}"])

u_coords = np.array(u_coords)
v_coords = np.array(v_coords)

# --- 3. Setup the Image Plane (LM Plane) ---
fov_rad = np.radians(IMAGE_FOV_DEG)
l_axis = np.linspace(-fov_rad/2, fov_rad/2, PIXELS)
m_axis = np.linspace(-fov_rad/2, fov_rad/2, PIXELS)
L, M = np.meshgrid(l_axis, m_axis)

# Calculate the master Point Spread Function (PSF) once
psf = np.zeros_like(L)
print(f"Calculating {len(u_coords)} Fourier fringes for the master PSF...")
for u, v in zip(u_coords, v_coords):
    psf += np.cos(2.0 * np.pi * (u * L + v * M))
psf /= len(u_coords)

# --- 4. Interactive GUI Setup ---
fig = plt.figure(figsize=(15, 6))
fig.canvas.manager.set_window_title('Interferometry UI')

# Subplot 1: UV Plane
ax1 = fig.add_subplot(131)
scatter_plot = ax1.scatter(u_coords, v_coords, color='blue', s=15, picker=True)
highlight_dot, = ax1.plot([], [], 'ro', markersize=8) # The red selection dot
ax1.set_title('UV Plane (Click a point!)')
ax1.set_xlabel('u (wavelengths)')
ax1.set_ylabel('v (wavelengths)')
ax1.axhline(0, color='gray', lw=0.5)
ax1.axvline(0, color='gray', lw=0.5)
ax1.axis('equal')

# Subplot 2: The Individual Sinusoid
ax2 = fig.add_subplot(132)
# Initialize with the first baseline
initial_fringe = np.cos(2.0 * np.pi * (u_coords[0] * L + v_coords[0] * M))
fringe_img = ax2.imshow(initial_fringe, extent=[-IMAGE_FOV_DEG/2, IMAGE_FOV_DEG/2, -IMAGE_FOV_DEG/2, IMAGE_FOV_DEG/2], origin='lower', cmap='RdBu', vmin=-1, vmax=1)
ax2.set_title(f'Selected Fringe\n({baseline_labels[0]})')
ax2.set_xlabel('East-West (Degrees)')
ax2.set_ylabel('North-South (Degrees)')

# Subplot 3: The Superposition (PSF)
ax3 = fig.add_subplot(133)
im3 = ax3.imshow(psf, extent=[-IMAGE_FOV_DEG/2, IMAGE_FOV_DEG/2, -IMAGE_FOV_DEG/2, IMAGE_FOV_DEG/2], origin='lower', cmap='inferno')
ax3.set_title('Final Point Spread Function\n(All Fringes Summed)')
ax3.set_xlabel('East-West (Degrees)')
ax3.set_ylabel('North-South (Degrees)')
fig.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)

# --- 5. Event Handling Logic ---
def on_click(event):
    if event.inaxes != ax1:
        return # Ignore clicks outside the UV plot
    
    # Find the closest UV point to the mouse click
    distances = np.sqrt((u_coords - event.xdata)**2 + (v_coords - event.ydata)**2)
    closest_idx = np.argmin(distances)
    
    # Update the highlight dot on the UV plot
    sel_u = u_coords[closest_idx]
    sel_v = v_coords[closest_idx]
    highlight_dot.set_data([sel_u], [sel_v])
    
    # Calculate the new sinusoid for this specific point
    new_fringe = np.cos(2.0 * np.pi * (sel_u * L + sel_v * M))
    
    # Update the middle image and title
    fringe_img.set_data(new_fringe)
    ax2.set_title(f'Selected Fringe\n({baseline_labels[closest_idx]})\nu={sel_u:.0f}, v={sel_v:.0f}')
    
    # Redraw the canvas to show changes
    fig.canvas.draw_idle()

# Bind the click event to the figure
fig.canvas.mpl_connect('button_press_event', on_click)

plt.tight_layout()
plt.show()