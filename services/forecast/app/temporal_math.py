"""Model-level math (docs/ADVANCED_MATH.md §9): BiLSTM+attention backbone,
window statistics, MoCo contrastive pretraining, continuous regression heads.

Deliberately additive, not a replacement of `triad_model.TriadNet`: the
shipped `vitals.pt`/TriadNet checkpoints have their architecture (and
input/output dimensions) baked in by `torch.save`/`load_state_dict`, so
swapping the backbone in place would silently break every existing
checkpoint. `TriadNetTemporal` here is a new, separately-trainable model;
promoting it to the default is a deployment decision, not a math one.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def window_statistics(x: np.ndarray) -> dict[str, float]:
    """Per-window mean/var/skew/kurt/ZCR/energy (PRL 2025 fusion pipeline, F1=0.96).

    `x` is a 1D array of one modality's samples over the window. Skew/kurt
    are 0.0 when the window has (near-)zero variance, since standardizing
    by sigma=0 is undefined rather than "no skew."
    """
    x = np.asarray(x, dtype=np.float64)
    t = x.size
    if t == 0:
        return {"mean": 0.0, "var": 0.0, "skew": 0.0, "kurt": 0.0, "zcr": 0.0, "energy": 0.0}
    mean = float(np.mean(x))
    var = float(np.mean((x - mean) ** 2))
    sigma = np.sqrt(var)
    if sigma > 1e-9:
        skew = float(np.mean(((x - mean) / sigma) ** 3))
        kurt = float(np.mean(((x - mean) / sigma) ** 4) - 3.0)
    else:
        skew = 0.0
        kurt = 0.0
    zcr = float(np.mean(np.abs(np.diff(np.sign(x))))) / 2.0 if t > 1 else 0.0
    energy = float(np.sum(x**2))
    return {"mean": mean, "var": var, "skew": skew, "kurt": kurt, "zcr": zcr, "energy": energy}


class BahdanauAttention(nn.Module):
    """Additive attention over encoder states: e_ij = tanh(W_f h_i + b_j),
    a_ij = softmax(e_ij), context = sum(a_ij * h_i)."""

    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.proj = nn.Linear(hidden_dim, hidden_dim)
        self.score = nn.Linear(hidden_dim, 1, bias=False)

    def forward(self, encoder_states: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """encoder_states: (batch, seq_len, hidden_dim) -> (context, attn_weights)."""
        energy = self.score(torch.tanh(self.proj(encoder_states))).squeeze(-1)  # (batch, seq_len)
        weights = F.softmax(energy, dim=-1)
        context = torch.einsum("bt,bth->bh", weights, encoder_states)
        return context, weights


class BiLSTMAttentionEncoder(nn.Module):
    """Bidirectional LSTM + Bahdanau attention temporal backbone."""

    def __init__(self, input_dim: int, hidden: int = 64) -> None:
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden, batch_first=True, bidirectional=True)
        self.attention = BahdanauAttention(hidden * 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (batch, seq_len, input_dim) -> (batch, hidden*2) context vector."""
        encoder_states, _ = self.lstm(x)
        context, _ = self.attention(encoder_states)
        return context


class TriadNetTemporal(nn.Module):
    """BiLSTM+attention TriadNet variant with arousal/valence regression heads.

    Consumes the *unflattened* sequence (batch, SEQUENCE_LEN, FEATURE_DIM)
    rather than TriadNet's flattened (batch, SEQUENCE_LEN*FEATURE_DIM) MLP
    input, since a recurrent backbone needs the temporal axis intact.
    """

    def __init__(
        self,
        feature_dim: int,
        intent_labels: list[str],
        emotion_labels: list[str],
        behavior_labels: list[str],
        hidden: int = 64,
    ) -> None:
        super().__init__()
        self.encoder = BiLSTMAttentionEncoder(feature_dim, hidden)
        context_dim = hidden * 2
        self.intent_head = nn.Linear(context_dim, len(intent_labels))
        self.emotion_head = nn.Linear(context_dim, len(emotion_labels))
        self.behavior_head = nn.Linear(context_dim, len(behavior_labels))
        # Continuous arousal in [0,1], valence in [-1,1] (doc §4/§9): sigmoid
        # and tanh output activations respectively, applied at call time.
        self.arousal_head = nn.Linear(context_dim, 1)
        self.valence_head = nn.Linear(context_dim, 1)
        self.intent_labels = intent_labels
        self.emotion_labels = emotion_labels
        self.behavior_labels = behavior_labels

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        context = self.encoder(x)
        arousal = torch.sigmoid(self.arousal_head(context)).squeeze(-1)
        valence = torch.tanh(self.valence_head(context)).squeeze(-1)
        return (
            self.intent_head(context),
            self.emotion_head(context),
            self.behavior_head(context),
            arousal,
            valence,
        )


def regression_loss(arousal_pred: torch.Tensor, valence_pred: torch.Tensor, arousal_true: torch.Tensor, valence_true: torch.Tensor) -> torch.Tensor:
    """MSE loss for the continuous arousal/valence heads, combinable with the
    existing classification-head cross-entropy via simple addition."""
    return F.mse_loss(arousal_pred, arousal_true) + F.mse_loss(valence_pred, valence_true)


def info_nce_loss(query: torch.Tensor, positive_key: torch.Tensor, negative_keys: torch.Tensor, temperature: float = 0.07) -> torch.Tensor:
    """MoCo InfoNCE contrastive loss (2024 MDPI unsupervised pretraining, 43.2% vs 14% baseline).

    query: (batch, dim); positive_key: (batch, dim); negative_keys: (K, dim).
    All should already be L2-normalized (standard MoCo practice) — this
    function doesn't normalize for you, since re-normalizing silently would
    hide a caller bug where the encoder forgot to.
    """
    pos_logit = torch.sum(query * positive_key, dim=-1, keepdim=True) / temperature  # (batch, 1)
    neg_logits = (query @ negative_keys.T) / temperature  # (batch, K)
    logits = torch.cat([pos_logit, neg_logits], dim=1)  # (batch, 1+K)
    labels = torch.zeros(query.size(0), dtype=torch.long, device=query.device)  # positive is index 0
    return F.cross_entropy(logits, labels)


@torch.no_grad()
def momentum_update(key_encoder: nn.Module, query_encoder: nn.Module, m: float = 0.999) -> None:
    """theta_k <- m*theta_k + (1-m)*theta_q — MoCo's momentum key-encoder update."""
    for pk, pq in zip(key_encoder.parameters(), query_encoder.parameters()):
        pk.data.mul_(m).add_(pq.data, alpha=1.0 - m)
