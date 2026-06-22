# IEB Triad Mathematics (AARFLingo)

Reference for `core/triad_math.py` and `services/forecast` training.

## Feature sequence

Per-frame perception vector \(x_t \in \mathbb{R}^D\) with \(D=20\) (see `core/feature_spec.py`).

Stack \(T=15\) frames, left-pad with zeros if shorter:

\[
\tilde{X} \in \mathbb{R}^{T \times D}, \quad x = \mathrm{vec}(\tilde{X}) \in \mathbb{R}^{TD}
\]

## TriadNet forward

Shared MLP backbone \(f_\theta\), three linear heads:

\[
h = f_\theta(x), \quad z_I = W_I h, \quad z_E = W_E h, \quad z_B = W_B h
\]

\[
\pi^I = \mathrm{softmax}(z_I), \quad \pi^E = \mathrm{softmax}(z_E), \quad \pi^B = \mathrm{softmax}(z_B)
\]

## Losses

Cross-entropy per head (true labels \(y_I, y_E, y_B\)):

\[
\mathcal{L}_{CE} = -\log \pi^I_{y_I} - \log \pi^E_{y_E} - \log \pi^B_{y_B}
\]

Ethogram coupling weight \(w = w(y_I, y_E, y_B)\) from `ethogram/coupling-matrix.json`:

\[
\mathcal{L}_c = \begin{cases}
-\log(w + \varepsilon) & w > 0 \\
L_{\mathrm{forbidden}} & w \le 0
\end{cases}
\]

Total training loss (default \(\lambda = 0.3\)):

\[
\mathcal{L} = \mathcal{L}_{CE} + \lambda \mathcal{L}_c
\]

## Inference confidence

\[
\mathrm{conf} = \frac{\pi^I_{\hat{y}_I} + \pi^E_{\hat{y}_E} + \pi^B_{\hat{y}_B}}{3}
\]

where \(\hat{y}\) are argmax indices.

## Gate (runtime)

`gate_decision` in `services/runtime/app/engine.py` applies `forbidden_pairs` and coupling triples with confidence threshold 0.55.

## Training pipeline

```bash
./scripts/train_aarflingo.sh
# or
poetry run aarflingo-forecast train --epochs 30
```

Outputs:

- `artifacts/models/default/triad.pt` — best validation checkpoint
- `artifacts/models/default/train_metrics.json` — per-epoch train/val loss and accuracy

Verify math interactively: `notebooks/01_triad_math_simulation.ipynb`.
