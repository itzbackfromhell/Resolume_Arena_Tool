"""Named export workflow profiles for Resolume and print targets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

from .exceptions import ProcessingError
from .models import ExportTarget, FitMode, ProcessingOptions
from .resolume_export import (
    DEFAULT_REMBG_MODEL,
    RESOLUME_PRESETS,
    normalize_export_target,
    normalize_resolume_preset,
    resolume_processing_options,
    shirt_print_processing_options,
)

PROFILE_KEY_ALIASES: dict[str, str] = {
    "resolume": "resolume_1080p",
    "1080p": "resolume_1080p",
    "arena": "resolume_1080p",
    "avenue": "resolume_1080p",
    "4k": "resolume_4k",
    "uhd": "resolume_4k",
    "square": "resolume_square_1080",
    "square_1080": "resolume_square_1080",
    "shirt": "shirt_print_clean",
    "print": "shirt_print_clean",
    "shirt_print": "shirt_print_clean",
}
VALID_FIT_MODES: frozenset[str] = frozenset({"contain", "cover", "stretch"})
VALID_EDGE_PROFILES: frozenset[str] = frozenset({"normal", "soft", "tight", "grow"})


@dataclass(frozen=True)
class WorkflowProfile:
    """One named export workflow preset.

    Profiles intentionally store UI/workflow choices rather than raw image
    algorithms. ``to_processing_options`` is the single conversion point into
    deterministic export settings.
    """

    key: str
    label: str
    target: ExportTarget = "resolume"
    model: str = DEFAULT_REMBG_MODEL
    resolume_preset: str = "1080p"
    fit_mode: FitMode = "contain"
    edge_profile: str = "normal"
    shirt_padding: int = 96
    overwrite: bool = False
    description: str = ""

    def to_json_object(self) -> dict[str, str | int | bool]:
        """Return a stable JSON-object-compatible representation."""

        return asdict(self)

    def to_processing_options(self) -> ProcessingOptions:
        """Build export processing options for this profile."""

        if self.target == "shirt_print":
            options = shirt_print_processing_options(
                self.model,
                padding=self.shirt_padding,
                edge_profile=self.edge_profile,
            )
        else:
            options = resolume_processing_options(
                self.model,
                canvas_size=normalize_resolume_preset(self.resolume_preset),
                fit_mode=self.fit_mode,
                edge_profile=self.edge_profile,
            )
        return replace(options, overwrite=self.overwrite)


BUILT_IN_WORKFLOW_PROFILES: tuple[WorkflowProfile, ...] = (
    WorkflowProfile(
        key="resolume_1080p",
        label="Resolume 1080p Alpha PNG",
        target="resolume",
        resolume_preset="1080p",
        fit_mode="contain",
        edge_profile="normal",
        description="Default transparent 1920x1080 PNG for Resolume Arena/Avenue decks.",
    ),
    WorkflowProfile(
        key="resolume_4k",
        label="Resolume 4K Alpha PNG",
        target="resolume",
        resolume_preset="4k",
        fit_mode="contain",
        edge_profile="normal",
        description="Transparent 3840x2160 PNG for UHD visual workflows.",
    ),
    WorkflowProfile(
        key="resolume_square_1080",
        label="Resolume Square 1080 Alpha PNG",
        target="resolume",
        resolume_preset="square_1080",
        fit_mode="contain",
        edge_profile="normal",
        description="Transparent square PNG for loopable social/VJ source assets.",
    ),
    WorkflowProfile(
        key="shirt_print_clean",
        label="Shirt/Print Clean PNG",
        target="shirt_print",
        edge_profile="tight",
        shirt_padding=96,
        description="Trimmed transparent PNG with print-safe padding and a tighter alpha edge.",
    ),
)


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def normalize_profile_key(value: str) -> str:
    """Normalize a profile key and resolve built-in aliases."""

    key = _normalize_key(value)
    return PROFILE_KEY_ALIASES.get(key, key)


def built_in_profiles() -> tuple[WorkflowProfile, ...]:
    """Return bundled workflow profiles in stable UI order."""

    return BUILT_IN_WORKFLOW_PROFILES


def profile_map(profiles: tuple[WorkflowProfile, ...] | None = None) -> dict[str, WorkflowProfile]:
    """Return profiles keyed by normalized key."""

    selected_profiles = profiles if profiles is not None else BUILT_IN_WORKFLOW_PROFILES
    return {normalize_profile_key(profile.key): profile for profile in selected_profiles}


def get_profile(key: str, profiles: tuple[WorkflowProfile, ...] | None = None) -> WorkflowProfile:
    """Resolve one profile by key or alias."""

    resolved_key = normalize_profile_key(key)
    profiles_by_key = profile_map(profiles)
    if resolved_key in profiles_by_key:
        return profiles_by_key[resolved_key]
    available = ", ".join(sorted(profiles_by_key))
    raise ProcessingError(f"Unknown workflow profile: {key}. Available profiles: {available}.")


def _string_value(raw: dict[str, Any], key: str, default: str) -> str:
    value = raw.get(key, default)
    if isinstance(value, str):
        return value
    if value is None:
        return default
    return str(value)


def _bool_value(raw: dict[str, Any], key: str, default: bool = False) -> bool:
    value = raw.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "yes", "true", "on"}
    return bool(value)


def _int_value(raw: dict[str, Any], key: str, default: int, *, minimum: int = 0) -> int:
    value = raw.get(key, default)
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, number)


def _normalize_fit_mode(value: str) -> FitMode:
    normalized = value.strip().lower().replace("-", "_")
    if normalized in VALID_FIT_MODES:
        return normalized  # type: ignore[return-value]
    raise ProcessingError(f"Unknown fit mode in workflow profile: {value}.")


def _normalize_edge_profile(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_")
    if normalized in VALID_EDGE_PROFILES:
        return normalized
    raise ProcessingError(f"Unknown edge cleanup profile in workflow profile: {value}.")


def profile_from_json_object(raw: dict[str, Any]) -> WorkflowProfile:
    """Build and validate one profile from JSON-like data."""

    key = normalize_profile_key(_string_value(raw, "key", ""))
    if not key:
        raise ProcessingError("Workflow profile is missing a key.")

    target = normalize_export_target(_string_value(raw, "target", "resolume"))
    resolume_preset = _string_value(raw, "resolume_preset", "1080p").strip().lower().replace("-", "_")
    if resolume_preset not in RESOLUME_PRESETS:
        raise ProcessingError(f"Unknown Resolume preset in workflow profile: {resolume_preset}.")

    return WorkflowProfile(
        key=key,
        label=_string_value(raw, "label", key.replace("_", " ").title()),
        target=target,
        model=_string_value(raw, "model", DEFAULT_REMBG_MODEL),
        resolume_preset=resolume_preset,
        fit_mode=_normalize_fit_mode(_string_value(raw, "fit_mode", "contain")),
        edge_profile=_normalize_edge_profile(_string_value(raw, "edge_profile", "normal")),
        shirt_padding=_int_value(raw, "shirt_padding", 96),
        overwrite=_bool_value(raw, "overwrite"),
        description=_string_value(raw, "description", ""),
    )


def merge_profiles(
    built_ins: tuple[WorkflowProfile, ...],
    user_profiles: tuple[WorkflowProfile, ...],
) -> tuple[WorkflowProfile, ...]:
    """Merge built-in and user profiles, allowing user profiles to override keys."""

    merged: dict[str, WorkflowProfile] = {}
    for profile in built_ins + user_profiles:
        merged[normalize_profile_key(profile.key)] = profile
    return tuple(merged.values())
