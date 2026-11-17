"""poster_style.py -- make matplotlib figures match the Fall 2026 poster.

Put this file in the poster folder (next to fonts/). In any plotting script:

    import sys; sys.path.insert(0, "/Users/roshan/Documents/School/Telescope/Capability Calculator/Fall 2026 Poster")
    import poster_style
    poster_style.use()                                  # after any other style/theme setup
    fig, ax = plt.subplots(figsize=poster_style.figsize(aspect=0.55))
    ...
    poster_style.save(fig, "Fall 2026 Poster/figures/noise_budget")   # -> .pdf, transparent

What it does
  1. Transparent background: figure, axes and saved file have no fill, so the
     plot sits directly on the poster's glass cards.
  2. Poster typography: EB Garamond text, Instrument Serif titles, and font
     sizes in real points. The figure is drawn at the poster's actual block
     width, so when LaTeX includes it at \\linewidth it is scaled 1:1 and
     24 pt here is 24 pt on the printed poster.
  3. Poster colours: Duke Royal / rust / Duke Navy / warm ink, matching the
     beamer theme (beamerthemedukeglass.sty).
  4. Vector PDF output with the fonts embedded (crisp at any print size).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
from cycler import cycler
from matplotlib import font_manager

# ---- fonts (the same files the poster uses) ------------------------------
FONT_DIR = Path(__file__).resolve().parent / "fonts"
for _f in FONT_DIR.glob("*.ttf"):
    font_manager.fontManager.addfont(str(_f))
TEXT_FONT = "EB Garamond"
TITLE_FONT = "Instrument Serif"

# ---- colours (from beamerthemedukeglass.sty) -----------------------------
NAVY = "#012169"      # Duke Navy
ROYAL = "#00539B"     # Duke Royal Blue
RUST = "#A12D10"      # accent: use for the one thing to notice
INK = "#3F3429"       # body text
INKSOFT = "#6B5D50"   # ticks, captions, secondary lines
HAIRLINE = "#D8CFC2"  # grid
SERIES = [ROYAL, RUST, NAVY, INKSOFT]   # line / bar colour order

# ---- geometry ------------------------------------------------------------
# One poster column = (121.92 cm - 2*2.8 cm edges - 2*2.6 cm gaps) / 3 = 37.04 cm,
# minus 2*2.2 cm card padding = 32.6 cm of usable width inside a block.
BLOCK_WIDTH_IN = 32.6 / 2.54   # 12.85 in


def figsize(width_frac: float = 1.0, aspect: float = 0.6) -> tuple[float, float]:
    """(width, height) in inches for a figure that fills `width_frac` of a block.

    aspect = height / width. Draw at this size and include with
    \\includegraphics[width=width_frac\\linewidth] so nothing gets rescaled.
    """
    w = BLOCK_WIDTH_IN * width_frac
    return (w, w * aspect)


def use(base_pt: float = 26) -> None:
    """Apply the poster style globally. base_pt = axis-label size in points.

    Poster guide minimums: body 24 pt, captions 18 pt. Tick labels come out at
    0.9 * base_pt, so base_pt = 26 keeps everything at or above ~24 pt.
    """
    mpl.rcParams.update({
        # transparent everywhere
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "savefig.facecolor": "none",
        "savefig.edgecolor": "none",
        "savefig.transparent": True,
        # vector output, fonts embedded as TrueType
        "savefig.format": "pdf",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "pdf.fonttype": 42,
        # typography
        "font.family": TEXT_FONT,
        "font.size": base_pt,
        "axes.titlesize": base_pt * 1.3,
        "axes.labelsize": base_pt,
        "xtick.labelsize": base_pt * 0.9,
        "ytick.labelsize": base_pt * 0.9,
        "legend.fontsize": base_pt * 0.9,
        "mathtext.fontset": "custom",
        "mathtext.rm": TEXT_FONT,
        "mathtext.it": f"{TEXT_FONT}:italic",
        "mathtext.bf": TEXT_FONT,
        # colours
        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.titlecolor": NAVY,
        "axes.edgecolor": INKSOFT,
        "xtick.color": INKSOFT,
        "ytick.color": INKSOFT,
        "axes.prop_cycle": cycler(color=SERIES),
        # quiet frame and grid
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 1.0,
        "axes.grid": True,
        "grid.color": HAIRLINE,
        "grid.linewidth": 0.8,
        "lines.linewidth": 2.5,
        "xtick.major.width": 1.0,
        "ytick.major.width": 1.0,
        "xtick.major.size": 6,
        "ytick.major.size": 6,
        "legend.frameon": False,
    })


def title(ax, text: str, **kw) -> None:
    """Axes title in the poster's display face (Instrument Serif)."""
    ax.set_title(text, fontfamily=TITLE_FONT, loc=kw.pop("loc", "left"), **kw)


def save(fig, path, **kw) -> Path:
    """Save as a transparent PDF (extension added if missing)."""
    path = Path(path)
    if path.suffix == "":
        path = path.with_suffix(".pdf")
    path.parent.mkdir(parents=True, exist_ok=True)
    # facecolor="none" overrides scripts that pass an explicit background
    fig.savefig(path, transparent=True, facecolor="none", edgecolor="none", **kw)
    return path
