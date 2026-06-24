"""Persistent user workflow profile loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .profiles import WorkflowProfile, built_in_profiles, merge_profiles, profile_from_json_object
from .settings import load_json_object, save_json_object, user_presets_path

PROFILES_KEY = "profiles"


def _profile_entries(payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    raw_profiles = payload.get(PROFILES_KEY, [])
    if not isinstance(raw_profiles, list):
        return ()
    return tuple(item for item in raw_profiles if isinstance(item, dict))


def load_user_profiles(path: Path | None = None) -> tuple[WorkflowProfile, ...]:
    """Load user-defined workflow profiles from disk.

    Invalid entries are skipped so a broken custom profile cannot prevent the
    app from starting. Built-in profiles remain available through
    ``load_available_profiles``.
    """

    payload = load_json_object(path or user_presets_path())
    profiles: list[WorkflowProfile] = []
    for entry in _profile_entries(payload):
        try:
            profiles.append(profile_from_json_object(entry))
        except Exception:
            continue
    return tuple(profiles)


def load_available_profiles(path: Path | None = None) -> tuple[WorkflowProfile, ...]:
    """Return built-in profiles merged with user-defined profiles."""

    return merge_profiles(built_in_profiles(), load_user_profiles(path))


def save_user_profiles(profiles: tuple[WorkflowProfile, ...], path: Path | None = None) -> Path:
    """Persist user-defined workflow profiles."""

    target = path or user_presets_path()
    save_json_object(target, {PROFILES_KEY: [profile.to_json_object() for profile in profiles]})
    return target
