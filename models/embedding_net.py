"""Small per-phase MLP embedding network (task 103), per
docs/embedding_methodology.md's architecture: one EmbeddingNet instance
per phase, since different phases have different feature-vector sizes.
"""

from __future__ import annotations

import torch
import torch.nn.functional as functional
from torch import nn

# A deliberately small embedding space given how little reference data
# this project realistically has -- see docs/embedding_methodology.md.
EMBEDDING_DIM = 8


class EmbeddingNet(nn.Module):
    def __init__(self, input_dim: int, embedding_dim: int = EMBEDDING_DIM):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, embedding_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # L2-normalized so embedding distance is comparable across phases/
        # runs regardless of the raw feature vector's scale.
        return functional.normalize(self.net(x), p=2, dim=-1)
