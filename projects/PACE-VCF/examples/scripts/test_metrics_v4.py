"""Unit tests for the v4 metric helpers value_at_key_rank() and amplitude_by_key().

Run: python test_metrics_v4.py [path/to/run_metrics_generation_v4.py]
The v3 tests (test_metrics_v3.py) still apply to v4: mean_at_extreme() is unchanged.
"""
import ast
import sys
from pathlib import Path

import numpy as np

path = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).with_name("run_metrics_generation_v4.py"))
src = open(path, encoding="utf-8").read()
ns = {"np": np}
for node in ast.parse(src).body:
    if isinstance(node, ast.FunctionDef) and node.name in ("value_at_key_rank", "amplitude_by_key"):
        exec(compile(ast.Module([node], []), "v4", "exec"), ns)
vak, amp = ns["value_at_key_rank"], ns["amplitude_by_key"]


def cube(vals):
    return np.array(vals, dtype=float).reshape(len(vals), 1, 1)


def check(name, got, want):
    got = float(np.asarray(got).squeeze())
    ok = (np.isnan(want) and np.isnan(got)) or (not np.isnan(want) and abs(got - want) < 1e-9)
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {got}, want {want}")
    return ok


results = []
nan = np.nan

# --- value at the key extremes: the value where the KEY is extreme, not the extreme value
ndvi = cube([.2, .9, .5, .1, .7]); red = cube([.30, .04, .10, .25, .06])
results.append(check("red at greenest composite (NDVI .9)", vak(red, ndvi, "highest"), 0.04))
results.append(check("red at least-green composite (NDVI .1)", vak(red, ndvi, "lowest"), 0.25))

# --- amplitude: greenest minus least green, signed
results.append(check("AmpGreenest red = 0.04 - 0.25 (negative: red drops when green)", amp(red, ndvi), -0.21))
nir = cube([.20, .45, .30, .18, .40])
results.append(check("AmpGreenest NIR = 0.45 - 0.18 (positive)", amp(nir, ndvi), 0.27))
results.append(check("differs from the plain max - min of the band", amp(red, ndvi) == (red.max() - red.min()), 0.0))

# --- median rank: element n_valid // 2 of the ascending key order
results.append(check("5 valid: median-NDVI composite is NDVI .5 -> red .10", vak(red, ndvi, "median"), 0.10))
ndvi4 = cube([.2, .9, .5, .1]); red4 = cube([.30, .04, .10, .25])
results.append(check("4 valid: upper middle (NDVI .5) -> red .10", vak(red4, ndvi4, "median"), 0.10))
x = cube([1., 100., 2., 3., 4.]); k = cube([5., 4., 3., 2., 1.])
results.append(check("not the plain median of the values (plain median = 3)", vak(x, k, "median"), 2.0))

# --- missing key: never selected (the v2 'warmest = no thermal' bug must not come back)
th = cube([300, 310, 320, nan, nan]); b = cube([.1, .2, .3, .9, .9])
results.append(check("warmest ignores composites with no thermal", vak(b, th, "highest"), 0.3))
results.append(check("coolest ignores composites with no thermal", vak(b, th, "lowest"), 0.1))
results.append(check("median of 3 valid keys", vak(b, th, "median"), 0.2))
results.append(check("AmpWarmest = 0.3 - 0.1", amp(b, th), 0.2))

# --- missing value at an extreme: next valid composite is used
results.append(check("NaN value at the greenest composite -> next greenest",
                     vak(cube([.30, nan, .10, .25, .06]), ndvi, "highest"), 0.06))

# --- degenerate cases
results.append(check("no valid key -> NaN", vak(b, cube([nan] * 5), "highest"), nan))
results.append(check("no valid key -> amplitude NaN", amp(b, cube([nan] * 5)), nan))
results.append(check("one valid composite -> amplitude 0", amp(cube([nan, .4, nan]), cube([1., 2., 3.])), 0.0))

# --- an array sorted by itself: amplitude is its plain range (why those bands are dropped)
rng = np.random.default_rng(0)
a = rng.random((12, 40, 40)); a[rng.random(a.shape) < 0.25] = nan
same = np.allclose(amp(a, a), np.nanmax(a, axis=0) - np.nanmin(a, axis=0), equal_nan=True)
print(f"{'PASS' if same else 'FAIL'}  self-keyed amplitude == plain max - min on 1,600 random pixels w/ 25% NaN")
results.append(same)

# --- vectorised result matches a per-pixel loop
key = rng.random((12, 30, 30)); key[rng.random(key.shape) < 0.3] = nan
val = rng.random((12, 30, 30)); val[rng.random(val.shape) < 0.2] = nan
ok = True
for rank in ("lowest", "median", "highest"):
    got = vak(val, key, rank)
    for i in range(30):
        for j in range(30):
            m = np.isfinite(key[:, i, j]) & np.isfinite(val[:, i, j])
            if not m.any():
                want = nan
            else:
                o = np.argsort(key[m, i, j], kind="stable"); v = val[m, i, j][o]
                want = v[{"lowest": 0, "median": len(v) // 2, "highest": len(v) - 1}[rank]]
            g = got[i, j]
            if not ((np.isnan(want) and np.isnan(g)) or (not np.isnan(want) and abs(g - want) < 1e-12)):
                ok = False
print(f"{'PASS' if ok else 'FAIL'}  matches a per-pixel reference on 900 random pixels x 3 ranks (30% key NaN, 20% value NaN)")
results.append(ok)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
