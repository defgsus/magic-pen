from .image import ImageType


class Stage:

    def __init__(self):
        pass

    def step(self, image: ImageType) -> ImageType:
        raise NotImplemented

