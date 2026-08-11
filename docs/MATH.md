# IEB Triad Mathematics (AARFLingo)

Reference for `core/triad_math.py` and `services/forecast` training.

## Feature sequence

Per-frame perception vector \(x_t \in \mathbb{R}^D\) with \(D=43\)
(35 base features + 8 modality features, see `core/feature_spec.py`).

Stack \(T=15\) frames, left-pad with zeros if shorter:

\[
\tilde{X} \in \mathbb{R}^{T \times D}, \quad x = \mathrm{vec}(\tilde{X}) \in \mathbb{R}^{TD}
\]

## Approach geometry (τ, closing, heading)

Intent is a *destination*: approaching the door means "outside", the toy
means "play". Per frame, for each zone \(z\) with center \(c_z\) and the
dog at \(p\) with velocity \(v\):

\[
d_z = \|c_z - p\|, \qquad \hat u_z = \frac{c_z - p}{d_z}, \qquad \dot d_z = v \cdot \hat u_z
\]

- Closing rate: \(\mathrm{closing}_z = \mathrm{clamp}(\dot d_z / v_{\max}, 0, 1)\)
- Lee's time-to-contact: \(\tau_z = d_z / \max(\dot d_z, \varepsilon)\),
  normalized against a contact horizon \(H=60\) frames
  \(\mathrm{tau}_z = \mathrm{clamp}(1 - \tau_z / H, 0, 1)\) — high means imminent arrival.
- Heading cosine: \(\mathrm{heading}_z = \cos\angle(v, \hat u_z) = \hat v \cdot \hat u_z\).

All three depend only on the *relative* geometry dog↔zone, so they are
invariant under camera translation; absolute coordinates (`bbox_cx`,
`edge_*`) are not. The model should learn to weight the invariant set.

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

Max-probability overstates certainty when two hypotheses are nearly tied.
The honest confidence is the **margin** — the top-1 minus top-2 gap, meaned
across heads:

\[
m(\pi) = \pi_{(1)} - \pi_{(2)}, \qquad
\mathrm{margin} = \frac{m(\pi^I) + m(\pi^E) + m(\pi^B)}{3}
\]

A dog equidistant between door and toy has a small intent margin; the gate
should treat small margins as "review" even when \(\mathrm{conf}\) is high.

## Gate (runtime)

`gate_decision` in `services/runtime/app/engine.py` applies `forbidden_pairs` and coupling triples with confidence threshold 0.55; per-frame `margin` is exposed alongside `confidence` for ambiguity-aware review.

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
