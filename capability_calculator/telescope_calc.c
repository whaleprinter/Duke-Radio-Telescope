#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define MAX_ANTENNAS 100
#define PI 3.14159265359
#define EARTH_RADIUS 6370913 // 6371000.0 // Mean Earth Radius in meters. Used a calculator for Durham area

typedef struct {
    int id;
    double lat_deg;
    double lon_deg;
    double x_m; // Local Cartesian X (East-West)
    double y_m; // Local Cartesian Y (North-South)
} Antenna;

double to_rad(double deg) {
    return deg * (PI / 180.0);
}

// Convert Lat/Lon to Local X/Y meters relative to the first antenna
void calculate_local_xy(Antenna *ants, int count) {
    if (count == 0) return;
    
    // Set the first antenna as the reference point (0,0)
    double ref_lat = to_rad(ants[0].lat_deg);
    double ref_lon = to_rad(ants[0].lon_deg);

    for (int i = 0; i < count; i++) {
        double lat_rad = to_rad(ants[i].lat_deg);
        double lon_rad = to_rad(ants[i].lon_deg);

        // North-South distance: R * delta_lat
        ants[i].y_m = EARTH_RADIUS * (lat_rad - ref_lat);
        
        // East-West distance: R * delta_lon * cos(avg_lat)
        // We use the average latitude for the cosine scaling to reduce distortion
        ants[i].x_m = EARTH_RADIUS * (lon_rad - ref_lon) * cos((ref_lat + lat_rad) / 2.0);
    }
}

int main() {
    FILE *fp;
    Antenna antennas[MAX_ANTENNAS];
    int count = 0;
    double wavelength, dish_diameter;

    // --- 1. User Inputs ---
    printf("Enter observing wavelength (meters) [e.g. 0.21 for Hydrogen]: ");
    if (scanf("%lf", &wavelength) != 1) return 1;

    printf("Enter individual antenna diameter (meters) [e.g. 3.0]: ");
    if (scanf("%lf", &dish_diameter) != 1) return 1;

    // --- 2. Load Map Data ---
    fp = fopen("antenna_locations.txt", "r");
    if (fp == NULL) {
        perror("Error opening file");
        printf("Make sure 'antenna_locations.txt' is in the same folder.\n");
        return 1;
    }

    printf("\n--- Loading Coordinates ---\n");
    // MODIFIED: Added comma to format string "%lf, %lf" to handle CSV
    while (count < MAX_ANTENNAS && fscanf(fp, "%lf, %lf", &antennas[count].lat_deg, &antennas[count].lon_deg) == 2) {
        antennas[count].id = count + 1;
        printf("Antenna %d: %f, %f\n", count+1, antennas[count].lat_deg, antennas[count].lon_deg);
        count++;
    }
    fclose(fp);
    printf("Successfully loaded %d antennas.\n", count);

    // --- 3. Convert to Meters ---
    calculate_local_xy(antennas, count);

    // --- 4. Calculate Baselines ---
    double max_bx = 0.0, max_by = 0.0; // Max separation in X and Y axes specifically
    double max_b_total = 0.0;          // Absolute longest baseline
    double min_b_total = 1e9;          // Shortest baseline (for Large Scale Structure)

    for (int i = 0; i < count; i++) {
        for (int j = i + 1; j < count; j++) {
            double dx = fabs(antennas[i].x_m - antennas[j].x_m);
            double dy = fabs(antennas[i].y_m - antennas[j].y_m);
            double total_dist = sqrt(dx*dx + dy*dy);

            if (dx > max_bx) max_bx = dx;
            if (dy > max_by) max_by = dy;
            if (total_dist > max_b_total) max_b_total = total_dist;
            if (total_dist < min_b_total) min_b_total = total_dist;
        }
    }

    // --- 5. Physics Calculations ---
    // Resolution (Theta = lambda / B_max)
    double res_x_rad = (max_bx > 0) ? (wavelength / max_bx) : 0;
    double res_y_rad = (max_by > 0) ? (wavelength / max_by) : 0;
    double res_total_rad = (max_b_total > 0) ? (wavelength / max_b_total) : 0;

    // Single Dish Field of View (Primary Beam ~ lambda / D) Single dish FOV
    double fov_rad = wavelength / dish_diameter;
    
    // Largest Angular Scale (lambda / B_min) When working together as an array, everything fits into this range. Total FOV
    double las_rad = (min_b_total > 0) ? (wavelength / min_b_total) : 0;

    // --- 6. Output Results ---
    printf("\n============================================\n");
    printf("TELESCOPE PERFORMANCE REPORT\n");
    printf("============================================\n");
    printf("Parameters:\n");
    printf("  Wavelength:       %.4f m\n", wavelength);
    printf("  Dish Diameter:    %.1f m\n", dish_diameter);
    printf("  Max Baseline:     %.1f m\n", max_b_total);
    printf("  Min Baseline:     %.1f m\n", min_b_total);
    printf("--------------------------------------------\n");
    printf("RESOLUTION (Synthesized Beam size):\n");
    printf("  X-Resolution:     %.4f deg (%.1f arcmin)\n", res_x_rad * (180.0/PI), (res_x_rad * (180.0/PI))*60);
    printf("  Y-Resolution:     %.4f deg (%.1f arcmin)\n", res_y_rad * (180.0/PI), (res_y_rad * (180.0/PI))*60);
    printf("  Best Resolution:  %.4f deg (%.1f arcmin)\n", res_total_rad * (180.0/PI), (res_total_rad * (180.0/PI))*60);
    printf("--------------------------------------------\n");
    printf("SINGLE DISH FIELD OF VIEW:\n");
    printf("  FOV (Single Dish): %.2f deg\n", fov_rad * (180.0/PI));
    printf("--------------------------------------------\n");
    printf("SENSITIVITY LIMITS:\n");
    printf("  Total FOV: %.2f deg\n", las_rad * (180.0/PI));
    printf("============================================\n");

    return 0;
}