# LAFT Framework Summary (arXiv:2610.12662v1)

## Quick Reference for Fortran → JAX Translation

### Core Architecture
- **Agentic workflow**: Source analysis → Translation → Repair → Validation → Profiling
- **Deterministic front-end**: Metadata extraction + bridge generation (array layout ↔ science separation)
- **Structured prompts**: Domain-specific translation templates
- **Numerical oracle**: Fortran reference comparison (near FP precision)
- **Profiling feedback**: GPU execution pattern analysis

### Key Metrics (Kessler Microphysics)
| LLM | Numerical Parity | GPU Speedup (1M cols) |
|-----|------------------|----------------------|
| Gemini | ✅ | **357×** |
| Claude | ✅ | Lower |
| GPT | ✅ | Lower |
| Qwen | ✅ | Lower |

### Critical Insight
> **Numerical agreement alone does not ensure efficient GPU execution** — must combine validation with hardware-aware profiling

### Reusable Components
- Bridge generator (array layout conversion)
- Validation harness (numerical + performance)
- Profiling-guided optimization loop
- Reproducible benchmarking suite

### Citation
```bibtex
@article{linck2026laft,
  title={Evaluating LLMs for Translating Legacy Fortran Atmospheric Physics to GPU-Accelerated JAX},
  author={Linck, Iris and Dennis, John and Schreck, John and Stengel, Karen and Gagne II, David John},
  journal={arXiv:2610.12662},
  year={2026}
}
```