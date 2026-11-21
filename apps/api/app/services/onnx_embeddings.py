"""Small CPU runtime for the hosted demo. Pooling matches the MiniLM model card."""

from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer


class MiniLM:
    def __init__(self, directory: Path):
        self.tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=256)
        self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(directory / "minilm.onnx"), options, providers=["CPUExecutionProvider"]
        )

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        encodings = self.tokenizer.encode_batch(texts)
        mask = np.asarray([item.attention_mask for item in encodings], dtype=np.int64)
        inputs = {
            "input_ids": np.asarray([item.ids for item in encodings], dtype=np.int64),
            "attention_mask": mask,
            "token_type_ids": np.asarray([item.type_ids for item in encodings], dtype=np.int64),
        }
        tokens = self.session.run(["last_hidden_state"], inputs)[0]
        pooled = np.sum(tokens * mask[..., None], axis=1) / np.maximum(mask.sum(axis=1, keepdims=True), 1)
        return (pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12)).tolist()
