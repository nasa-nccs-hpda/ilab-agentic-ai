"""Map tile names <-> array indices using AJ Kerr's own inventory logic.

His CLI picks its tile by --job-index into a sorted list of every tile that
has a folder under output/ OR a training-label file. That list grew from 69 to
291+ entries once all tiles had metrics, so indices from his 2026-09-09 run no
longer point at the same tiles. This computes the current indices with his
code (ModisTileInventory._discover_tile_ids), so the numbering always matches
what his CLI will do.

Usage:
  $PY tile_indices.py lookup h09v05 h12v09      # prints "<index> <tile>" per tile
  $PY tile_indices.py ajkerr-tiles              # his 09-09 tiles that made chips
  $PY tile_indices.py check <index> <tile>      # exit 1 unless index -> tile
"""
import json
import sys
from pathlib import Path

AJKERR_TILING_SRC = "/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/pace_hyperspectral_vcf/tiling/src"
INPUT_BASE = Path("/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF/output")
AOI_LABEL_BASE = Path("/explore/nobackup/projects/ilab/data/MODIS/MODIS_VCF/Mark_training/"
                      "VCF_training_adjusted/tile_adjustment/v5.0.3/geotiff")
AJKERR_V2_INVENTORY = Path("/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/chip_outputs/fixed_metrics/"
                           "date_2026_09_09-time_13_51_18/raw/manifests/tile_inventory.jsonl")


def current_tile_order() -> list[str]:
    sys.path.insert(0, AJKERR_TILING_SRC)
    from pace_hyperspectral.inventory import ModisTileInventory
    inv = ModisTileInventory(input_base_dir=INPUT_BASE, aoi_label_base_dir=AOI_LABEL_BASE)
    return list(inv._discover_tile_ids())


def ajkerr_v2_tiles() -> list[str]:
    """Tiles that were 'available' in his 09-09 run (63 of 69; the other 6 made no chips)."""
    rows = [json.loads(line) for line in AJKERR_V2_INVENTORY.read_text().splitlines() if line.strip()]
    return [r["tile_id"] for r in rows if r["discovery_status"] == "available"]


def main() -> int:
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "ajkerr-tiles":
        print("\n".join(ajkerr_v2_tiles()))
        return 0
    order = current_tile_order()
    if cmd == "lookup":
        missing = [t for t in args if t not in order]
        if missing:
            print(f"not in current inventory: {missing}", file=sys.stderr)
            return 1
        for t in args:
            print(order.index(t), t)
        return 0
    if cmd == "check":
        index, tile = int(args[0]), args[1]
        actual = order[index] if index < len(order) else None
        if actual != tile:
            print(f"index {index} is now {actual}, expected {tile}", file=sys.stderr)
            return 1
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
