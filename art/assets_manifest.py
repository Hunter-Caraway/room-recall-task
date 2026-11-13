"""Poly Haven (CC0) assets used to build the basements and the made objects.
Fetched by fetch_assets.py."""
import csv
import pathlib

from choose_models import ROOM_MODELS

_MADE = pathlib.Path(__file__).parent / "made_objects.csv"


def made_models() -> list[str]:
    with open(_MADE, encoding="utf-8", newline="") as handle:
        return [row["model"] for row in csv.DictReader(handle)]


ALL_MODELS = sorted(set(ROOM_MODELS) | set(made_models()))

TEXTURES = ["garage_floor", "painted_concrete", "concrete_block_wall", "oak_veneer_01", "plank_flooring_02",
            "concrete_floor_worn_001", "brick_wall_001"]
HDRIS = ["symmetrical_garden_02"]
