from typing import Union, List, Type

import numpy as np
import torch
import PIL.Image


ImageType = Union[PIL.Image.Image, np.ndarray, torch.Tensor]


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

