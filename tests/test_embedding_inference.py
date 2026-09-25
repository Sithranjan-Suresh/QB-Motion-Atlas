"""Round-trip test for models/export_onnx.py + models/embedding_inference.py
(tasks 108-109): train a tiny model on synthetic triplets, export it,
load it back via ONNX runtime, and confirm inference matches the
in-memory PyTorch model -- no real reference dataset exists yet.
"""

import random

import torch

from models.embedding_inference import EmbeddingInference
from models.export_onnx import save_checkpoint
from models.train_embedding import _vectors_to_tensor, train_embedding_net
from pipeline.embedding.sampling import PhaseRecord, generate_triplets

FEATURE_KEYS = ["elbow_angle_deg", "release_arm_velocity"]


def _make_records() -> list[PhaseRecord]:
    rng = random.Random(0)
    records = []
    for qb_name, (angle, velocity) in {"qb_a": (90.0, 1.0), "qb_b": (100.0, 1.3)}.items():
        for i in range(6):
            vector = {
                "elbow_angle_deg": angle + rng.uniform(-4, 4),
                "release_arm_velocity": velocity + rng.uniform(-0.15, 0.15),
            }
            records.append(PhaseRecord(qb_name, f"{qb_name}_clip{i}", "release", vector))
    return records


def test_onnx_roundtrip_matches_pytorch_model(tmp_path):
    torch.manual_seed(0)
    records = _make_records()
    triplets = generate_triplets(records, rng=random.Random(1))
    result = train_embedding_net(triplets, FEATURE_KEYS, epochs=50)

    checkpoint_dir = tmp_path / "checkpoint"
    save_checkpoint(result.model, FEATURE_KEYS, result.mean, result.std, checkpoint_dir)

    inference = EmbeddingInference(checkpoint_dir)

    test_vector = {"elbow_angle_deg": 95.0, "release_arm_velocity": 1.1}
    onnx_embedding = inference.embed(test_vector)

    with torch.no_grad():
        torch_embedding = result.model(_vectors_to_tensor([test_vector], FEATURE_KEYS, result.mean, result.std))[0]

    assert len(onnx_embedding) == len(torch_embedding)
    for onnx_val, torch_val in zip(onnx_embedding, torch_embedding.tolist()):
        assert abs(onnx_val - torch_val) < 1e-4


def test_embed_raises_on_missing_feature(tmp_path):
    torch.manual_seed(0)
    records = _make_records()
    triplets = generate_triplets(records, rng=random.Random(1))
    result = train_embedding_net(triplets, FEATURE_KEYS, epochs=5)

    checkpoint_dir = tmp_path / "checkpoint"
    save_checkpoint(result.model, FEATURE_KEYS, result.mean, result.std, checkpoint_dir)
    inference = EmbeddingInference(checkpoint_dir)

    import pytest

    with pytest.raises(ValueError):
        inference.embed({"elbow_angle_deg": 90.0})  # missing release_arm_velocity
