"""Cooking profile helpers for Xiaomi Electric Rice Cooker."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import re

from .const import (
    MODEL_NORMAL2,
    MODEL_NORMAL3,
    MODEL_NORMAL4,
    MODEL_NORMAL5,
    MODEL_PRESSURE1,
    MODEL_PRESSURE2,
)

PROFILE_DATA_FILE = "cooker_profiles.json"
PROFILE_KEY_PATTERN = re.compile(r"[^a-z0-9]+")

PROFILE_GROUP_MODELS: dict[str, tuple[str, ...]] = {
    "MODEL_PRESSURE": (MODEL_PRESSURE1, MODEL_PRESSURE2),
    "MODEL_NORMAL_GROUP1": (MODEL_NORMAL2, MODEL_NORMAL5),
    "MODEL_NORMAL_GROUP2": (MODEL_NORMAL3, MODEL_NORMAL4),
}

MODEL_TO_PROFILE_GROUP = {
    model: group
    for group, models in PROFILE_GROUP_MODELS.items()
    for model in models
}


@dataclass(slots=True, frozen=True)
class CookingProfile:
    """A selectable cooking profile."""

    key: str
    title: str
    description: str
    profile: str


def _normalize_profile_key(title: str) -> str:
    """Convert a profile title into a stable option key."""
    normalized = PROFILE_KEY_PATTERN.sub("_", title.strip().lower()).strip("_")
    return normalized or "profile"


@lru_cache(maxsize=1)
def _load_profiles_by_group() -> dict[str, tuple[CookingProfile, ...]]:
    """Load bundled profile data."""
    raw_data = json.loads(
        Path(__file__).with_name(PROFILE_DATA_FILE).read_text(encoding="utf-8")
    )
    return {
        group: tuple(
            CookingProfile(
                key=_normalize_profile_key(item["title"]),
                title=item["title"],
                description=item["description"],
                profile=item["profile"],
            )
            for item in raw_data[group]
        )
        for group in PROFILE_GROUP_MODELS
    }


def get_profiles_for_model(model: str | None) -> tuple[CookingProfile, ...]:
    """Return supported cooking profiles for a given cooker model."""
    if model is None:
        return ()

    group = MODEL_TO_PROFILE_GROUP.get(model)
    if group is None:
        return ()

    return _load_profiles_by_group().get(group, ())
