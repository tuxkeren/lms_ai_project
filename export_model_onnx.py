"""Ekspor model embedding (sentence-transformers) ke format ONNX.

Cara pakai:
    python export_model_onnx.py
    python export_model_onnx.py --model indobenchmark/indobert-base-p1
"""

import argparse
import os

import torch
from transformers import AutoModel, AutoTokenizer

DIR_PROYEK = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(DIR_PROYEK, 'model_onnx')


class ModelEmbedding(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, input_ids, attention_mask, token_type_ids=None):
        hasil = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        return hasil.last_hidden_state


def main():
    parser = argparse.ArgumentParser(description='Ekspor model ke ONNX')
    parser.add_argument(
        '--model',
        default='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        help='Nama model di HuggingFace',
    )
    args = parser.parse_args()

    print(f"Mengunduh model '{args.model}'...")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModel.from_pretrained(args.model)
    model = ModelEmbedding(model)
    model.eval()

    dummy = tokenizer("contoh kalimat untuk mengekspor model", padding=True, truncation=True, return_tensors="pt")

    feed = [dummy["input_ids"], dummy["attention_mask"]]
    input_names = ["input_ids", "attention_mask"]
    if "token_type_ids" in dummy:
        feed.append(dummy["token_type_ids"])
        input_names.append("token_type_ids")

    os.makedirs(TARGET, exist_ok=True)

    dynamic_axes = {name: {0: "batch", 1: "seq"} for name in input_names}
    dynamic_axes["token_embeddings"] = {0: "batch", 1: "seq"}

    torch.onnx.export(
        model,
        tuple(feed),
        os.path.join(TARGET, "model.onnx"),
        input_names=input_names,
        output_names=["token_embeddings"],
        dynamic_axes=dynamic_axes,
        opset_version=14,
    )

    tokenizer.save_pretrained(TARGET)
    print(f"Selesai. Model tersimpan di '{TARGET}'")
    print(f"Input ONNX: {input_names}")


if __name__ == "__main__":
    main()