"""Chinese-CLIP model wrapper.

Set PICSEEK_MOCK_MODEL=1 to use a fast mock (for development/testing).
Otherwise loads the real OFA-Sys/chinese-clip-vit-base-patch16 model.
"""

import os

MODEL_NAME = "OFA-Sys/chinese-clip-vit-base-patch16"
EMBEDDING_DIM = 512

_instance = None


def get_model():
    global _instance
    if _instance is None:
        if os.environ.get("PICSEEK_MOCK_MODEL") == "1":
            _instance = MockCLIPModel()
        else:
            _instance = CLIPModel()
    return _instance


def reset_model():
    """Reset the singleton (for testing)."""
    global _instance
    _instance = None


class CLIPModel:
    def __init__(self):
        import torch
        from transformers import ChineseCLIPProcessor, ChineseCLIPModel as HFModel

        self.device = self._get_device()
        self.processor = ChineseCLIPProcessor.from_pretrained(MODEL_NAME)
        self.model = HFModel.from_pretrained(MODEL_NAME)
        self.model.to(self.device)
        self.model.eval()

    @staticmethod
    def _get_device() -> str:
        import torch
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def encode_image(self, image_path: str) -> list[float]:
        import torch
        from PIL import Image

        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            features = self.model.get_image_features(**inputs)
        features = features / features.norm(p=2, dim=-1, keepdim=True)
        return features.squeeze().cpu().tolist()

    def encode_images(self, image_paths: list[str]) -> list[list[float]]:
        import torch
        from PIL import Image

        images = [Image.open(p).convert("RGB") for p in image_paths]
        inputs = self.processor(images=images, return_tensors="pt").to(self.device)
        with torch.no_grad():
            features = self.model.get_image_features(**inputs)
        features = features / features.norm(p=2, dim=-1, keepdim=True)
        return features.cpu().tolist()

    def encode_text(self, text: str) -> list[float]:
        import torch

        inputs = self.processor(text=[text], padding=True, return_tensors="pt").to(self.device)
        with torch.no_grad():
            features = self.model.get_text_features(**inputs)
        features = features / features.norm(p=2, dim=-1, keepdim=True)
        return features.squeeze().cpu().tolist()


class MockCLIPModel:
    """Fast mock for development and testing. Returns deterministic vectors."""

    def __init__(self):
        self.model = True
        self.processor = True

    def _hash_to_vector(self, data: str) -> list[float]:
        import hashlib
        h = hashlib.sha512(data.encode()).digest()
        raw = []
        for i in range(EMBEDDING_DIM):
            byte_val = h[i % len(h)]
            raw.append((byte_val / 255.0) * 2 - 1)
        norm = sum(x * x for x in raw) ** 0.5
        return [x / norm for x in raw]

    def encode_image(self, image_path: str) -> list[float]:
        return self._hash_to_vector(f"image:{image_path}")

    def encode_images(self, image_paths: list[str]) -> list[list[float]]:
        return [self.encode_image(p) for p in image_paths]

    def encode_text(self, text: str) -> list[float]:
        return self._hash_to_vector(f"text:{text}")
