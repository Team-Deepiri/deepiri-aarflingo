"""Train a MobileNetV3-Large dog-breed classifier on Stanford Dogs (120 breeds).

Stanford Dogs layout: data/raw/dog_images/Images/<synset>-<Breed>/*.jpg

Produces artifacts/models/vision/breed.pt + breed_labels.json that
`app.breed.BreedClassifier` loads as the `finetuned` mode (higher 120-way
accuracy than the ImageNet fallback).
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch

BREED_NAMES = None  # type: ignore[assignment]


def discover_breeds(images_root: Path) -> list[tuple[str, str]]:
    """Return [(breed_folder, human_name), ...] sorted by folder name."""
    out = []
    for d in sorted(images_root.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        if "-" in name:
            human = name.split("-", 1)[1].replace("_", " ")
        else:
            human = name.replace("_", " ")
        imgs = [p for p in d.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")]
        if imgs:
            out.append((name, human))
    return out


def build_splits(
    images_root: Path,
    seed: int = 42,
    train_frac: float = 0.85,
    val_frac: float = 0.10,
    max_per_class: int = 0,
) -> tuple[list[tuple[Path, int]], list[tuple[Path, int]], list[tuple[Path, int]], list[str]]:
    """Split images into train / val / test by class, returning (train, val, test, labels)."""
    rng = random.Random(seed)
    breeds = discover_breeds(images_root)
    labels: list[str] = [human for _, human in breeds]
    train: list[tuple[Path, int]] = []
    val: list[tuple[Path, int]] = []
    test: list[tuple[Path, int]] = []
    for idx, (folder, _) in enumerate(breeds):
        imgs = sorted(p for p in (images_root / folder).iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
        if max_per_class and len(imgs) > max_per_class:
            imgs = rng.sample(imgs, max_per_class)
        rng.shuffle(imgs)
        n = len(imgs)
        n_train = int(n * train_frac)
        n_val = int(n * val_frac)
        for p in imgs[:n_train]:
            train.append((p, idx))
        for p in imgs[n_train : n_train + n_val]:
            val.append((p, idx))
        for p in imgs[n_train + n_val :]:
            test.append((p, idx))
    return train, val, test, labels


def load_image(path: Path, size: int = 224) -> np.ndarray:
    import cv2

    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"cannot decode {path}")
    return cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)


class _Preprocessor:
    def __init__(self) -> None:
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 1, 3)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 1, 3)

    def __call__(self, bgr: np.ndarray) -> np.ndarray:
        rgb = bgr[:, :, ::-1].copy().astype(np.float32) / 255.0
        return ((rgb - self.mean) / self.std).transpose(2, 0, 1)


class _BreedDataset(torch.utils.data.Dataset):
    def __init__(self, split: list[tuple[Path, int]]) -> None:
        self.split = split
        self.pre = _Preprocessor()

    def __len__(self) -> int:
        return len(self.split)

    def __getitem__(self, i: int) -> tuple[torch.Tensor, torch.Tensor]:
        path, label = self.split[i]
        x = self.pre(load_image(path))
        return torch.from_numpy(x), torch.tensor(label, dtype=torch.long)


def _train_epoch(model, loader, criterion, optimizer, device, train=True) -> tuple[float, float]:
    total = 0
    correct = 0
    loss_sum = 0.0
    model.train(train)
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        if optimizer is not None:
            optimizer.zero_grad()
        logits = model(x)
        loss = criterion(logits, y)
        if train:
            loss.backward()
            optimizer.step()
        loss_sum += float(loss.item())
        total += int(y.numel())
        correct += int((logits.argmax(1) == y).sum().item())
    acc = correct / total if total else 0.0
    return loss_sum / (len(loader) or 1), acc


def train_breed(
    data_dir: Path | None = None,
    out_weights: Path | None = None,
    epochs: int = 6,
    batch_size: int = 64,
    lr: float = 1e-3,
    freeze_backbone: int = 4,
    seed: int = 42,
) -> dict:
    import torch
    import torchvision.models as M

    root = Path(__file__).resolve().parents[3]
    data_dir = data_dir or (root / "data" / "raw" / "dog_images" / "Images")
    out_weights = out_weights or (root / "artifacts" / "models" / "vision" / "breed.pt")
    out_labels = out_weights.with_name("breed_labels.json")

    if not data_dir.is_dir():
        raise FileNotFoundError(
            f"Stanford Dogs not found at {data_dir}. "
            "Run ./scripts/fetch_public_datasets.sh --dog-images first."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device: {device}  ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'})", file=sys.stderr)
    print(f"data:  {data_dir}", file=sys.stderr)

    train, val, test, labels = build_splits(data_dir, seed=seed)
    n_classes = len(labels)
    print(f"classes: {n_classes}  train: {len(train)}  val: {len(val)}  test: {len(test)}", file=sys.stderr)

    model = M.mobilenet_v3_large(weights=M.MobileNet_V3_Large_Weights.IMAGENET1K_V1)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = torch.nn.Linear(in_features, n_classes)
    model.to(device)

    # Freeze the backbone for the first `freeze_backbone` epochs (head-only), then
    # unfreeze the last blocks for a short fine-tune.
    for name, param in model.features.named_parameters():
        param.requires_grad = False

    pre = _Preprocessor()

    num_workers = min(8, max(1, (torch.get_num_threads() or 1)))
    train_dl = torch.utils.data.DataLoader(
        _BreedDataset(train), batch_size=batch_size, shuffle=True, num_workers=num_workers, persistent_workers=True
    )
    val_dl = torch.utils.data.DataLoader(
        _BreedDataset(val), batch_size=batch_size, shuffle=False, num_workers=num_workers
    )
    test_dl = torch.utils.data.DataLoader(
        _BreedDataset(test), batch_size=batch_size, shuffle=False, num_workers=num_workers
    )

    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val = 0.0
    best_state = None
    for epoch in range(1, epochs + 1):
        if epoch > freeze_backbone:
            for param in model.parameters():
                param.requires_grad = True
            optimizer = torch.optim.AdamW(
                [p for p in model.parameters() if p.requires_grad], lr=lr * 0.1
            )
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs - freeze_backbone)
        loader = train_dl
        loss, acc = _train_epoch(model, loader, criterion, optimizer, device, train=True)
        vloss, vacc = _train_epoch(model, val_dl, criterion, None, device, train=False)
        scheduler.step()
        print(
            f"epoch {epoch}/{epochs}  train_loss {loss:.3f}  train_acc {acc:.3f}  "
            f"val_loss {vloss:.3f}  val_acc {vacc:.3f}",
            file=sys.stderr,
        )
        if vacc > best_val:
            best_val = vacc
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    tloss, tacc = _train_epoch(model, test_dl, criterion, None, device, train=False)
    print(f"test acc {tacc:.3f}  (best val {best_val:.3f})", file=sys.stderr)

    out_weights.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_weights)
    out_labels.write_text(json.dumps(labels, indent=2), encoding="utf-8")
    return {
        "weights": str(out_weights),
        "labels": str(out_labels),
        "n_classes": n_classes,
        "train": len(train),
        "val": len(val),
        "test": len(test),
        "test_acc": round(tacc, 4),
        "best_val_acc": round(best_val, 4),
    }


if __name__ == "__main__":
    import json as _json

    kwargs = {}
    args = sys.argv[1:]
    if args:
        data_dir = Path(args[0]) if args[0] != "-" else None
        kwargs["data_dir"] = data_dir
    result = train_breed(**kwargs)
    print(_json.dumps(result, indent=2))
