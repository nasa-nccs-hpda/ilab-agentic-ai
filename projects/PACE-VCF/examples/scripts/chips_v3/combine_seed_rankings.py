"""Combine the multi-seed study into stable tree-cover band rankings.

Reads, for each model, the ranking of every seed: the new seeds in
<seeds_dir>/<model>/seed_NNN/ and seed 7 in the reference all-band run
(from run_metadata.txt).
  neural models: XAI_full/feature_importance.csv, scope=overall (the XAI target
                 is tree cover only, so overall = tree cover)
  xgboost      : feature_importance.csv, target 0 (tree cover), rank by gain

Writes <seeds_dir>/combined/ (refuses if it exists unless --force):
  <model>_band_stability.csv   every band: rank in each seed, mean / median /
                               best / worst rank, how many seeds put it in the
                               top 50 and top 100, mean normalised importance;
                               sorted by mean rank (= the consensus ranking)
  <model>_consensus_top{050,100}.txt / .pattern
                               consensus lists (by mean rank) and regexes for
                               --exclude-input-band-pattern, as make_topn_lists.py
  seed_overlap.csv             each pair of seeds: shared bands in the top 50
                               and top 100, Spearman correlation of the ranks
  seed_accuracy.csv            tree-cover R2 / RMSE on val and test for each seed

Usage: combine_seed_rankings.py <seeds_dir> [--force]
"""
import argparse
import itertools
import re
import shutil
from pathlib import Path

import pandas as pd

MODELS = ("spatial-cnn", "pixel-transformer", "xgboost")
TOPS = (50, 100)


def ranking_file(model_dir: Path, model: str) -> Path:
    if model == "xgboost":
        return model_dir / "feature_importance.csv"
    return model_dir / "XAI_full" / "feature_importance.csv"


def read_metadata(seeds_dir: Path) -> dict:
    meta = {}
    for line in (seeds_dir / "run_metadata.txt").read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            meta[k] = v
    return meta


def ranking(path: Path, model: str) -> pd.DataFrame:
    """Columns rank (1 = most important) and normalized_importance, indexed by band name."""
    d = pd.read_csv(path)
    if model == "xgboost":
        d = d[d.target_band_index == 0].rename(columns={"normalized_gain": "normalized_importance"})
    else:
        d = d[d.scope == "overall"]
    return d.set_index("input_band_name")[["rank", "normalized_importance"]]


def tree_cover_scores(model_dir: Path, model: str, ref: Path, seed: int) -> pd.DataFrame:
    """Tree-cover val/test scores as columns split, r2, rmse, checkpoint (empty if none)."""
    if model == "xgboost":
        f = model_dir / "metrics_summary.csv"
        if not f.is_file():
            return pd.DataFrame()
        m = pd.read_csv(f)
        m = m[m.target_band_name == "Percent_Tree_Cover"]
        return pd.DataFrame({"split": m.split, "r2": m.coefficient_of_determination, "rmse": m.rmse,
                             "checkpoint": "-"})
    f = model_dir / "chip_metrics.csv"
    if not f.is_file() and seed == 7:
        f = next(iter(sorted(ref.glob("chip_metrics_neural*.csv"))), f)
    if not f.is_file():
        return pd.DataFrame()
    m = pd.read_csv(f)
    m = m[(m.layer == "Percent_Tree_Cover") & m.model.str.contains(model, regex=False)]
    return m[["split", "r2", "rmse", "checkpoint"]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("seeds_dir", type=Path)
    ap.add_argument("--force", action="store_true", help="replace an existing combined/ folder")
    args = ap.parse_args()
    meta = read_metadata(args.seeds_dir)
    ref = Path(meta["reference_run_seed7"])
    n_bands = int(meta["n_bands"])
    out = args.seeds_dir / "combined"
    if out.exists():
        if not args.force:
            raise SystemExit(f"{out} exists; use --force to rebuild it")
        shutil.rmtree(out)
    out.mkdir()

    overlap_rows, acc_rows = [], []
    for model in MODELS:
        # --- rankings per seed ---
        sources = {}
        if ranking_file(ref / model, model).is_file():
            sources[7] = ref / model
        for d in sorted((args.seeds_dir / model).glob("seed_*")):
            if ranking_file(d, model).is_file():
                sources[int(d.name[5:])] = d
            else:
                print(f"  {model} {d.name}: no ranking (job failed or still running) -- skipped")
        if len(sources) < 2:
            print(f"SKIP {model}: {len(sources)} seed(s) with results")
            continue
        seeds = sorted(sources)
        ranks, imps = {}, {}
        for s in seeds:
            r = ranking(ranking_file(sources[s], model), model)
            if len(r) != n_bands:
                raise SystemExit(f"{model} seed {s}: {len(r)} ranked bands, expected {n_bands}")
            ranks[s], imps[s] = r["rank"], r["normalized_importance"]
        R = pd.DataFrame(ranks)
        R.columns = [f"rank_seed{s}" for s in seeds]
        table = R.copy()
        table["mean_rank"] = R.mean(axis=1)
        table["median_rank"] = R.median(axis=1)
        table["best_rank"] = R.min(axis=1)
        table["worst_rank"] = R.max(axis=1)
        for n in TOPS:
            table[f"n_seeds_top{n}"] = (R <= n).sum(axis=1)
        table["mean_normalized_importance"] = pd.DataFrame(imps).mean(axis=1)
        table = table.sort_values(["mean_rank", "median_rank"])
        table.insert(0, "consensus_rank", range(1, len(table) + 1))
        table.index.name = "input_band_name"
        table.to_csv(out / f"{model}_band_stability.csv")

        names = list(table.index)
        for n in TOPS:
            keep = names[:n]
            pattern = "^(?!(?:" + "|".join(re.escape(k) for k in keep) + ")$)"
            assert {x for x in names if not re.search(pattern, x)} == set(keep)
            (out / f"{model}_consensus_top{n:03d}.txt").write_text("\n".join(keep) + "\n")
            (out / f"{model}_consensus_top{n:03d}.pattern").write_text(pattern)

        # --- agreement between seeds ---
        for a, b in itertools.combinations(seeds, 2):
            row = {"model": model, "seed_a": a, "seed_b": b,
                   "spearman_rank_corr": R[f"rank_seed{a}"].corr(R[f"rank_seed{b}"], method="spearman")}
            for n in TOPS:
                ta = set(R.index[R[f"rank_seed{a}"] <= n]); tb = set(R.index[R[f"rank_seed{b}"] <= n])
                row[f"shared_top{n}"] = len(ta & tb)
            overlap_rows.append(row)

        # --- accuracy per seed ---
        for s in seeds:
            for _, r in tree_cover_scores(sources[s], model, ref, s).iterrows():
                acc_rows.append({"model": model, "seed": s, "split": r.split, "r2": r.r2, "rmse": r.rmse,
                                 "checkpoint": r.checkpoint})

        # --- summary ---
        k = len(seeds)
        ov = pd.DataFrame([r for r in overlap_rows if r["model"] == model])
        print(f"\n{model}: {k} seeds ({', '.join(map(str, seeds))})")
        print(f"  shared top 50 between two seeds: mean {ov.shared_top50.mean():.1f} "
              f"(range {ov.shared_top50.min()}-{ov.shared_top50.max()}); "
              f"Spearman of full rankings: mean {ov.spearman_rank_corr.mean():.2f}")
        for need in range(k, 0, -1):
            print(f"  bands in the top 50 of at least {need}/{k} seeds: {(table.n_seeds_top50 >= need).sum()}")
        print("  consensus top 10: " + ", ".join(names[:10]))

    pd.DataFrame(overlap_rows).to_csv(out / "seed_overlap.csv", index=False)
    acc = pd.DataFrame(acc_rows)
    acc.to_csv(out / "seed_accuracy.csv", index=False)
    if len(acc):
        print("\nTree cover, test chips, across seeds:")
        t = acc[acc.split == "test"].groupby("model").agg(seeds=("seed", "count"), r2_mean=("r2", "mean"),
                                                          r2_sd=("r2", "std"), rmse_mean=("rmse", "mean"),
                                                          rmse_sd=("rmse", "std"))
        print(t.round(4).to_string())
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
