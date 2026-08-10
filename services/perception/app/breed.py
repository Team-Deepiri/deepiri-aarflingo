"""Dog breed classifier — Stanford Dogs fine-tuned MobileNetV3 with an
ImageNet-based zero-training fallback.

Detection (YOLO) answers "is there a dog".  This module answers "what kind of
dog".  The 120 Stanford Dogs breeds are all ImageNet-1k synsets, so a plain
pretrained MobileNetV3-Large can already produce a reasonable top-k breed guess
with no training.  When `breed.pt` (a fine-tuned checkpoint) is present we use
it instead — it is materially more accurate on the 120-way task.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

IMAGENET_DOG_INDICES = list(range(151, 269))  # ImageNet dog-breed classes


def default_breed_weights(root: Path | None = None) -> Path:
    base = root or Path(__file__).resolve().parents[3]
    return base / "artifacts" / "models" / "vision" / "breed.pt"


def default_breed_labels(root: Path | None = None) -> Path:
    base = root or Path(__file__).resolve().parents[3]
    return base / "artifacts" / "models" / "vision" / "breed_labels.json"


def _imagenet_names() -> list[str]:
    """1000 ImageNet-1k class names (order matches torchvision pretrained heads)."""
    p = Path(__file__).with_name("imagenet_classes.txt")
    if p.exists():
        return [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    return []


class BreedClassifier:
    def __init__(self, weights: Path | None = None) -> None:
        self._weights = weights or default_breed_weights()
        self._labels: list[str] | None = None
        self._model = None  # type: ignore[assignment]
        self._transform = None
        self._imagenet_model = None  # type: ignore[assignment]
        self._use_finetuned = self._load_finetuned()
        self._load_imagenet()

    # -- model loading -----------------------------------------------------

    def _load_finetuned(self) -> bool:
        import torch
        import torchvision.transforms as T

        w = self._weights
        if not w.exists():
            return False
        labels_p = self._weights.with_name("breed_labels.json")
        if not labels_p.exists():
            return False
        try:
            import torchvision.models as M

            labels = json.loads(labels_p.read_text(encoding="utf-8"))
            model = M.mobilenet_v3_large(weights=None)
            in_features = model.classifier[-1].in_features
            model.classifier[-1] = torch.nn.Linear(in_features, len(labels))
            state = torch.load(w, map_location="cpu", weights_only=True)
            model.load_state_dict(state)
            model.eval()
            self._model = model
            self._labels = labels
            self._transform = T.Compose(
                [
                    T.ToTensor(),
                    T.Resize((224, 224)),
                    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ]
            )
            return True
        except Exception:
            return False

    def _load_imagenet(self) -> None:
        import torchvision.transforms as T

        self._names = _imagenet_names()
        self._labels = self._names
        if not self._names:
            self._imagenet_model = None  # type: ignore[assignment]
            self._transform = None
            return
        import torchvision.models as M

        self._imagenet_model = M.mobilenet_v3_large(weights=M.MobileNet_V3_Large_Weights.IMAGENET1K_V1)
        self._imagenet_model.eval()
        if self._model is None:
            self._model = self._imagenet_model
        self._transform = T.Compose(
            [
                T.ToTensor(),
                T.Resize((224, 224)),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    @property
    def mode(self) -> str:
        return "finetuned" if self._use_finetuned else "imagenet"

    @property
    def available(self) -> bool:
        return self._model is not None and self._transform is not None

    # -- inference ---------------------------------------------------------

    def _softmax(self, logits: np.ndarray) -> np.ndarray:
        e = np.exp(logits - logits.max())
        return e / e.sum()

    def _probs(self, model, img: np.ndarray) -> np.ndarray:
        import torch

        with torch.no_grad():
            x = self._transform(img).unsqueeze(0)
            return self._softmax(model(x)[0].numpy())

    def _imagenet_top(self, probs: np.ndarray, top_k: int) -> list[tuple[str, float]]:
        dog = [(i, probs[i]) for i in IMAGENET_DOG_INDICES]
        dog.sort(key=lambda t: t[1], reverse=True)
        return [(self._names[i], float(p)) for i, p in dog[:top_k]]

    def classify_crop(self, crop_bgr: np.ndarray, top_k: int = 3) -> list[tuple[str, float]]:
        """Return [(breed_name, confidence), ...] for a BGR dog-region crop.

        When a fine-tuned checkpoint is present we use a max-rule ensemble:
        run both the fine-tuned head and the ImageNet dog-only head, and trust
        whichever is most confident for the top-1 guess.
        """
        if not self.available:
            return []
        img = crop_bgr[:, :, ::-1].copy()  # BGR -> RGB (contiguous for torch)

        if self._use_finetuned and self._imagenet_model is not None:
            ft_probs = self._probs(self._model, img)
            im_probs = self._probs(self._imagenet_model, img)
            im_top = self._imagenet_top(im_probs, top_k)
            # fine-tuned uses 120-class labels; ImageNet head maps to breed names.
            ft_order = np.argsort(ft_probs)[::-1][:top_k]
            ft_names = [(self._labels[i], float(ft_probs[i])) for i in ft_order]
            # Max-rule: pick the prediction set whose top-1 confidence wins.
            if ft_names[0][1] >= im_top[0][1]:
                return ft_names
            return im_top

        probs = self._probs(self._model, img)
        if self._use_finetuned:
            order = np.argsort(probs)[::-1][:top_k]
            return [(self._labels[i], float(probs[i])) for i in order]
        return self._imagenet_top(probs, top_k)

    def best(self, crop_bgr: np.ndarray) -> tuple[str | None, float]:
        top = self.classify_crop(crop_bgr, top_k=1)
        if not top:
            return None, 0.0
        name, conf = top[0]
        return name, conf


def classify_breed_crop(crop_bgr: np.ndarray, classifier: BreedClassifier | None = None, top_k: int = 3):
    clf = classifier or BreedClassifier()
    return clf.classify_crop(crop_bgr, top_k=top_k)


def default_breed_labels_map(root: Path | None = None) -> dict[str, int]:
    p = default_breed_labels(root)
    if not p.exists():
        return {}
    return {name: i for i, name in enumerate(json.loads(p.read_text(encoding="utf-8")))}
