from typing import Union, List, Optional, Iterable

import torch
import numpy as np
import clip

from src.config import DEFAULT_CLIP_MODEL
from src.image import ImageType, resize_crop
from .clip_singleton import ClipSingleton
from .device import get_torch_device


def get_text_features(
        text: Union[str, Iterable[str]],
        model: str = DEFAULT_CLIP_MODEL,
        device: str = "auto",
) -> np.ndarray:
    device = get_torch_device(device)

    model, _ = ClipSingleton.get(model, device)

    if isinstance(text, str):
        is_array = False
        text = [text]
    else:
        is_array = True
        if not isinstance(text, list):
            text = list(text)

    tokens = clip.tokenize(text).to(device)
    with torch.no_grad():
        features = model.encode_text(tokens).cpu().numpy()

    # features /= np.linalg.norm(features, axis=-1, keepdims=True)

    if is_array:
        return features
    else:
        return features[0]


def get_image_features(
        images: Iterable[ImageType],
        model: str = DEFAULT_CLIP_MODEL,
        device: str = "auto",
) -> np.ndarray:
    device = get_torch_device(device)

    if not isinstance(images, (list, tuple)):
        images = list(images)

    model, preprocess = ClipSingleton.get(model, device)

    with torch.no_grad():
        resized_images = [
            preprocess(resize_crop(i, [224, 224]))
            for i in images
        ]
        torch_images = torch.stack(resized_images).to(model.device)
        features = model.encode_image(torch_images).cpu().numpy()

    # features /= np.linalg.norm(features, axis=-1, keepdims=True)

    return features

