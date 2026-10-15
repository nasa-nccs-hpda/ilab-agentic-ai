"""Compare a v3 chip run against AJ Kerr's 2026-09-09 v2 chips (read-only).

For every tile in the new run, checks:
  - the same chip ids were produced (chip placement depends on labels, not metrics)
  - identical band names, in identical order (the 521-band feature contract)
  - identical label chips
  - which input bands changed, and whether they're all on the expected v3 fix list

Usage:
  $PY compare_chips.py <new_run_dir> [--tiles h09v05 h12v09]
"""
import argparse
import re
from collections import Counter
from pathlib import Path

import numpy as np
import rasterio

V2_RUN = Path("/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/chip_outputs/"
              "fixed_metrics/date_2026_09_09-time_13_51_18")

# Bands the v3 fixes are allowed to change (see notebooks/3m_metrics_v3_sort_fixes.ipynb).
EXPECTED_CHANGE = re.compile(
    r"Warmest\d|BandReflM(ax|in)Temp|Greenest\dMeanBandRefl|Brownest3Mean|"
    r"(High|Low)Anthocyanin3Mean|(Least|Most)Stressed3Mean|High(Chlorophyll|Carotenoid)3Mean|"
    r"DuringStress|SnowFree-Lowest3|REP|REIP"
)


def read(path):
    with rasterio.open(path) as s:
        return list(s.descriptions), s.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("new_run_dir", type=Path)
    ap.add_argument("--tiles", nargs="*")
    ap.add_argument("--allow-new-band-list", action="store_true",
                    help="for metrics versions whose band list differs from v2 (v4): check chip ids, "
                         "labels and band counts only")
    args = ap.parse_args()

    new_raw = args.new_run_dir / "raw"
    tiles = args.tiles or sorted(p.name for p in new_raw.iterdir() if (p / "inputs").is_dir())
    if not tiles:
        print(f"No chips found yet in {new_raw} -- is the job still running? (squeue -u $USER)")
        return 1
    changed = Counter()
    band_counts = Counter()
    problems = []

    for tile in tiles:
        new_ids = {p.name for p in (new_raw / tile / "inputs").glob("*.tif")}
        old_ids = {p.name for p in (V2_RUN / "raw" / tile / "inputs").glob("*.tif")}
        print(f"{tile}: {len(new_ids)} chips (v2 had {len(old_ids)})", end="")
        if new_ids != old_ids:
            problems.append(f"{tile}: chip set differs (+{len(new_ids - old_ids)} / -{len(old_ids - new_ids)})")
            print("  <-- chip set differs", end="")
        print()

        for chip in sorted(new_ids & old_ids):
            n_names, n_arr = read(new_raw / tile / "inputs" / chip)
            o_names, o_arr = read(V2_RUN / "raw" / tile / "inputs" / chip)
            band_counts[len(n_names)] += 1
            # v2/v3 chips legitimately repeat two names; from v4 on every name is unique
            if args.allow_new_band_list and len(set(n_names)) != len(n_names):
                problems.append(f"{tile}/{chip}: a band name is used twice")
            if n_names != o_names:
                if not args.allow_new_band_list:
                    problems.append(f"{tile}/{chip}: band names/order differ ({len(n_names)} vs {len(o_names)})")
                    continue
            else:
                for i, name in enumerate(n_names):
                    if not np.array_equal(n_arr[i], o_arr[i], equal_nan=True):
                        changed[name] += 1

            lab_new, lab_old = new_raw / tile / "labels" / chip, V2_RUN / "raw" / tile / "labels" / chip
            if lab_old.exists() and not np.array_equal(read(lab_new)[1], read(lab_old)[1], equal_nan=True):
                problems.append(f"{tile}/{chip}: label chip differs")

    unexpected = sorted(n for n in changed if not EXPECTED_CHANGE.search(n))
    print(f"\nbands per chip: {dict(band_counts)}")
    if args.allow_new_band_list:
        unexpected = []
        print("band list differs from v2 by design: compared chip ids and labels only")
    else:
        print(f"{len(changed)} input bands changed in at least one chip; {len(unexpected)} not on the v3 fix list")
    for n in unexpected[:30]:
        print(f"  UNEXPECTED: {n} ({changed[n]} chips)")
    ok_msg = ("same chips, same labels, one band count, no repeated band names" if args.allow_new_band_list
              else "same chips, same 521-band order, same labels")
    if len(band_counts) > 1:
        problems.append(f"chips have different band counts: {dict(band_counts)}")
    print("\nProblems:" if problems else f"\nNo structural problems: {ok_msg}.")
    for p in problems:
        print("  " + p)
    return 1 if problems or unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
