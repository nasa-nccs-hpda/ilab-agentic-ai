# LAFT vs 5-Phase Pipeline: Comparison & When to Use

## Quick Decision Guide

| Aspect | LAFT (arXiv:2610.12662) | 5-Phase Pipeline (arXiv:2606.07681) |
|--------|-------------------------|-------------------------------------|
| **Primary Goal** | GPU-accelerated JAX with numerical parity | **Differentiable** JAX (gradients, AD) |
| **Target Domain** | Atmospheric physics parameterizations | Land surface models (CLM) |
| **Scale** | Single scheme (Kessler microphysics) | Full model (19K lines, 73 modules) |
| **Validation** | Numerical + **GPU profiling** | Numerical + **gradient verification** |
| **Key Innovation** | Bridge (array layout ↔ science), profiling feedback | Dependency analysis, compile-repair, oracle |
| **Speedup** | 357× (Gemini, 1M cols) | 24× (ensemble N=2048) |
| **LLMs Tested** | 4 (Claude, GPT, Gemini, Qwen) | Not specified (agentic pipeline) |
| **Output** | JAX kernel + profiling report | Full differentiable model + framework |

## When to Use Which

### Use LAFT when:
- Translating **individual physics parameterizations** (microphysics, radiation, etc.)
- **GPU performance is critical** — need hardware-aware optimization
- Working with **atmospheric models** (CESM, WRF, E3SM)
- Need **reproducible profiling** across LLMs
- Target is **JAX on GPU** (not necessarily differentiable)

### Use 5-Phase Pipeline when:
- Translating **full model components** with complex call graphs
- Need **end-to-end differentiability** (gradients, Jacobians, AD)
- Working with **land surface / coupled models**
- Need **autonomous compile-repair** for large codebases
- Want **reusable framework** for other ESM components
- Parameter estimation / data assimilation / calibration are goals

## Complementary Insights

| Insight | Source |
|---------|--------|
| Numerical parity ≠ GPU efficiency | LAFT |
| Dependency analysis enables correct module ordering | 5-Phase |
| Bridge pattern separates layout from science | LAFT |
| Compile-repair loops handle large-scale translation | 5-Phase |
| Profiling-guided feedback optimizes GPU kernels | LAFT |
| Fortran oracle ensures numerical correctness at module level | 5-Phase |
| Gradient verification enables differentiable science | 5-Phase |

## Combined Workflow Idea

```
Fortran Codebase
       │
       ▼
┌──────────────────┐
│ Dependency Analysis │ ← 5-Phase Phase 1
│ (call graph, order) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│ Module-by-Module │     │ LAFT Bridge      │
│ Translation      │────▶│ (array layout)   │
│ (compile-repair) │     └────────┬─────────┘
└────────┬─────────┘              │
         │                        ▼
         ▼               ┌──────────────────┐
┌──────────────────┐     │ JAX Kernel       │
│ Fortran Oracle   │     │ + Profiling      │ ← LAFT profiling
│ (numerical parity)│     └────────┬─────────┘
└────────┬─────────┘              │
         │                        ▼
         ▼               ┌──────────────────┐
┌──────────────────┐     │ Gradient         │
│ Integration &    │────▶│ Verification     │ ← 5-Phase Phase 4
│ Gradient Check   │     └──────────────────┘
└──────────────────┘
```

## Key Papers to Cite Together

```bibtex
@article{linck2026laft,
  title={Evaluating LLMs for Translating Legacy Fortran Atmospheric Physics to GPU-Accelerated JAX},
  author={Linck, Iris and Dennis, John and Schreck, John and Stengel, Karen and Gagne II, David John},
  journal={arXiv:2610.12662},
  year={2026}
}

@article{lahlou2026systematic,
  title={Systematic LLM Translation of Legacy Scientific Code to Differentiable Frameworks: Application to a Land Surface Model},
  author={Lahlou, Aya and Hawkins, Linnia and Gentine, Pierre},
  journal={arXiv:2606.07681},
  year={2026}
}
```