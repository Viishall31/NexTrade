"""Step 4: the three competing architectures (FR-M1..M3, spec section 6).

All take (batch, window, n_features) and return (batch, n_classes) logits; softmax is
applied by the loss / at inference.
"""
import math

import torch
from torch import nn


def _head(in_dim: int, dense: int, dropout: float, n_classes: int) -> nn.Sequential:
    return nn.Sequential(nn.Linear(in_dim, dense), nn.ReLU(), nn.Dropout(dropout), nn.Linear(dense, n_classes))


class LSTMClassifier(nn.Module):
    def __init__(self, n_features: int, n_classes: int, hidden: int, layers: int, dropout: float,
                 dense: int, head_dropout: float):
        super().__init__()
        self.lstm = nn.LSTM(n_features, hidden, num_layers=layers, batch_first=True,
                            dropout=dropout if layers > 1 else 0.0)
        self.out_dropout = nn.Dropout(dropout)
        self.head = _head(hidden, dense, head_dropout, n_classes)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.head(self.out_dropout(out[:, -1]))


class CausalConv1d(nn.Conv1d):
    """Left-padded convolution: output at step t only sees inputs <= t."""

    def __init__(self, in_ch: int, out_ch: int, kernel: int):
        super().__init__(in_ch, out_ch, kernel)
        self.left_pad = kernel - 1

    def forward(self, x):
        return super().forward(nn.functional.pad(x, (self.left_pad, 0)))


class AdditiveAttention(nn.Module):
    """Bahdanau-style: score_t = v^T tanh(W h_t); context = sum_t softmax(score)_t h_t."""

    def __init__(self, in_dim: int, attn_dim: int):
        super().__init__()
        self.W = nn.Linear(in_dim, attn_dim)
        self.v = nn.Linear(attn_dim, 1, bias=False)

    def forward(self, h):
        weights = torch.softmax(self.v(torch.tanh(self.W(h))).squeeze(-1), dim=1)
        return (weights.unsqueeze(-1) * h).sum(dim=1), weights


class CNNBiLSTMAttention(nn.Module):
    def __init__(self, n_features: int, n_classes: int, conv_filters: list, kernel: int, pool: int,
                 hidden: int, dropout: float, attn_dim: int, dense: int, head_dropout: float):
        super().__init__()
        convs, ch = [], n_features
        for f in conv_filters:
            convs += [CausalConv1d(ch, f, kernel), nn.ReLU()]
            ch = f
        self.conv = nn.Sequential(*convs, nn.MaxPool1d(pool))
        self.bilstm = nn.LSTM(ch, hidden, batch_first=True, bidirectional=True)
        self.dropout = nn.Dropout(dropout)
        self.attention = AdditiveAttention(2 * hidden, attn_dim)
        self.head = _head(2 * hidden, dense, head_dropout, n_classes)

    def forward(self, x):
        z = self.conv(x.transpose(1, 2)).transpose(1, 2)   # (batch, window // pool, filters)
        h, _ = self.bilstm(z)
        context, _ = self.attention(self.dropout(h))
        return self.head(context)


class SinusoidalPositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 512):
        super().__init__()
        pos = torch.arange(max_len).unsqueeze(1)
        div = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer("pe", pe)

    def forward(self, x):
        return x + self.pe[: x.size(1)]


class TransformerClassifier(nn.Module):
    def __init__(self, n_features: int, n_classes: int, d_model: int, layers: int, heads: int,
                 ff_dim: int, dropout: float, dense: int):
        super().__init__()
        self.proj = nn.Linear(n_features, d_model)
        self.pos = SinusoidalPositionalEncoding(d_model)
        layer = nn.TransformerEncoderLayer(d_model, heads, ff_dim, dropout, batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.head = _head(d_model, dense, dropout, n_classes)

    def forward(self, x):
        return self.head(self.encoder(self.pos(self.proj(x))).mean(dim=1))


ARCHITECTURES = {
    "lstm": LSTMClassifier,
    "cnn_bilstm_attn": CNNBiLSTMAttention,
    "transformer": TransformerClassifier,
}


def build_model(name: str, n_features: int, n_classes: int, hp: dict) -> nn.Module:
    return ARCHITECTURES[name](n_features=n_features, n_classes=n_classes, **hp)


def count_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
