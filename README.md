# Duke Radio Telescope: Capability Calculator

## Poster figure (one command)

```bash
python3 poster_figure.py
```

This produces one 2 × 3 figure: array geometry on the campus map, the UV plane,
an example fringe, the PSF, the example true sky, and the simulated observation.
It is saved to:

- `array_simulation.pdf` and `array_simulation.png` in this folder
- `Fall 2026 Poster/figures/array_simulation.pdf` for the poster

The style (fonts, colours, transparent background) comes from
`Fall 2026 Poster/poster_style.py`. The figure is drawn at full block width,
so include it with `\includegraphics[width=\linewidth]{figures/array_simulation.pdf}`.

Useful options (`python3 poster_figure.py -h` lists them all):

| option | what it does |
|---|---|
| `-w 0.21` | observing wavelength in metres |
| `-b 3 4` | which antenna pair's fringe to show (highlighted on the map and UV plane) |
| `--font-pt 22` | axis-label size on the printed poster |
| `--aspect 0.70` | figure height ÷ width |
| `--no-poster` | only save in this folder |
| `--show` | open a window after saving |

## Inputs

- `antenna_locations.txt`: one `lat, lon` per line; A1 is the first line
- `DukeMap.png`: campus map background
- `Galaxy.jpg`: example sky used for the simulated observation

## Other tools

- `telescope_calc.c` / `telescope`: C capability calculator (resolution, FOV)
- `ConfigurationPlotter.py`: resolution and FOV sweeps, built on `./telescope`
- `old_scripts/`: earlier single-panel scripts, replaced by `poster_figure.py`
