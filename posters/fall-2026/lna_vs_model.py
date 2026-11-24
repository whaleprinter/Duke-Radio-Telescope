"""Measured LNA gain (NanoVNA) vs. the hardware model, styled for the poster.

Run from anywhere:  python3 posters/fall-2026/lna_vs_model.py
Writes:             posters/fall-2026/figures/lna_vs_model.pdf  (transparent)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import poster_style as ps

POSTER = Path(__file__).resolve().parent
TELESCOPE = POSTER.parents[2]   # fall-2026 -> posters -> Duke-Radio-Telescope -> Telescope
MEASURED = TELESCOPE / "NanoVNA/Parts_Verification/LNA_30_20_11-14-2026-15h14/S21_LNA_30_20_11-14-2026-15h14.csv"
MODEL = TELESCOPE / "Coordinates Plotter/hardware_model/output/bench/lna/expected_s21.csv"
F0 = 1420.405751768  # MHz

meas = pd.read_csv(MEASURED)
meas["f_mhz"] = meas["freq_hz"] / 1e6
model = pd.read_csv(MODEL)

# Flag single-point glitches: points more than 0.3 dB from a 9-point running median.
med = meas["gain_db"].rolling(9, center=True, min_periods=1).median()
glitch = (meas["gain_db"] - med).abs() > 0.3
clean = meas[~glitch]

lo, hi = meas["f_mhz"].min(), meas["f_mhz"].max()
model = model[(model["freq_mhz"] >= lo) & (model["freq_mhz"] <= hi)]

ps.use()
fig, ax = plt.subplots(figsize=ps.figsize(aspect=0.55))

ax.axvspan(1395.4, 1445.4, color=ps.HAIRLINE, alpha=0.45, lw=0, zorder=0)
ax.plot(model["freq_mhz"], model["lna_gain_db"], color=ps.INKSOFT, lw=2.5,
        ls=(0, (6, 4)), label="model (datasheet)")
ax.plot(clean["f_mhz"], clean["gain_db"], color=ps.ROYAL, lw=2.5, label="measured (NanoVNA)")
ax.axvline(F0, color=ps.RUST, lw=1.5)

g_meas = np.interp(F0, clean["f_mhz"], clean["gain_db"])
g_model = np.interp(F0, model["freq_mhz"], model["lna_gain_db"])
ax.annotate(f"1420.4 MHz\nmeasured {g_meas:.2f} dB\nmodel {g_model:.2f} dB",
            xy=(F0, g_meas), xytext=(F0 + 45, g_meas + 0.75),
            color=ps.RUST, ha="left", va="bottom",
            arrowprops=dict(arrowstyle="-", color=ps.RUST, lw=1.2))

ax.set_xlabel("frequency (MHz)")
ax.set_ylabel("LNA gain (dB)")
ax.set_xlim(lo, hi)
ax.legend(loc="lower left")

out = ps.save(fig, POSTER / "figures" / "lna_vs_model")
print(f"wrote {out}  ({int(glitch.sum())} glitch point(s) dropped)")
