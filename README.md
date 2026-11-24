# Duke Radio Telescope

Simulation code and posters for the Duke Radio Telescope project
(Pierre R. Lamond Department of Electrical and Computer Engineering, Duke University).

| folder | what's in it |
|---|---|
| [`capability_calculator/`](capability_calculator/) | Array simulation: antenna layout, uv coverage, fringes, PSF and a simulated observation. `python3 capability_calculator/poster_figure.py` makes the poster's Figure 1. |
| [`posters/fall-2026/`](posters/fall-2026/) | Fall 2026 research poster (48 × 36 in): LaTeX source, theme, fonts, logos and figures. Build with `latexmk -xelatex poster.tex` inside that folder. |

The galactic sky map and receiver-chain figures are made by the companion repo
[telescope-coordinates-plotter](https://github.com/whaleprinter/telescope-coordinates-plotter)
(`poster_figures.py`), which expects this repo checked out next to it as `Duke-Radio-Telescope/`.
