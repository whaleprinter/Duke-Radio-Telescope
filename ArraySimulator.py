import argparse
import subprocess
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from scipy.signal import fftconvolve

# --- 1. CLI Argument Parsing ---
parser = argparse.ArgumentParser(description="Radio Telescope Array Simulator")
parser.add_argument('-w', '--wavelength', type=float, default=0.21, help="Observing wavelength in meters (default: 0.21)")
parser.add_argument('-d', '--diameter', type=float, default=1.0, help="Individual dish diameter in meters (default: 1.0)")
parser.add_argument('-c', '--convolve', type=str, metavar='IMAGE_FILE', help="Run convolution simulation using the provided image file")
args = parser.parse_args()

# --- 2. Execute the C Physics Engine ---
print("\nExecuting C Physics Engine...")
try:
    # Run the compiled C program and pipe the arguments into it
    process = subprocess.run(['./telescope'], 
                             input=f"{args.wavelength}\n{args.diameter}\n", 
                             text=True, 
                             capture_output=True, 
                             check=True)
    
    # Print the C program's output directly to the terminal
    print(process.stdout)
except FileNotFoundError:
    print("Error: Could not find the './telescope' executable. Please compile your C code first.")
    sys.exit(1)
except subprocess.CalledProcessError:
    print("Error: The C program crashed during execution.")
    sys.exit(1)

# --- 3. Generate the Geometry & UV Plane ---
EARTH_RADIUS = 6371000.0  
IMAGE_FOV_DEG = 1.0  
PIXELS = 500  

try:
    data = np.loadtxt('antenna_locations.txt', delimiter=',')
    lats_rad = np.radians(data[:, 0])
    lons_rad = np.radians(data[:, 1])
except Exception:
    print("Error loading 'antenna_locations.txt'. Ensure it exists and is formatted as: lat, lon")
    sys.exit(1)

ref_lat, ref_lon = lats_rad[0], lons_rad[0]
y_m = EARTH_RADIUS * (lats_rad - ref_lat)
x_m = EARTH_RADIUS * (lons_rad - ref_lon) * np.cos((ref_lat + lats_rad) / 2.0)
num_ants = len(x_m)

# Build UV points using the dynamically provided wavelength
u_coords, v_coords, baseline_labels = [], [], []
for i in range(num_ants):
    for j in range(i + 1, num_ants):
        u = (x_m[i] - x_m[j]) / args.wavelength
        v = (y_m[i] - y_m[j]) / args.wavelength
        u_coords.extend([u, -u])
        v_coords.extend([v, -v])
        baseline_labels.extend([f"A{i+1} \u2192 A{j+1}", f"A{j+1} \u2192 A{i+1}"])

u_coords = np.array(u_coords)
v_coords = np.array(v_coords)

# --- 4. Compute the Master PSF ---
print(f"Calculating {len(u_coords)} Fourier fringes for the Point Spread Function...")
fov_rad = np.radians(IMAGE_FOV_DEG)
l_axis = np.linspace(-fov_rad/2, fov_rad/2, PIXELS)
m_axis = np.linspace(-fov_rad/2, fov_rad/2, PIXELS)
L, M = np.meshgrid(l_axis, m_axis)

psf = np.zeros_like(L)
for u, v in zip(u_coords, v_coords):
    psf += np.cos(2.0 * np.pi * (u * L + v * M))
psf /= len(u_coords) # Normalize

# --- 5. Branch Logic: Convolution Mode vs. Interactive Mode ---

if args.convolve:
    # ====== CONVOLUTION MODE ======
    print(f"Loading target image: {args.convolve}")
    try:
        img = mpimg.imread(args.convolve)
        if img.ndim == 3: # Convert to grayscale if RGB
            img_gray = np.dot(img[...,:3], [0.2989, 0.5870, 0.1140])
        else:
            img_gray = img
    except Exception:
        print(f"Error: Could not load image '{args.convolve}'.")
        sys.exit(1)

    print("Convolving image with PSF (Simulating observation)...")
    # Normalize PSF sum to 1 so the resulting image doesn't blow out
    psf_normalized = psf / np.sum(np.abs(psf)) 
    simulated_observation = fftconvolve(img_gray, psf_normalized, mode='same')

    # Plotting
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    fig.canvas.manager.set_window_title('Convolution Simulation')

    ax1.imshow(img_gray, cmap='magma', origin='lower')
    ax1.set_title('True Sky (Input)')
    ax1.axis('off')

    ax2.imshow(psf, cmap='inferno', origin='lower', extent=[-IMAGE_FOV_DEG/2, IMAGE_FOV_DEG/2, -IMAGE_FOV_DEG/2, IMAGE_FOV_DEG/2])
    ax2.set_title('Point Spread Function')
    
    vmin, vmax = np.percentile(simulated_observation, [1, 99])
    ax3.imshow(simulated_observation, cmap='magma', origin='lower', vmin=vmin, vmax=vmax)
    ax3.set_title('Simulated Observation (Dirty Image)')
    ax3.axis('off')

    plt.tight_layout()
    plt.show()

else:
    # ====== INTERACTIVE GUI MODE ======
    print("Launching Interactive UV GUI...")
    fig = plt.figure(figsize=(15, 6))
    fig.canvas.manager.set_window_title('Interactive UV Plane & Fringes')

    ax1 = fig.add_subplot(131)
    scatter_plot = ax1.scatter(u_coords, v_coords, color='blue', s=15, picker=True)
    highlight_dot, = ax1.plot([], [], 'ro', markersize=8)
    ax1.set_title('UV Plane (Click a point!)')
    ax1.axhline(0, color='gray', lw=0.5); ax1.axvline(0, color='gray', lw=0.5)
    ax1.axis('equal')

    ax2 = fig.add_subplot(132)
    initial_fringe = np.cos(2.0 * np.pi * (u_coords[0] * L + v_coords[0] * M))
    fringe_img = ax2.imshow(initial_fringe, extent=[-IMAGE_FOV_DEG/2, IMAGE_FOV_DEG/2, -IMAGE_FOV_DEG/2, IMAGE_FOV_DEG/2], origin='lower', cmap='RdBu', vmin=-1, vmax=1)
    ax2.set_title(f'Selected Fringe\n({baseline_labels[0]})')

    ax3 = fig.add_subplot(133)
    im3 = ax3.imshow(psf, extent=[-IMAGE_FOV_DEG/2, IMAGE_FOV_DEG/2, -IMAGE_FOV_DEG/2, IMAGE_FOV_DEG/2], origin='lower', cmap='inferno')
    ax3.set_title('Final PSF (All Fringes Summed)')
    fig.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)

    def on_click(event):
        if event.inaxes != ax1: return
        distances = np.sqrt((u_coords - event.xdata)**2 + (v_coords - event.ydata)**2)
        idx = np.argmin(distances)
        highlight_dot.set_data([u_coords[idx]], [v_coords[idx]])
        fringe_img.set_data(np.cos(2.0 * np.pi * (u_coords[idx] * L + v_coords[idx] * M)))
        ax2.set_title(f'Selected Fringe\n({baseline_labels[idx]})\nu={u_coords[idx]:.0f}, v={v_coords[idx]:.0f}')
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.tight_layout()
    plt.show()