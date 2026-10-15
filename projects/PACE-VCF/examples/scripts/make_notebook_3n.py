"""Build notebooks/3n_metrics_v4_no_duplicates.ipynb from run_metrics_generation_v4.py.

The script is the single source of the metric code; the notebook is generated
from it so the two cannot drift apart. Re-run this after changing the script:

    $PY make_notebook_3n.py            # refuses to overwrite an existing 3n
    $PY make_notebook_3n.py --force    # rebuild (clears the notebook's outputs)
"""
import re
import sys
from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).resolve().parent
SRC = HERE / "run_metrics_generation_v4.py"
DST = HERE / "notebooks" / "3n_metrics_v4_no_duplicates.ipynb"
if DST.exists() and "--force" not in sys.argv:
    raise SystemExit(f"{DST} exists; pass --force to rebuild it")

src = SRC.read_text(encoding="utf-8")
start = src.index("# %% Cell 1: Configuration")
end = src.index("# =============================================================================\n# CLI entry point")
body = src[start:end]
chunks = [c for c in re.split(r"(?m)^(?=# %% Cell )", body) if c.strip()]

intro = """# 3n: Metrics v4 -- no duplicate bands

Same metric families as `3m_metrics_v3_sort_fixes.ipynb`, with the duplicate bands removed. **This notebook is generated from `run_metrics_generation_v4.py`** by `make_notebook_3n.py`; edit the script, then rebuild the notebook, so the two never disagree.

**Why v4.** In v3, 100 of the 521 training bands were exact copies of another band. Most came from metrics that did not compute what their names say.

**What changed (v3 -> v4)**

1. **Amplitude variants use the sort key** -- `AmpGreenestBandRefl-*`, `AmpWarmestBandRefl-*`, `PACEIndex-*-AmpGreenness`, `-AmpAnthocyanin`, `-AmpPigmentRatio`, `-AmpStress`: the value at the highest-key composite minus the value at the lowest-key composite, signed (for NDVI: greenest minus least green). They were all the plain max - min. Helper: `amplitude_by_key()` (Cell 7).
2. **Median variants use the sort key** -- `BandReflMedianGreenness-*`, `BandReflMedianTemp-*`: the value at the median-ranked composite of the key. They were the plain median. Helper: `value_at_key_rank()` (Cell 7).
3. **46 bands are not written** because each is one quantity under a second name (`DROPPED_BANDS_V4`, Cell 13b, with the band that is kept): the plain range under other names (`-SeasonalRange`, `CrossIndex-*-SeasonalRange`), NDVI sorted by NDVI, an index sorted by itself, `PACEIndex-*-Brownest` (= `-AtMinNDVI`), `Greenest3MeanBandRefl-Band31` / `Warmest3MeanBandRefl-Band31` (= `TempMeanGreenest3` / `TempMeanWarmest3`), and a few one-offs.
4. **14 bands are renamed, values unchanged** -- in the PACE file `PACEIndex-<Index>-Greenest3Mean` -> `-Highest3Mean` (it is the mean of the index's own 3 highest values, not NDVI-sorted), and `PACEIndex-REP/REIP-Brownest3Mean` -> `-Lowest3Mean` (so the name is no longer shared with the NDVI-sorted band in the AltSort file).

In both new helpers only composites where **both** the key and the value are valid take part.

**Result:** 650 bands (MODIS 298, PACE 146, AltSort 206), down from 696; 475 after the `^(Unsorted|QA_)` exclusion used for training (v3: 521). No two bands are identical and no name is used twice. Full list: `v4_band_list.json`.

**Intent reference:** Mark Carroll's MODIS VCF code, `nasa-nccs-hpda/modis_vcf`, branch `mcarrol2/v1.2.0`, `model/Metrics.py` (commit `7036b6a`): "Sort band X by NDVI high to low: amp == value 8 - value 1" and "band x reflectance associated with median greenness". Note his running code takes `abs()` of the amplitude and a plain median; v4 follows the descriptions (decided by MJ, 2026-10-12).

**Checked before the full run:** 18/18 unit tests (`test_metrics_v4.py`); v3-vs-v4 on h12v09, h09v05, h31v11 -- exactly 73 bands changed, all intended, 563 identical to v3, renamed bands identical to their v3 originals.

**How to use this notebook**

- **The 291-tile run is a batch job, not this notebook** (about 12 CPU-hours): `bash launch_metrics_v4.sh`, progress with `bash launch_metrics_v4.sh status`. It finished on 2026-10-12 and wrote `.../output/<tile>/2025/3-Metrics-v4/`.
- **Here:** read the definitions, run one tile, and inspect the result. The run cell writes to a scratch folder, so it cannot overwrite the real v4 files."""

setup_cell = '''# %% Setup: where this notebook writes, and PROJ
# Must run BEFORE Cell 1. The metric code reads PACE_METRICS_OUT_BASE once.
import os
from pathlib import Path

# Scratch output, so running a tile here never touches the real 3-Metrics-v4/ files.
NOTEBOOK_OUT_BASE = Path("/explore/nobackup/people/mfrost2/projects/PACE/notebooks/3n_scratch_output")
NOTEBOOK_OUT_BASE.mkdir(parents=True, exist_ok=True)
os.environ["PACE_METRICS_OUT_BASE"] = str(NOTEBOOK_OUT_BASE)

# Writing GeoTIFFs with strict GDAL errors needs PROJ's database. On the batch
# nodes (2026-10-12) PROJ could not open it in place; a private copy works.
def _proj_ok():
    from osgeo import gdal, osr
    gdal.UseExceptions()
    try:
        s = osr.SpatialReference()
        s.ImportFromProj4("+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +R=6371007.181 +units=m +no_defs")
        d = gdal.GetDriverByName("MEM").Create("", 2, 2, 1, gdal.GDT_Int16)
        d.SetProjection(s.ExportToWkt())
        gdal.GetDriverByName("GTiff").CreateCopy("/vsimem/_proj_test.tif", d).FlushCache()
        return True
    except RuntimeError:
        return False

if not _proj_ok():
    import shutil, sys
    src_proj = Path(sys.prefix) / "share" / "proj"
    if not (src_proj / "proj.db").exists():
        src_proj = Path("/panfs/ccds02/app/modules/jupyter/ilab/jupyter-lab/ilab-juplab-ENV-current/share/proj")
    copy = NOTEBOOK_OUT_BASE / "_proj_copy"
    if not (copy / "proj.db").exists():
        shutil.copytree(src_proj, copy, dirs_exist_ok=True)
    os.environ["PROJ_DATA"] = os.environ["PROJ_LIB"] = str(copy)
    # PROJ is already loaded in this kernel, so the environment variable alone
    # is too late: tell the running library where to look.
    from osgeo import osr
    osr.SetPROJSearchPaths([str(copy)])
    print("PROJ: using a private copy at", copy, "| works now:", _proj_ok())
    assert _proj_ok(), "PROJ still cannot open its database; GeoTIFF writing will fail"
else:
    print("PROJ: fine as is")
print("This notebook writes to:", NOTEBOOK_OUT_BASE)
'''

run_cell = '''# %% Cell 15: Run ONE tile into the scratch folder
TEST_TILE = "h12v09"

assert METRICS_OUT_BASE != OUTPUT_BASE, (
    "This notebook is pointed at the real output tree. Run the Setup cell first, then Cell 1 again. "
    "The full run is a batch job: bash launch_metrics_v4.sh")

import time
t0 = time.time()
counts = process_tile_metrics(TEST_TILE)
print(f"\\n{TEST_TILE}: MODIS {counts[0]}, PACE {counts[1]}, AltSort {counts[2]} bands "
      f"= {sum(counts)} in {time.time() - t0:.0f} s -> {METRICS_OUT_BASE / TEST_TILE / str(YEAR) / METRICS_SUBDIR}")
'''

check_cell = '''# %% Cell 16: Checks on that tile
import json, hashlib, collections, re
import rasterio

FILES = ("MODIS_Metrics.tif", "PACE_Metrics.tif", "PACE_AltSort_Metrics.tif")
mine = METRICS_OUT_BASE / TEST_TILE / str(YEAR) / METRICS_SUBDIR
batch = OUTPUT_BASE / TEST_TILE / str(YEAR) / METRICS_SUBDIR        # the real v4 files
v3 = OUTPUT_BASE / TEST_TILE / str(YEAR) / "3-Metrics-v3"

def load(folder):
    out = {}
    for f in FILES:
        with rasterio.open(folder / f) as s:
            out.update({(f, d): a for d, a in zip(s.descriptions, s.read())})
    return out

a = load(mine)

# 1. band list matches v4_band_list.json
want = json.load(open("/explore/nobackup/people/mfrost2/projects/PACE/v4_band_list.json"))
want_set = {(b["file"], b["name"]) for b in want["bands"]}
print(f"1. bands: {len(a)} (expected {want['n_total']}); same list as v4_band_list.json: {set(a) == want_set}")

# 2. no two bands identical, no name used twice
groups = collections.defaultdict(list)
for (f, name), arr in a.items():
    v = arr[arr != NO_DATA_INT]
    if v.size and v.min() != v.max():
        groups[hashlib.md5(arr.tobytes()).hexdigest()].append(name)
dups = [g for g in groups.values() if len(g) > 1]
names = collections.Counter(name for _, name in a)
print(f"2. groups of identical bands: {len(dups)} {dups[:3]} | names used twice: {[n for n, c in names.items() if c > 1]}")

# 3. identical to the batch run's files for this tile
if (batch / FILES[0]).exists():
    b = load(batch)
    print("3. identical to the batch v4 files:", set(a) == set(b) and all(np.array_equal(a[k], b[k]) for k in a))
else:
    print("3. no batch v4 files for this tile to compare with")

# 4. against v3: which bands changed
if (v3 / FILES[0]).exists():
    c = load(v3)
    changed = sorted(k[1] for k in a if k in c and not np.array_equal(a[k], c[k]))
    fam = collections.Counter(re.sub(r"-(Band_?\\d+|NDVI)$", "-*", re.sub(r"PACEIndex-[A-Za-z0-9]+-", "PACEIndex-*-", n)) for n in changed)
    print(f"4. bands that differ from v3: {len(changed)}  (expected 73)")
    for k, n in fam.most_common():
        print(f"     {n:3d}  {k}")
    print(f"   in v3 but not v4: {len(set(c) - set(a))}  |  in v4 but not v3 (renames): {len(set(a) - set(c))}")
'''

look_cell = '''# %% Cell 17: Look at two of the fixed bands
import matplotlib.pyplot as plt

show = [("MODIS_Metrics.tif", "AmpGreenestBandRefl-Band_1", "red: greenest minus least green"),
        ("MODIS_Metrics.tif", "AmpGreenestBandRefl-Band_2", "NIR: greenest minus least green"),
        ("MODIS_Metrics.tif", "BandReflMedianGreenness-Band_1", "red at the median-NDVI composite")]
fig, axes = plt.subplots(1, len(show), figsize=(5.2 * len(show), 4.6), constrained_layout=True)
for ax, (f, name, what) in zip(axes, show):
    arr = a[(f, name)].astype("float32")
    arr[arr == NO_DATA_INT] = np.nan
    arr /= REFL_SCALE
    lim = np.nanpercentile(np.abs(arr), 98)
    signed = name.startswith("Amp")
    im = ax.imshow(arr, cmap="RdBu_r" if signed else "viridis", vmin=-lim if signed else 0, vmax=lim, interpolation="nearest")
    ax.set_title(f"{name}\\n{what}", fontsize=10)
    ax.axis("off")
    fig.colorbar(im, ax=ax, shrink=0.8, label="reflectance")
    print(f"{name}: median {np.nanmedian(arr):+.4f}, share negative {np.nanmean(arr < 0):.2f}")
fig.suptitle(f"{TEST_TILE}: metrics v4", fontsize=13)
plt.show()
'''

outro = """## Running all tiles

The full run is a batch job (independent CPU jobs, resumable; a tile counts as done only when its three files have 298 / 146 / 206 bands):

```bash
cd /explore/nobackup/people/mfrost2/projects/PACE
bash launch_metrics_v4.sh            # 4 jobs, about 3 hours for 291 tiles
bash launch_metrics_v4.sh status     # how many tiles are done, which are missing
```

Do not use job arrays on these nodes (see the README, 2026-10-09).

## What comes after

Chips, training, the band-count sweep, final models, stacks, inference and the map comparison all take a metrics version; see the "v4 plan" section of the project `README.md` for the phases and their checks.

To rebuild this notebook after changing the script: `$PY make_notebook_3n.py --force`."""

nb = nbf.v4.new_notebook()
nb.cells.append(nbf.v4.new_markdown_cell(intro))
nb.cells.append(nbf.v4.new_code_cell(setup_cell))
for c in chunks:
    nb.cells.append(nbf.v4.new_code_cell(c.rstrip() + "\n"))
for cell in (run_cell, check_cell, look_cell):
    nb.cells.append(nbf.v4.new_code_cell(cell))
nb.cells.append(nbf.v4.new_markdown_cell(outro))
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, DST)
print(f"wrote {DST}: {len(nb.cells)} cells ({len(chunks)} from {SRC.name})")
