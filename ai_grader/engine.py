import os
import onnxruntime as ort
from transformers import AutoTokenizer
import numpy as np
from numpy.linalg import norm
from django.conf import settings

# Tentukan jalur folder model ONNX
MODEL_PATH = os.path.join(settings.BASE_DIR, 'model_onnx')

print("Memuat Tokenizer dan ONNX Session untuk AI Engine...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
session = ort.InferenceSession(os.path.join(MODEL_PATH, "model.onnx"))

def get_embedding(teks):
    """Fungsi mengubah teks menjadi vektor menggunakan ONNX dan Numpy"""
    inputs = tokenizer(teks, padding=True, truncation=True, return_tensors="np")
    
    outputs = session.run(None, {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"],
        "token_type_ids": inputs["token_type_ids"]
    })
    
    token_embeddings = outputs[0] 
    attention_mask = inputs["attention_mask"]
    
    input_mask_expanded = np.expand_dims(attention_mask, -1)
    sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
    sum_mask = np.clip(np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None)
    
    return (sum_embeddings / sum_mask)[0]

def hitung_cosine_similarity(vec1, vec2):
    """Menghitung kemiripan cosinus antara dua vektor"""
    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))