# Triad Model Math

## Notation

- Intent logits \(z_I\), emotion \(z_E\), behavior \(z_B\)
- Coupling matrix \(C\) from `ethogram/coupling-matrix.json`

## Softmax heads

\[
P(k) = \frac{e^{z_k}}{\sum_j e^{z_j}}
\]

## Coupling prior loss

For batch prediction \((i, e, b)\):

\[
\mathcal{L}_{couple} = -\log \big( C_{i,e,b} + \epsilon \big)
\]

## Total objective

\[
\mathcal{L} = \mathcal{L}_{CE} + \lambda \mathcal{L}_{couple} + \mu \mathcal{L}_{conf}
\]

where \(\mathcal{L}_{conf}\) penalizes over-confidence below human review threshold \(\tau=0.5\).

## Gate decision

\[
\text{gate}(i,e,b,c) =
\begin{cases}
\text{reject} & (i,b) \in \text{forbidden} \\
\text{review} & c < \tau \\
\text{pass} & \text{otherwise}
\end{cases}
\]
