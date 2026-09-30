"""File names inside an embedding checkpoint directory. Kept apart from
models/export_onnx.py (which needs torch) so inference can import them
without the training stack installed."""

MODEL_FILENAME = "model.onnx"
METADATA_FILENAME = "metadata.json"
