from typing import Union, List, Optional

import torch
import numpy as np
import clip

from .clip_singleton import ClipSingleton, DEFAULT_MODEL
from src.image import ImageType, resize_crop


def get_text_features(
        text: Union[str, List[str]],
        model: str = DEFAULT_MODEL,
        device: str = "auto",
) -> np.ndarray:
    model, _ = ClipSingleton.get(model, device)

    is_array = not isinstance(text, str)
    if not is_array:
        text = [text]

    tokens = clip.tokenize(text).to(device)
    with torch.no_grad():
        features = model.encode_text(tokens).cpu().numpy()

    # features /= np.linalg.norm(features, axis=-1, keepdims=True)

    if is_array:
        return features
    else:
        return features[0]


def get_image_features(
        image: Union[ImageType, List[ImageType]],
        model: str = DEFAULT_MODEL,
        device: str = "auto",
) -> np.ndarray:

    is_array = isinstance(image, (list, tuple))
    if not is_array:
        image = [image]

    model, preprocess = ClipSingleton.get(model, device)

    with torch.no_grad():
        resized_images = [
            preprocess(resize_crop(i, [244, 244]))
            for i in image
        ]
        torch_images = torch.stack(resized_images).to(model.device)
        features = model.encode_image(torch_images).cpu().numpy()

    # features /= np.linalg.norm(features, axis=-1, keepdims=True)

    if is_array:
        return features
    else:
        return features[0]

