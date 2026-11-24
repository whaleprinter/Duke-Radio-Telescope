"""poster_figure.py -- one figure for the Fall 2026 poster's "Baseline Simulation" block.

Run it from anywhere:

    python3 poster_figure.py                # default: lambda = 21 cm, fringe from A1-A2
    python3 poster_figure.py --baseline 3 4 # show a different example fringe
    python3 poster_figure.py --show         # also open a window after saving

It draws six panels in a 2 x 3 grid, in the order the poster tells the story:

    Array geometry | UV plane           | Example fringe
    PSF            | True sky (example) | Simulated observation

and saves them as one figure to

    ./array_simulation.pdf and ./array_simulation.png   (this folder)
    ./Fall 2026 Poster/figures/array_simulation.pdf     (the poster)

Styling comes from poster_style.py in the poster folder, so fonts, colours and
transparent background match the poster. The figure is drawn at the full block
width, so include it in LaTeX with \\includegraphics[width=\\linewidth]{...}.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
POSTER_DIR = HERE / "Fall 2026 Poster"
POSTER_FIG_DIR = POSTER_DIR / "figures"
OUT_NAME = "array_simulation"

ANTENNA_FILE = HERE / "antenna_locations.txt"
MAP_FILE = HERE / "DukeMap.png"
SKY_FILE = HERE / "Galaxy.jpg"

EARTH_RADIUS = 6371000.0   # m
PSF_FOV_DEG = 1.0          # width of the fringe / PSF panels
PSF_PIXELS = 500
SKY_FOV_DEG = 8.5          # angular width given to the example sky image
SKY_PIXELS = 1000          # sky image is resampled to this many pixels across

# DukeMap.png edges in feet relative to A1, hand-calibrated so that A1-A2 is
# exactly 250 ft (see the old MapOverlay.py in git history).
MAP_EXTENT_FT = (-1250, 1200, -884, 800)   # left, right, bottom, top


# --------------------------------------------------------------------------
#  Physics
# --------------------------------------------------------------------------
def load_array(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Antenna (lat, lon) in degrees -> local East/North metres relative to A1."""
    data = np.loadtxt(path, delimiter=",")
    lat, lon = np.radians(data[:, 0]), np.radians(data[:, 1])
    y = EARTH_RADIUS * (lat - lat[0])
    x = EARTH_RADIUS * (lon - lon[0]) * np.cos((lat[0] + lat) / 2.0)
    return x, y


def uv_points(x, y, wavelength):
    """Every baseline (i < j) and its mirror, in wavelengths."""
    i, j = np.triu_indices(len(x), k=1)
    u = (x[i] - x[j]) / wavelength
    v = (y[i] - y[j]) / wavelength
    return np.concatenate([u, -u]), np.concatenate([v, -v])


def sky_grid(fov_deg: float, pixels: int):
    half = np.radians(fov_deg) / 2
    axis = np.linspace(-half, half, pixels)
    return np.meshgrid(axis, axis)


def fringe(u, v, L, M):
    return np.cos(2.0 * np.pi * (u * L + v * M))


def psf_on(u, v, L, M):
    """PSF = average of every baseline's fringe."""
    out = np.zeros_like(L)
    for uk, vk in zip(u, v):
        out += fringe(uk, vk, L, M)
    return out / len(u)


def load_sky(path: Path, pixels: int) -> np.ndarray:
    """Greyscale example sky, resampled to pixels x pixels, scaled 0..1."""
    from PIL import Image
    img = Image.open(path).convert("L").resize((pixels, pixels), Image.LANCZOS)
    arr = np.asarray(img, dtype=float)[::-1]   # flip so origin='lower' is upright
    return (arr - arr.min()) / (np.ptp(arr) or 1.0)


def observe(sky, u, v, sky_fov_deg, psf_fov_deg):
    """Convolve the sky with the PSF sampled at the sky image's pixel scale."""
    from scipy.signal import fftconvolve
    n = round(sky.shape[0] * psf_fov_deg / sky_fov_deg) | 1   # odd, so it's centred
    L, M = sky_grid(psf_fov_deg, n)
    kernel = psf_on(u, v, L, M)
    kernel /= np.abs(kernel).sum()
    return fftconvolve(sky, kernel, mode="same")


# --------------------------------------------------------------------------
#  Figure
# --------------------------------------------------------------------------
def build_figure(args):
    import matplotlib
    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.image as mpimg
    import matplotlib.patheffects as pe
    import matplotlib.pyplot as plt

    sys.path.insert(0, str(POSTER_DIR))
    import poster_style as ps

    # --- numbers -------------------------------------------------------
    x, y = load_array(ANTENNA_FILE)
    n_ant = len(x)
    a, b = args.baseline[0] - 1, args.baseline[1] - 1
    if not (0 <= a < n_ant and 0 <= b < n_ant and a != b):
        sys.exit(f"--baseline must name two different antennas between 1 and {n_ant}")

    u, v = uv_points(x, y, args.wavelength)
    u_ex, v_ex = (x[a] - x[b]) / args.wavelength, (y[a] - y[b]) / args.wavelength

    L, M = sky_grid(PSF_FOV_DEG, PSF_PIXELS)
    print(f"{n_ant} antennas -> {n_ant * (n_ant - 1) // 2} baselines -> {len(u)} UV points")
    print("Summing fringes for the PSF ...")
    psf = psf_on(u, v, L, M)
    ex_fringe = fringe(u_ex, v_ex, L, M)

    print(f"Simulating an observation of {SKY_FILE.name} ...")
    sky = load_sky(SKY_FILE, SKY_PIXELS)
    observed = observe(sky, u, v, SKY_FOV_DEG, PSF_FOV_DEG)

    dists = np.hypot(x[:, None] - x[None, :], y[:, None] - y[None, :])
    b_max = dists.max()
    print(f"Longest baseline: {b_max:.0f} m  ->  resolution ~ lambda/B = "
          f"{np.degrees(args.wavelength / b_max) * 60:.1f} arcmin")

    # --- layout --------------------------------------------------------
    ps.use(base_pt=args.font_pt)
    fig, axes = plt.subplots(2, 3, figsize=ps.figsize(aspect=args.aspect),
                             layout="constrained")
    fig.get_layout_engine().set(w_pad=0.08, h_pad=0.08, wspace=0.06, hspace=0.06)
    (ax_geo, ax_uv, ax_fr), (ax_psf, ax_sky, ax_obs) = axes
    halo = [pe.withStroke(linewidth=4, foreground="white")]
    ext = [-PSF_FOV_DEG / 2, PSF_FOV_DEG / 2] * 2
    sky_ext = [-SKY_FOV_DEG / 2, SKY_FOV_DEG / 2] * 2

    # 1. Array geometry on the campus map
    if MAP_FILE.exists():
        ft_per_m = 250.0 / np.hypot(x[1] - x[0], y[1] - y[0])
        map_ext = [e / ft_per_m for e in MAP_EXTENT_FT]
        ax_geo.imshow(mpimg.imread(MAP_FILE), extent=map_ext, zorder=0)
    else:
        print(f"Warning: {MAP_FILE.name} not found, drawing the array without a map.")
        map_ext = [-np.inf, np.inf, -np.inf, np.inf]
    ax_geo.scatter(x, y, s=60, c=ps.ROYAL, edgecolor="white", linewidth=1.2, zorder=3)
    ax_geo.plot(x[[a, b]], y[[a, b]], color=ps.RUST, lw=3, path_effects=halo, zorder=2)
    for k in (a, b):
        ax_geo.annotate(f"A{k + 1}", (x[k], y[k]), textcoords="offset points",
                        xytext=(0, 10), ha="center", fontsize=args.font_pt * 0.8,
                        color=ps.NAVY, path_effects=halo, zorder=4)
    # square window around the array (so it matches the other panels),
    # slid back inside the map if it would run off an edge
    half = max(np.ptp(x), np.ptp(y)) / 2 + 40
    for lim, centre, lo_edge, hi_edge in ((ax_geo.set_xlim, x.mean(), *map_ext[:2]),
                                          (ax_geo.set_ylim, y.mean(), *map_ext[2:])):
        c = min(max(centre, lo_edge + half), hi_edge - half)
        lim(c - half, c + half)
    ax_geo.set_aspect("equal")
    ax_geo.grid(False)
    ax_geo.set_xlabel("East (m)")
    ax_geo.set_ylabel("North (m)")
    ps.title(ax_geo, "Array geometry")

    # 2. UV plane (in kilo-wavelengths so the ticks stay short)
    ax_uv.scatter(u / 1e3, v / 1e3, s=14, c=ps.ROYAL, linewidths=0)
    ax_uv.scatter([u_ex / 1e3, -u_ex / 1e3], [v_ex / 1e3, -v_ex / 1e3],
                  s=110, c=ps.RUST, edgecolor="white", linewidth=1.2, zorder=3)
    ax_uv.axhline(0, color=ps.HAIRLINE, lw=1, zorder=0)
    ax_uv.axvline(0, color=ps.HAIRLINE, lw=1, zorder=0)
    ax_uv.set_aspect("equal", adjustable="datalim")
    ax_uv.set_xlabel(r"$u$ (k$\lambda$)")
    ax_uv.set_ylabel(r"$v$ (k$\lambda$)")
    ax_uv.grid(False)
    ps.title(ax_uv, r"$uv$ plane")

    # 3. Example fringe from the highlighted baseline
    ax_fr.imshow(ex_fringe, extent=ext, origin="lower", cmap="RdBu_r", vmin=-1, vmax=1)
    ps.title(ax_fr, f"Fringe (A{a + 1}–A{b + 1})")

    # 4. PSF = all fringes summed
    ax_psf.imshow(psf, extent=ext, origin="lower", cmap="inferno")
    ps.title(ax_psf, "PSF (all fringes)")

    # 5. Example true sky
    ax_sky.imshow(sky, extent=sky_ext, origin="lower", cmap="magma")
    ps.title(ax_sky, "True sky (example)")

    # 6. Simulated observation = sky * PSF
    lo, hi = np.percentile(observed, [1, 99])
    ax_obs.imshow(observed, extent=sky_ext, origin="lower", cmap="magma", vmin=lo, vmax=hi)
    ps.title(ax_obs, "Simulated observation")

    for ax in (ax_fr, ax_psf, ax_sky, ax_obs):
        ax.grid(False)
        ax.set_xlabel("Offset (deg)")
    for ax in (ax_fr, ax_psf):
        ax.set_xticks([-0.5, 0, 0.5])
        ax.set_yticks([-0.5, 0, 0.5])
    for ax in (ax_sky, ax_obs):
        ax.set_xticks([-4, 0, 4])
        ax.set_yticks([-4, 0, 4])

    return fig, ps, plt


def main():
    p = argparse.ArgumentParser(description="Make the array-simulation poster figure.")
    p.add_argument("-w", "--wavelength", type=float, default=0.21,
                   help="observing wavelength in metres (default 0.21)")
    p.add_argument("-b", "--baseline", type=int, nargs=2, default=(1, 2), metavar=("I", "J"),
                   help="antenna pair whose fringe is shown (default 1 2)")
    p.add_argument("--font-pt", type=float, default=22,
                   help="axis-label size in points on the printed poster (default 22)")
    p.add_argument("--aspect", type=float, default=0.70,
                   help="figure height / width (default 0.70)")
    p.add_argument("--no-poster", action="store_true",
                   help="only save into this folder, not the poster's figures folder")
    p.add_argument("--show", action="store_true", help="open a window after saving")
    args = p.parse_args()

    fig, ps, plt = build_figure(args)

    # The map and sky panels are bitmaps, which the PDF stores at the save
    # dpi: 300 keeps them sharp in print (a panel is ~3.6 in wide on the poster).
    saved = [ps.save(fig, HERE / OUT_NAME, dpi=300),
             ps.save(fig, HERE / f"{OUT_NAME}.png", dpi=200)]
    if not args.no_poster:
        saved.append(ps.save(fig, POSTER_FIG_DIR / OUT_NAME, dpi=300))
    print("Saved:")
    for path in saved:
        print("  ", path)

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
