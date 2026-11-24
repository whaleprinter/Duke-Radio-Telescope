import subprocess
import re
import numpy as np
import matplotlib.pyplot as plt
import csv

# --- 1. Define Parameter Sweeps ---
# Sweep wavelength from 5cm to 50cm (keeping D constant at 3.0m)
lambdas = np.linspace(0.05, 0.50, 20)
# Sweep diameter from 1m to 10m (keeping lambda constant at 21cm)
diameters = np.linspace(0.25, 4, 20)

# --- 2. The Execution Function ---
def run_simulation(lam, D):
    """Feeds parameters to the C executable and extracts the results."""
    process = subprocess.Popen(['./telescope'], 
                               stdin=subprocess.PIPE, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
    
    stdout, _ = process.communicate(f"{lam}\n{D}\n")
    
    # We now grab the TRUE Field of View calculation (lambda / D)
    res_match = re.search(r"Best Resolution:\s+([0-9.]+)\s+deg", stdout)
    fov_match = re.search(r"FOV \(Single Dish\):\s+([0-9.]+)\s+deg", stdout)
    
    res = float(res_match.group(1)) if res_match else 0.0
    fov = float(fov_match.group(1)) if fov_match else 0.0
        
    return res, fov

# --- 3. Run the Sweeps ---
res_vs_lam, fov_vs_lam = [], []
print("Running Wavelength Sweep...")
for lam in lambdas:
    res, fov = run_simulation(lam, 3.0) 
    res_vs_lam.append(res)
    fov_vs_lam.append(fov)

res_vs_D, fov_vs_D = [], []
print("Running Antenna Size Sweep...")
for D in diameters:
    res, fov = run_simulation(0.21, D) 
    res_vs_D.append(res)
    fov_vs_D.append(fov)

# --- 4. Export to CSV ---
csv_filename = 'telescope_sweep_data.csv'
with open(csv_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Sweep Type', 'Wavelength (m)', 'Diameter (m)', 'Resolution (deg)', 'FOV (deg)'])
    for i in range(len(lambdas)):
        writer.writerow(['Lambda Sweep', lambdas[i], 3.0, res_vs_lam[i], fov_vs_lam[i]])
    for i in range(len(diameters)):
        writer.writerow(['Diameter Sweep', 0.21, diameters[i], res_vs_D[i], fov_vs_D[i]])
print(f"Data saved to {csv_filename}")

# --- 5. Generate the Subplots ---
fig, axs = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Radio Telescope Array Characteristics', fontsize=16)

# Plot 1: Resolution vs Lambda
axs[0, 0].plot(lambdas, res_vs_lam, color='blue', marker='o')
axs[0, 0].set_title('1) Resolution vs Wavelength (Fixed D=3m)')
axs[0, 0].set_xlabel('Wavelength $\lambda$ (meters)')
axs[0, 0].set_ylabel('Resolution (Degrees)')
axs[0, 0].grid(True)

# Plot 2: Resolution vs Antenna Size (Will be flat)
axs[0, 1].plot(diameters, res_vs_D, color='red', marker='s')
axs[0, 1].set_title('2) Resolution vs Antenna Size (Fixed $\lambda$=0.21m)')
axs[0, 1].set_xlabel('Antenna Diameter D (meters)')
axs[0, 1].set_ylabel('Resolution (Degrees)')
axs[0, 1].grid(True)

# Plot 3: TRUE FOV vs Lambda
axs[1, 0].plot(lambdas, fov_vs_lam, color='green', marker='^')
axs[1, 0].set_title('3) FOV vs Wavelength (Fixed D=3m)')
axs[1, 0].set_xlabel('Wavelength $\lambda$ (meters)')
axs[1, 0].set_ylabel('Field of View (Degrees)')
axs[1, 0].grid(True)

# Plot 4: TRUE FOV vs Antenna Size (Will now be a curve!)
axs[1, 1].plot(diameters, fov_vs_D, color='purple', marker='d')
axs[1, 1].set_title('4) FOV vs Antenna Size (Fixed $\lambda$=0.21m)')
axs[1, 1].set_xlabel('Antenna Diameter D (meters)')
axs[1, 1].set_ylabel('Field of View (Degrees)')
axs[1, 1].grid(True)

plt.tight_layout()
plt.show()