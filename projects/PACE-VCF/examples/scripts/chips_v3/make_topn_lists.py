"""Write each model's own top-N band lists (tree cover) for the band-count sweep.

Rankings, all for Percent_Tree_Cover:
  spatial-cnn, pixel-transformer : <run>/<model>/XAI_full/feature_importance.csv
                                   (fuller XAI: 76 val chips, best checkpoint), scope=overall
  xgboost                        : <run>/xgboost/feature_importance.csv, target 0, by gain

For each model and N it writes, under <out>/lists/:
  <model>_ranking.csv        all 521 bands in rank order
  <model>_top<N>.txt         the kept band names
  <model>_top<N>.pattern     regex for AJ Kerr's --exclude-input-band-pattern
                             (matches every band NOT kept)

Two band names occur twice in the 521 (REP/REIP-Brownest3Mean, once in the PACE
file and once in AltSort). Selection is by name, so if one copy is in the top N
the other comes along and the model gets N+1 bands; band counts are printed.

Usage: make_topn_lists.py <training_run_dir> <out_dir> --n 10 25 50 100 200 [--models ...]
Prints the models that have a ranking, one per line prefixed "MODEL ".
"""
import argparse
import re
from pathlib import Path

import pandas as pd


def ranking(run: Path, model: str, n_bands: int) -> pd.DataFrame | None:
    if model == "xgboost":
        path = run / "xgboost" / "feature_importance.csv"
        if not path.is_file():
            return None
        d = pd.read_csv(path)
        d = d[d.target_band_index == 0].sort_values("normalized_gain", ascending=False)
        d = d.rename(columns={"normalized_gain": "importance"})
    else:
        path = run / model / "XAI_full" / "feature_importance.csv"
        if not path.is_file():
            return None
        d = pd.read_csv(path)
        d = d[d.scope == "overall"].sort_values("rank").rename(columns={"normalized_importance": "importance"})
    d = d[["input_band_index", "input_band_name", "importance"]].reset_index(drop=True)
    d.insert(0, "rank", range(1, len(d) + 1))
    if len(d) != n_bands:
        raise ValueError(f"{model}: expected {n_bands} ranked bands, got {len(d)} in {path}")
    return d


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--n", type=int, nargs="+", required=True)
    ap.add_argument("--n-bands", type=int, default=521, help="bands the models were trained on (521 for v3, 475 for v4)")
    ap.add_argument("--models", nargs="+", default=["spatial-cnn", "pixel-transformer", "xgboost"])
    args = ap.parse_args()
    lists = args.out_dir / "lists"
    lists.mkdir(parents=True, exist_ok=False)

    for model in args.models:
        d = ranking(args.run_dir, model, args.n_bands)
        if d is None:
            print(f"SKIP {model}: no ranking found (for neural models run launch_xai_v3.sh first)")
            continue
        d.to_csv(lists / f"{model}_ranking.csv", index=False)
        all_names = list(d.input_band_name)
        for n in args.n:
            keep = list(dict.fromkeys(d.input_band_name[:n]))  # ordered, unique names
            pattern = "^(?!(?:" + "|".join(re.escape(k) for k in keep) + ")$)"
            compiled = re.compile(pattern)
            n_bands = sum(1 for name in all_names if not compiled.search(name))
            assert {name for name in all_names if not compiled.search(name)} == set(keep)
            (lists / f"{model}_top{n:03d}.txt").write_text("\n".join(keep) + "\n")
            (lists / f"{model}_top{n:03d}.pattern").write_text(pattern)
            print(f"  {model} top{n:03d}: {len(keep)} names -> {n_bands} bands")
        print(f"MODEL {model}")


if __name__ == "__main__":
    main()
