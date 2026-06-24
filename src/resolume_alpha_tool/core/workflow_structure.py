"""Folder layout helpers for professional Resolume export handoff."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .models import ExportTarget
from .profiles import WorkflowProfile, get_profile, normalize_profile_key


@dataclass(frozen=True)
class WorkflowExportLayout:
    """Deterministic output folders for one workflow profile."""

    root_dir: Path
    profile_key: str
    assets_dir: Path
    reports_dir: Path
    manifests_dir: Path
    previews_dir: Path

    def ensure(self) -> "WorkflowExportLayout":
        """Create all layout directories and return this layout."""

        for path in (self.assets_dir, self.reports_dir, self.manifests_dir, self.previews_dir):
            path.mkdir(parents=True, exist_ok=True)
        return self

    def manifest_path(self, name: str = "workflow_manifest.json") -> Path:
        """Return a manifest path inside the manifest folder."""

        return self.manifests_dir / name


def target_folder_name(target: ExportTarget) -> str:
    """Return a stable folder name for an export target."""

    return "shirt-print" if target == "shirt_print" else "resolume"


def build_workflow_export_layout(
    output_root: Path,
    profile: WorkflowProfile | str = "resolume_1080p",
    *,
    create: bool = False,
) -> WorkflowExportLayout:
    """Build the professional handoff folder layout for one profile."""

    workflow_profile = get_profile(profile) if isinstance(profile, str) else profile
    profile_key = normalize_profile_key(workflow_profile.key)
    workflow_root = output_root.expanduser() / target_folder_name(workflow_profile.target) / profile_key
    layout = WorkflowExportLayout(
        root_dir=workflow_root,
        profile_key=profile_key,
        assets_dir=workflow_root / "assets",
        reports_dir=workflow_root / "reports",
        manifests_dir=workflow_root / "manifests",
        previews_dir=workflow_root / "previews",
    )
    return layout.ensure() if create else layout


def workflow_manifest_payload(
    *,
    profile: WorkflowProfile,
    layout: WorkflowExportLayout,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a stable JSON manifest payload for a workflow export folder."""

    payload: dict[str, Any] = {
        "schema_version": 1,
        "profile": profile.to_json_object(),
        "layout": {
            "root_dir": layout.root_dir.as_posix(),
            "assets_dir": layout.assets_dir.as_posix(),
            "reports_dir": layout.reports_dir.as_posix(),
            "manifests_dir": layout.manifests_dir.as_posix(),
            "previews_dir": layout.previews_dir.as_posix(),
        },
    }
    if extra:
        payload["extra"] = extra
    return payload


def write_workflow_manifest(
    path: Path,
    *,
    profile: WorkflowProfile,
    layout: WorkflowExportLayout,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write one workflow manifest JSON file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = workflow_manifest_payload(profile=profile, layout=layout, extra=extra)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")
    return path


def layout_to_json_object(layout: WorkflowExportLayout) -> dict[str, str]:
    """Return a compact JSON-friendly layout object."""

    data = asdict(layout)
    return {key: str(value) for key, value in data.items()}
