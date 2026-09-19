#!/usr/bin/env python3
"""
Reproduce Figure 6 of Tsigaridis et al. 2025 (GMD, ROCKE-3D 2.0):
  "Box-and-whisker plot of net planetary radiation (net_rad_planet) in W/m^2
   for all ocean configurations following balancing. The last 100 years of
   simulations were used for analysis."

Data source (NASA GISS publication supplement):
  https://portal.nccs.nasa.gov/GISS_modelE/ROCKE-3D/publication-supplements/Tsigaridis2025GMD-planet_2.0/

Config -> directory mapping is copied verbatim from that directory's README.txt.
Two entries in NASA's own README have a paper-name typo (P2Gxq* should read
P2Sxq*, since the target directory is P2Sxq*); corrected here, directory
names (which is what actually matters for fetching data) are untouched.
"""
import argparse
import concurrent.futures
import re
import sys
from pathlib import Path
from urllib.request import urlopen, Request

import netCDF4 as nc

BASE_URL = "https://portal.nccs.nasa.gov/GISS_modelE/ROCKE-3D/publication-supplements/Tsigaridis2025GMD-planet_2.0"

# paper_name -> directory_name, planet_2.0 simulations, from README.txt
CONFIGS = {
    "P2GApF40": "P2GAF40_002",   "P2GApM40": "P2GAM40_008",
    "P2GAqF40": "P2GAqF40_002",  "P2GAqM40": "P2GAqM40_002",
    "P2GAoF40": "P2GAoF40_005",  "P2GAoM40": "P2GAoM40_009",

    "P2GxpF40": "P2GxF40_005",   "P2GxpM40": "P2GxM40_008",
    "P2GxqF40": "P2GxqF40_001",  "P2GxqM40": "P2GxqM40_001",
    "P2GxoF40": "P2GxoF40_001",  "P2GxoM40": "P2GxoM40_001",

    "P2GNpF40": "P2GNF40_005",   "P2GNpM40": "P2GNM40_003",
    "P2GNqF40": "P2GNqF40_002",  "P2GNqM40": "P2GNqM40_002",
    "P2GNoF40": "P2GNoF40_002",  "P2GNoM40": "P2GNoM40_002",

    "P2SApF40": "P2SAF40_017",   "P2SApM40": "P2SAM40_019",
    "P2SAqF40": "P2SAqF40_004",  "P2SAqM40": "P2SAqM40_005",
    "P2SAoF40": "P2SAoF40_004",  "P2SAoM40": "P2SAoM40_003",

    "P2SxpF40": "P2SxF40_007",   "P2SxpM40": "P2SxM40_014",
    "P2SxqF40": "P2SxqF40_002",  "P2SxqM40": "P2SxqM40_002",  # corrected paper name
    "P2SxoF40": "P2SxoF40_002",  "P2SxoM40": "P2SxoM40_002",  # corrected paper name

    "P2SNpF40": "P2SNF40_006",   "P2SNpM40": "P2SNM40_011",
    "P2SNqF40": "P2SNqF40_004",  "P2SNqM40": "P2SNqM40_004",
    "P2SNoF40": "P2SNoF40_004",  "P2SNoM40": "P2SNoM40_004",
}

FNAME_RE_TMPL = r'href="(ANN(\d+)\.aij{cfg}\.nc)"'  # excludes aijl (no trailing "l" in group)


def list_remote_years(directory: str, cfg: str) -> list[tuple[int, str]]:
    url = f"{BASE_URL}/{directory}/"
    with urlopen(Request(url, headers={"User-Agent": "curl/8"})) as resp:
        html = resp.read().decode("utf-8", "ignore")
    pat = re.compile(FNAME_RE_TMPL.format(cfg=re.escape(cfg)))
    hits = [(int(year), fname) for fname, year in pat.findall(html)]
    hits.sort()
    return hits


def fetch_file(directory: str, fname: str, cache_dir: Path) -> Path:
    dest = cache_dir / directory / fname
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.stat().st_size == 0:
        url = f"{BASE_URL}/{directory}/{fname}"
        with urlopen(Request(url, headers={"User-Agent": "curl/8"})) as resp, open(dest, "wb") as out:
            out.write(resp.read())
    return dest


def global_mean_net_rad_planet(path: Path) -> float:
    ds = nc.Dataset(path)
    try:
        return float(ds.variables["net_rad_planet_hemis"][2])  # [SH, NH, global]
    finally:
        ds.close()


def collect_config(paper_name: str, directory: str, cache_dir: Path, n_years: int, workers: int) -> list[float]:
    # The .nc filename suffix is the paper name (verified against the server
    # for p/q/o ocean types), even though the directory name itself sometimes
    # drops letters (e.g. paper name P2SApM40 lives in directory P2SAM40_019).
    years = list_remote_years(directory, paper_name)
    if not years:
        raise RuntimeError(f"No files found for {paper_name} ({directory})")
    last_n = years[-n_years:]
    print(f"  {paper_name} ({directory}): {len(last_n)} years "
          f"[{last_n[0][0]}-{last_n[-1][0]}]", file=sys.stderr)

    def _one(item):
        _, fname = item
        local = fetch_file(directory, fname, cache_dir)
        return global_mean_net_rad_planet(local)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_one, last_n))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--configs", nargs="*", default=None,
                     help="Subset of paper-name configs to plot (default: all M40 configs). "
                          "Use 'all' for every M40+F40 config (36 total, large download).")
    ap.add_argument("--n-years", type=int, default=100, help="Years per config (default 100, matches the paper)")
    ap.add_argument("--cache-dir", type=Path, default=Path("./rocke3d_cache"))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", type=Path, default=Path("figure6_reproduction.png"))
    args = ap.parse_args()

    if args.configs is None:
        selected = [c for c in CONFIGS if c.endswith("M40")]
    elif args.configs == ["all"]:
        selected = list(CONFIGS)
    else:
        selected = args.configs
        unknown = set(selected) - set(CONFIGS)
        if unknown:
            sys.exit(f"Unknown config name(s): {unknown}\nValid names: {sorted(CONFIGS)}")

    print(f"Fetching {len(selected)} configuration(s), {args.n_years} year(s) each:", file=sys.stderr)
    data = {}
    for paper_name in selected:
        directory = CONFIGS[paper_name]
        try:
            data[paper_name] = collect_config(paper_name, directory, args.cache_dir, args.n_years, args.workers)
        except Exception as e:
            print(f"  WARNING: skipping {paper_name}: {e}", file=sys.stderr)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = list(data.keys())
    series = [data[k] for k in labels]

    fig, ax = plt.subplots(figsize=(max(8, 0.6 * len(labels)), 5))
    ax.boxplot(series, tick_labels=labels, showfliers=True)
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_ylabel("net_rad_planet (W m$^{-2}$)")
    ax.set_title(f"Net planetary radiation, last {args.n_years} years\n"
                 f"(reproduction of Tsigaridis et al. 2025, Fig. 6)")
    plt.xticks(rotation=60, ha="right")
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    print(f"\nSaved plot to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
