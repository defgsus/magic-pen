import torch


def get_torch_device(device: str = "auto") -> str:
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("Cuda device requested but not available")

    return device
