from .image import ImageType


class Stage:

    def __init__(self):
        pass

    def apply_to_image(self, image: ImageType):
        raise NotImplemented

