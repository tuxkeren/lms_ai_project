import os
from django.conf import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, 'model_onnx')
MODEL_FILE = os.path.join(MODEL_PATH, 'model.onnx')
TOKENIZER = None
SESSION = None
SESSION_INPUTS = None


class ModelTidakTersedia(Exception):
    pass


def _muat_engine():
    global TOKENIZER, SESSION, SESSION_INPUTS
    if TOKENIZER is not None and SESSION is not None:
        return

    if not os.path.isdir(MODEL_PATH) or not os.path.isfile(MODEL_FILE):
        raise ModelTidakTersedia(
            f"Model ONNX tidak ditemukan di '{MODEL_PATH}'. "
            "Letakkan file model.onnx beserta folder tokenizer di direktori model_onnx."
        )

    try:
        import onnxruntime as ort
        from transformers import AutoTokenizer
    except ImportError as e:
        raise ModelTidakTersedia(
            f"Dependensi AI belum terinstall: {e}."
        ) from e

    TOKENIZER = AutoTokenizer.from_pretrained(MODEL_PATH)
    SESSION = ort.InferenceSession(MODEL_FILE)
    SESSION_INPUTS = {entry.name for entry in SESSION.get_inputs()}


def _siapkan_feed(teks):
    inputs = TOKENIZER(teks, padding=True, truncation=True, return_tensors="np")
    feed = {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"],
    }
    if "token_type_ids" in SESSION_INPUTS and "token_type_ids" in inputs:
        feed["token_type_ids"] = inputs["token_type_ids"]
    return feed, inputs["attention_mask"]


def get_embedding(teks):
    _muat_engine()
    feed, attention_mask = _siapkan_feed(teks)
    outputs = SESSION.run(None, feed)

    token_embeddings = outputs[0].astype("float32")
    input_mask_expanded = attention_mask[..., None].astype("float32")

    sum_embeddings = (token_embeddings * input_mask_expanded).sum(axis=1)
    sum_mask = input_mask_expanded.sum(axis=1).clip(min=1e-9)

    return (sum_embeddings / sum_mask)[0]


def hitung_cosine_similarity(vec1, vec2):
    import numpy as np
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))