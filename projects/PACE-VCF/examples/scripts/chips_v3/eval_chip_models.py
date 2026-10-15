"""Per-layer R2 / RMSE on the validation and test chips for the neural chip models.

AJ Kerr's training code only logs pooled RMSE/MAE for the neural models, so this
re-scores saved checkpoints on their own val/test chips. It reuses his loader
(pace_vcf_toy.xai.load_experiment: model + exact split from the run folder) and
his dataset/masking (no-data and water pixels excluded), so the numbers are
computed the same way as the XGBoost metrics_summary.csv. Read-only on the run
folders; writes one CSV.

Usage:
  $P eval_chip_models.py --out results.csv LABEL=EXPERIMENT_DIR [LABEL=EXPERIMENT_DIR ...]
  e.g.  v3/spatial-cnn=/path/to/run/spatial-cnn
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

sys.dont_write_bytecode = True
sys.path.insert(0, "/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/pace_hyperspectral_vcf/toy_model/src")
from pace_vcf_toy.dataset import RasterChipDataset  # noqa: E402
from pace_vcf_toy.transforms import Compose, StandardizeInput  # noqa: E402
from pace_vcf_toy.xai import load_experiment  # noqa: E402

LAYERS = ("Percent_Tree_Cover", "Percent_NonTree_Vegetation", "Percent_NonVegetated")


def score(pred, true):
    err = pred - true
    sse, sst = float(np.sum(err ** 2)), float(np.sum((true - true.mean()) ** 2))
    return {
        "valid_pixels": int(true.size),
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "bias": float(np.mean(err)),
        "r2": 1.0 - sse / sst if sst > 0 else float("nan"),
        "pearson_r": float(np.corrcoef(pred, true)[0, 1]),
    }


@torch.no_grad()
def evaluate(label, experiment_dir, device, batch_size):
    exp = load_experiment(Path(experiment_dir), device=device)
    s = exp.data_settings
    transform = Compose((StandardizeInput.from_npz(s.normalization_stats_path),))
    rows = []
    for split in ("val", "test"):
        dataset = RasterChipDataset(
            exp.records_by_split[split],
            input_nodata_value=s.input_nodata_value, label_nodata_value=s.label_nodata_value,
            water_value=s.water_value, exclude_water_from_loss=s.exclude_water_from_loss,
            transform=transform, exclude_input_band_pattern=s.exclude_input_band_pattern,
        )
        preds, trues = [[] for _ in LAYERS], [[] for _ in LAYERS]
        for batch in DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0):
            prediction = exp.module(batch["image"].to(device)).cpu().numpy()
            target = batch["target"].numpy()
            mask = np.broadcast_to(batch["target_mask"].numpy().astype(bool), target.shape)
            for b in range(len(LAYERS)):
                preds[b].append(prediction[:, b][mask[:, b]])
                trues[b].append(target[:, b][mask[:, b]])
        preds = [np.concatenate(p).astype("float64") for p in preds]
        trues = [np.concatenate(t).astype("float64") for t in trues]
        for b, name in enumerate(LAYERS):
            rows.append({"model": label, "checkpoint": exp.checkpoint_path.name, "split": split,
                         "chips": len(dataset), "layer": name, **score(preds[b], trues[b])})
        rows.append({"model": label, "checkpoint": exp.checkpoint_path.name, "split": split,
                     "chips": len(dataset), "layer": "all_layers_pooled",
                     **score(np.concatenate(preds), np.concatenate(trues))})
        print(f"  {label} {split}: {len(dataset)} chips, pooled RMSE {rows[-1]['rmse']:.3f}", flush=True)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("experiments", nargs="+", help="LABEL=EXPERIMENT_DIR")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--threads", type=int, default=4)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit(f"{args.out} already exists; choose another --out")
    torch.set_num_threads(args.threads)
    print(f"device={args.device}")
    rows = []
    for item in args.experiments:
        label, experiment_dir = item.split("=", 1)
        try:
            rows += evaluate(label, experiment_dir, args.device, args.batch_size)
        except Exception as exc:  # e.g. a training job that failed; score the rest
            print(f"  SKIPPED {label}: {type(exc).__name__}: {exc}", flush=True)
    pd.DataFrame(rows).to_csv(args.out, index=False)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
