"""Bridge app settings, workflow profiles, and export options."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from .models import ExportTarget, ProcessingOptions
from .profiles import WorkflowProfile, get_profile
from .resolume_export import normalize_export_target, resolume_processing_options, shirt_print_processing_options
from .settings import AppSettings
from .workflow_structure import WorkflowExportLayout, build_workflow_export_layout


@dataclass(frozen=True)
class WorkflowConfig:
    """Resolved private workflow configuration for one export flow."""

    target: ExportTarget
    profile: WorkflowProfile | None
    options: ProcessingOptions
    layout: WorkflowExportLayout | None = None


def _settings_options(settings: AppSettings, *, model: str) -> ProcessingOptions:
    target = normalize_export_target(settings.export_target)
    if target == "shirt_print":
        return shirt_print_processing_options(
            model,
            padding=settings.shirt_padding,
            edge_profile=settings.edge_profile,
        )
    return resolume_processing_options(
        model,
        canvas_size=_canvas_size_from_settings(settings),
        fit_mode=settings.fit_mode,
        edge_profile=settings.edge_profile,
    )


def _canvas_size_from_settings(settings: AppSettings) -> tuple[int, int]:
    from .resolume_export import normalize_resolume_preset

    return normalize_resolume_preset(settings.resolume_preset)


def resolve_workflow_config(
    settings: AppSettings,
    *,
    profile_key: str | None = None,
    model: str | None = None,
    output_root: Path | None = None,
    create_layout: bool = False,
) -> WorkflowConfig:
    """Resolve settings and an optional profile into export-ready configuration."""

    profile = get_profile(profile_key) if profile_key else None
    if profile is not None:
        selected_model = model or profile.model
        profile = replace(profile, model=selected_model)
        options = profile.to_processing_options()
        target = profile.target
    else:
        selected_model = model or "u2net"
        target = normalize_export_target(settings.export_target)
        options = _settings_options(settings, model=selected_model)

    layout = None
    if output_root is not None:
        layout_profile = profile or WorkflowProfile(
            key=f"settings_{target}",
            label="Settings Workflow",
            target=target,
            model=selected_model,
            resolume_preset=settings.resolume_preset,
            fit_mode=settings.fit_mode,
            edge_profile=settings.edge_profile,
            shirt_padding=settings.shirt_padding,
        )
        layout = build_workflow_export_layout(output_root, layout_profile, create=create_layout)

    return WorkflowConfig(target=target, profile=profile, options=options, layout=layout)
