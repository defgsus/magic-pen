from typing import List, Tuple

import torch
import clip

from .device import get_torch_device


CLIP_MODELS: List[str] = clip.available_models()

DEFAULT_MODEL = "ViT-B/32"

MODEL_DIMENSIONS = {
    "ViT-B/32": 512,
}

class ClipSingleton:

    _models = dict()

    @classmethod
    def get(cls, model: str, device: str) -> Tuple[torch.nn.Module, torch.nn.Module]:
        """
        Return CLIP model and preprocessor.

        :param model: str, name
        :param device: str, a torch device or 'auto'
        :return: tuple of (Module, Module)
        """
        device = get_torch_device(device)

        key = f"{model}/{device}"

        if key not in cls._models:
            model, preproc = clip.load(name=model, device=device)
            model.device = device  # store for later use
            cls._models[key] = (model, preproc)

        return cls._models[key]
