import os
from pathlib import Path
from typing import Union, List, Type

import numpy as np
import torch
import torchvision.transforms.functional as VT
import PIL.Image


ImageType = Union[PIL.Image.Image, np.ndarray, torch.Tensor]


def is_image_filename(filename: Union[str, Path]):
    if isinstance(filename, Path):
        ext = filename.suffix
    else:
        ext = os.path.splitext(filename)

    return ext.lower() in PIL.Image.registered_extensions()


def image_to_pil(image: ImageType) -> PIL.Image.Image:
    if isinstance(image, PIL.Image.Image):
        return image

    elif isinstance(image, torch.Tensor):
        data = image.cpu().detach().numpy()

    elif isinstance(image, np.ndarray):
        data = image

    else:
        raise TypeError(f"Can't convert image of type '{type(image).__name__}'")

    channels = data.shape[0]
    if data.ndim == 2:
        mode = "L"
        data = data.reshape((1, *data.shape))
        channels = 1

    elif channels == 1:
        mode = "L"

    elif channels == 3:
        mode = "RGB"

    elif channels == 4:
        mode = "RGBA"

    else:
        raise ValueError(f"Can't convert number of channels {channels}")

    data = np.clip(data, 0, 255).astype(np.int8)
    # [C, H, W] -> [H, W, C]
    data = data.transpose(1, 2, 0)

    # flip Y
    data = data[::-1, ...]

    if channels == 1:
        data = data.squeeze()

    return PIL.Image.fromarray(data, mode=mode)


def image_to_numpy(image: ImageType) -> np.ndarray:
    if isinstance(image, PIL.Image.Image):
        data = np.array(image.getdata())

        if image.mode == "L":
            data = data.reshape(image.height, image.width, 1)

        elif image.mode == "RGB":
            data = data.reshape(image.height, image.width, 3)

        elif image.mode == "RGBA":
            data = data.reshape(image.height, image.width, 4)

        else:
            raise ValueError(f"Can't convert image of mode '{image.mode}'")

        # flip Y
        data = data[::-1, ...]
        # [H, W, C] -> [C, H, W]
        data = data.transpose(2, 0, 1)

        return data

    elif isinstance(image, torch.Tensor):
        return image.numpy()

    elif isinstance(image, np.ndarray):
        return image

    else:
        raise TypeError(f"Can't convert image of type '{type(image).__name__}'")


def image_to_torch(image: ImageType) -> torch.Tensor:
    array = image_to_numpy(image)
    if array.strides:
        array = array.copy()
    return torch.Tensor(array)


def resize_crop(
        image: Union[torch.Tensor, PIL.Image.Image],
        resolution: List[int],
) -> Union[torch.Tensor, PIL.Image.Image]:
    if isinstance(image, PIL.Image.Image):
        width, height = image.width, image.height
    else:
        width, height = image.shape[-1], image.shape[-2]

    if width != resolution[0] or height != resolution[1]:

        if width < height:
            factor = max(resolution) / width
        else:
            factor = max(resolution) / height

        image = VT.resize(
            image,
            [int(height * factor), int(width * factor)],
            interpolation=VT.InterpolationMode.BICUBIC,
        )

        if isinstance(image, PIL.Image.Image):
            width, height = image.width, image.height
        else:
            width, height = image.shape[-1], image.shape[-2]

        if width != resolution[0] or height != resolution[1]:
            image = VT.center_crop(image, resolution)

    return image
