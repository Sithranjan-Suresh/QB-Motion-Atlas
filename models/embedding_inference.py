"""Lightweight ONNX-based inference for the V2 embedding model (task 109).
Loads a checkpoint saved by models/export_onnx.py::save_checkpoint --
never re-imports torch/the training code, so the live API can embed a
feature vector without pulling in the full training stack.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnxruntime

from models.export_onnx import METADATA_FILENAME, MODEL_FILENAME


class EmbeddingInference:
    def __init__(self, checkpoint_dir: str | Path):
        checkpoint_dir = Path(checkpoint_dir)
        self.session = onnxruntime.InferenceSession(str(checkpoint_dir / MODEL_FILENAME))

        metadata = json.loads((checkpoint_dir / METADATA_FILENAME).read_text())
        self.feature_keys: list[str] = metadata["feature_keys"]
        self.mean = np.array(metadata["mean"], dtype=np.float32)
        self.std = np.array(metadata["std"], dtype=np.float32)

    def embed(self, feature_vector: dict[str, float]) -> list[float]:
        """Normalizes `feature_vector` (using the training-time mean/std,
        same feature key order the model was trained on) and runs it
        through the ONNX model, returning the embedding as a plain list.
        """
        missing = set(self.feature_keys) - feature_vector.keys()
        if missing:
            raise ValueError(f"feature_vector is missing keys this model was trained on: {missing}")

        raw = np.array([[feature_vector[k] for k in self.feature_keys]], dtype=np.float32)
        normalized = (raw - self.mean) / self.std

        (embedding,) = self.session.run(None, {"features": normalized})
        return embedding[0].tolist()
