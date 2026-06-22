# AARFLingo Math Notebooks

Jupyter notebooks that implement and verify the IEB triad math used by `services/forecast`.

| Notebook | Purpose |
|----------|---------|
| `01_triad_math_simulation.ipynb` | Derive softmax, CE, coupling loss, flattening — cross-check `core/triad_math.py` |
| `02_training_pipeline.ipynb` | End-to-end synthetic training, loss curves, checkpoint export |

## Setup

```bash
cd /path/to/deepiri-aarflingo
pip install -r notebooks/requirements.txt
cd services/forecast && poetry install
export PYTHONPATH="$(pwd)/../..:$(pwd)"
jupyter notebook ../../notebooks/
```

Unit tests in `core/tests/test_triad_math.py` mirror notebook assertions for CI.

See also [docs/MATH.md](../docs/MATH.md).
