# 5-Phase Pipeline Summary (arXiv:2606.07681v1)

## Quick Reference for Fortran → Differentiable JAX Translation

### Five Phases
1. **Static Dependency Analysis**
   - Build full call graph
   - Determine module translation order (topological sort)
   - Identify shared state & side effects

2. **Iterative Compile-Repair Loops**
   - LLM translates module → JAX
   - Auto-compile → error → repair → repeat
   - Until clean compilation

3. **Fortran Reference Oracle**
   - Module-level numerical parity testing
   - Compare JAX output vs Fortran reference
   - Tolerance: near floating-point precision

4. **Integration & Gradient Verification**
   - Assemble modules into full model
   - Verify end-to-end differentiability
   - Check Jacobian correctness (reverse-mode AD)

5. **Evaluation & Release**
   - Parameter recovery benchmarks
   - Ensemble speedup measurements
   - Release as reusable framework

### Key Results (CLM-ml-v2, 19K lines, 73 modules)
| Metric | Value |
|--------|-------|
| Jacobian computation | Single backward pass |
| Parameter recovery steps | **8× fewer** than gradient-free |
| Wall-clock speedup (N=2048) | **24×** over sequential Fortran |
| Translation tasks analyzed | 73 modules |

### Differentiable Capabilities Enabled
- Gradient-based parameter estimation
- Sensitivity analysis
- Variational data assimilation
- Online training / calibration

### Reusable Artifacts
- Translated CLM-ml-v2 in JAX
- Pipeline infrastructure (dependency analyzer, compile-repair, oracle, verifier)
- Benchmark suite for other ESM components

### Citation
```bibtex
@article{lahlou2026systematic,
  title={Systematic LLM Translation of Legacy Scientific Code to Differentiable Frameworks: Application to a Land Surface Model},
  author={Lahlou, Aya and Hawkins, Linnia and Gentine, Pierre},
  journal={arXiv:2606.07681},
  year={2026}
}
```