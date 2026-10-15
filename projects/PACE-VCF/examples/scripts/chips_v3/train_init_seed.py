"""AJ Kerr's neural training (pace_vcf_toy.train) with a separate model seed.

In his CLI one --seed sets both the chip split and the model's random start
(weight initialisation, data order). For the multi-seed XAI study we want the
SAME split (seed 7: same train/val/test chips as every other run) and a
DIFFERENT random start, so the only thing that changes between runs is the
training path. This wrapper builds his config exactly as his CLI does (split
seed from --seed) and passes --init-seed to his Lightning runner instead.

His code is imported read-only from his repo; nothing of his is changed.

Usage (same arguments as pace_vcf_toy.train, plus --init-seed):
  PYTHONPATH=toy_model/src python train_init_seed.py --init-seed 11 --seed 7 <train args...>
--init-seed equal to --seed reproduces his CLI exactly.
"""
import json
import sys

from pace_vcf_toy import train as T


def main() -> int:
    argv = sys.argv[1:]
    if "--init-seed" not in argv:
        raise SystemExit("--init-seed N is required (use pace_vcf_toy.train directly otherwise)")
    i = argv.index("--init-seed")
    init_seed = int(argv[i + 1])
    del argv[i:i + 2]

    args = T.build_parser().parse_args(argv)
    config = T._experiment_config(args)  # split seed = args.seed
    print(f"split seed {config.data.split.seed} | model init seed {init_seed}")
    T.LightningExperimentRunner(
        config,
        options=T.LightningRunOptions(seed=init_seed, early_stopping_patience=args.early_stopping_patience),
    ).run()
    (config.output_dir / "seeds.json").write_text(
        json.dumps({"split_seed": config.data.split.seed, "init_seed": init_seed}) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
