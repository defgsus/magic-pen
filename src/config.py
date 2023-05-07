from pathlib import Path

from decouple import config


PROJECT_PATH: Path = Path(__file__).parent.parent
RESULTS_PATH: Path = config("MP_RESULTS_PATH", default=PROJECT_PATH / "results", cast=Path)
DATABASE_PATH: Path = config("MP_DATABASE_PATH", default=PROJECT_PATH / "db", cast=Path)

DEFAULT_CLIP_MODEL: str = config("MP_DEFAULT_CLIP_MODEL", default="ViT-B/32")
