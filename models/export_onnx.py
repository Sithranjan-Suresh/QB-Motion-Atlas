"""Export a trained EmbeddingNet to ONNX for lightweight production
inference (task 108). Bundles the normalization stats (mean/std, task
103's z-score step) alongside the model file, since the ONNX graph alone
has no memory of how its training inputs were scaled -- inference needs
to apply the exact same transform or the embeddings won't mean anything.
"""

from __future__ import annotations

import json
from pathlib import Path

import torch

from models.embedding_net import EmbeddingNet

MODEL_FILENAME = "model.onnx"
METADATA_FILENAME = "metadata.json"


def export_to_onnx(model: EmbeddingNet, input_dim: int, output_path: str | Path) -> None:
    """Exports `model` (already trained) to a standalone ONNX file."""
    model.eval()
    dummy_input = torch.zeros(1, input_dim)
    torch.onnx.export(
        model,
        dummy_input,
        str(output_path),
        input_names=["features"],
        output_names=["embedding"],
        dynamic_axes={"features": {0: "batch"}, "embedding": {0: "batch"}},
    )


def save_checkpoint(
    model: EmbeddingNet,
    feature_keys: list[str],
    mean: torch.Tensor,
    std: torch.Tensor,
    output_dir: str | Path,
) -> Path:
    """Writes `output_dir/model.onnx` + `output_dir/metadata.json` (feature
    key order and normalization stats) -- everything
    `models/embedding_inference.py::EmbeddingInference` needs to load and
    run this model correctly on new feature vectors.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    export_to_onnx(model, len(feature_keys), output_dir / MODEL_FILENAME)

    metadata = {
        "feature_keys": feature_keys,
        "mean": mean.tolist(),
        "std": std.tolist(),
    }
    (output_dir / METADATA_FILENAME).write_text(json.dumps(metadata, indent=2))

    return output_dir
