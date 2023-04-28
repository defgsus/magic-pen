
import diffusers

from ..stage import *


class DiffusionStage(Stage):

    def __init__(self):
        super().__init__()

    def step(self, image: ImageType) -> ImageType:
        # TODO
        diffusers.StableDiffusionPipeline
        return image
