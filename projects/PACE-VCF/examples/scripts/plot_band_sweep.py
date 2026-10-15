"""Tree-cover test accuracy vs number of input bands, one line per model.

Reads <models>/<version>_metrics/chip_models/band_count_sweep_tree_cover.csv
(each model retrained on its own top-N tree-cover bands; the largest N = all
bands: 521 for v3, 475 for v4).

  python plot_band_sweep.py                 # v3 -> band_count_sweep_tree_cover.png
  python plot_band_sweep.py --version v4    # v4, with the v3 curves dashed behind
                                            #    -> band_count_sweep_tree_cover_v4.png
  python plot_band_sweep.py --version v4 --title "..."   # set the headline

The v3 figure is never overwritten by a v4 run.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

MODELS_ROOT = Path("/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF/models")
HERE = Path(__file__).resolve().parent
ALL_BANDS = {"v3": 521, "v4": 475}
DEFAULT_TITLE = {
    "v3": "XGBoost levels off by 50 bands; the Spatial-CNN keeps gaining to 200",
    "v4": "Tree-cover accuracy vs number of input bands, v4 metrics (no duplicate bands)",
}

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
COLORS = {"XGBoost": "#2a78d6", "Spatial-CNN": "#eb6834", "Pixel-Transformer": "#1baf7a"}
ORDER = ["XGBoost", "Spatial-CNN", "Pixel-Transformer"]


def load(version: str) -> pd.DataFrame:
    path = MODELS_ROOT / f"{version}_metrics" / "chip_models" / "band_count_sweep_tree_cover.csv"
    if not path.is_file():
        raise SystemExit(f"No sweep results for {version}: {path} does not exist")
    d = pd.read_csv(path)
    return d[d.split == "test"]


ap = argparse.ArgumentParser()
ap.add_argument("--version", choices=sorted(ALL_BANDS), default="v3")
ap.add_argument("--title", default=None, help="headline; default depends on the version")
ap.add_argument("--no-reference", action="store_true", help="v4 only: leave out the dashed v3 curves")
args = ap.parse_args()

version = args.version
n_all = ALL_BANDS[version]
d = load(version)
ref = load("v3") if version == "v4" and not args.no_reference else None
out = HERE / ("band_count_sweep_tree_cover.png" if version == "v3" else f"band_count_sweep_tree_cover_{version}.png")

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=200)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)

if ref is not None:
    for model in ORDER:
        m = ref[ref.model == model].sort_values("top_n")
        ax.plot(m.top_n, m.r2, color=COLORS[model], lw=1.2, ls=(0, (4, 3)), alpha=0.55, zorder=2)
    ax.plot([], [], color=MUTED, lw=1.2, ls=(0, (4, 3)), label="v3 metrics (same model colour)")

label_y = {}
for model in ORDER:
    m = d[d.model == model].sort_values("top_n")
    if m.empty:
        continue
    ax.plot(m.top_n, m.r2, color=COLORS[model], lw=2, marker="o", ms=8,
            mec=SURFACE, mew=2, label=model, zorder=3, clip_on=False)
    label_y[model] = m.r2.iloc[-1]

# direct labels at the all-bands end, nudged apart if they would collide
ys = dict(sorted(label_y.items(), key=lambda kv: kv[1]))
prev = None
for model, y in ys.items():
    yy = y if prev is None else max(y, prev + 0.0055)
    ax.text(600, yy, f"{model}  {label_y[model]:.3f}", color=INK, fontsize=10.5, va="center", ha="left")
    prev = yy

ticks = [10, 25, 50, 100, 200, n_all]
ax.set_xscale("log")
ax.set_xticks(ticks)
ax.set_xticklabels(["10", "25", "50", "100", "200", f"{n_all}\n(all)"])
ax.minorticks_off()
ax.set_xlim(8.5, 600)
lowest = min(d.r2.min(), ref.r2.min()) if ref is not None else d.r2.min()
ax.set_ylim(min(0.88, lowest - 0.005), 0.97)
ax.set_xlabel("Input bands the model was trained on (its own top-ranked bands)", color=INK2)
ax.set_ylabel("Tree-cover R² on the test chips", color=INK2)
ax.tick_params(colors=MUTED, labelcolor=INK2)
ax.grid(axis="y", color=GRID, lw=0.8)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(AXIS)
ax.legend(loc="lower right", frameon=False, fontsize=10, labelcolor=INK2)

fig.suptitle(args.title or DEFAULT_TITLE[version],
             x=0.07, ha="left", fontsize=15, fontweight="bold", color=INK, y=0.975)
subtitle = (f"Each model retrained on its own top-N tree-cover bands, PACE-VCF {version} chips, same 75 test chips "
            "(287,332 pixels).\nOne training run per point.")
if ref is not None:
    subtitle += " Dashed lines: the same sweep on the v3 metrics (521 bands, 100 of them duplicates)."
fig.text(0.07, 0.925, subtitle, ha="left", va="top", color=INK2, fontsize=10, linespacing=1.5)
fig.subplots_adjust(left=0.08, right=0.80, top=0.82, bottom=0.13)
fig.savefig(out, facecolor=SURFACE)
print("saved", out)
