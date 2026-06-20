"""Safe Resolume-oriented export profile helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import ProcessingOptions


@dataclass(frozen=True)
class ResolumeExportProfile:
    name: str
    description: str
    options: ProcessingOptions
    suggested_folder: str


PROFILES: dict[str, ResolumeExportProfile] = {
    "overlay_1080p": ResolumeExportProfile(
        name="overlay_1080p",
        description="Transparent 1920x1080 overlay asset for Arena/Avenue decks.",
        options=ProcessingOptions(fit_mode="contain", canvas_width=1920, canvas_height=1080, output_format="png"),
        suggested_folder="Resolume_Overlays_1080p",
    ),
    "overlay_4k": ResolumeExportProfile(
        name="overlay_4k",
        description="Transparent 3840x2160 overlay asset for 4K compositions.",
        options=ProcessingOptions(fit_mode="contain", canvas_width=3840, canvas_height=2160, output_format="png"),
        suggested_folder="Resolume_Overlays_4K",
    ),
    "logo_bug": ResolumeExportProfile(
        name="logo_bug",
        description="Auto-cropped logo/sticker element with padding and clean alpha.",
        options=ProcessingOptions(auto_crop=True, padding=48, alpha_threshold=12, feather_radius=0.4, output_format="png"),
        suggested_folder="Resolume_Logos",
    ),
    "vj_glow_stage": ResolumeExportProfile(
        name="vj_glow_stage",
        description="Glow-heavy stage asset for dark VJ visuals.",
        options=ProcessingOptions(
            auto_crop=True,
            padding=96,
            glow_radius=22.0,
            fit_mode="contain",
            canvas_width=1920,
            canvas_height=1080,
            output_format="png",
        ),
        suggested_folder="Resolume_Glow_Assets",
    ),
}


def get_profile(name: str) -> ResolumeExportProfile:
    try:
        return PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown Resolume profile: {name}") from exc


def profile_output_dir(base_dir: Path, profile: ResolumeExportProfile) -> Path:
    return base_dir / profile.suggested_folder
