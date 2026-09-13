import os
from django.conf import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, 'model_onnx')
MODEL_FILE = os.path.join(MODEL_PATH, 'model.onnx')
TOKENIZER = None
SESSION = None


class ModelTidakTersedia(Exception):
    pass


def _muat_engine():
    global TOKENIZER, SESSION
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


def get_embedding(teks):
    _muat_engine()
    inputs = TOKENIZER(teks, padding=True, truncation=True, return_tensors="np")

    outputs = SESSION.run(None, {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"],
        "token_type_ids": inputs["token_type_ids"]
    })

    token_embeddings = outputs[0]
    attention_mask = inputs["attention_mask"]

    input_mask_expanded = attention_mask[..., None].astype("float32")
    sum_embeddings = token_embeddings.astype("float32") * input_mask_expanded
    sum_embeddings = sum_embeddings.sum(axis=1)
    sum_mask = input_mask_expanded.sum(axis=1).clip(min=1e-9)

    return (sum_embeddings / sum_mask)[0]


def hitung_cosine_similarity(vec1, vec2):
    import numpy as np
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))