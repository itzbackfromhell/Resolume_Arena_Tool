import json

from resolume_alpha_tool.core.profiles import get_profile
from resolume_alpha_tool.core.workflow_structure import (
    build_workflow_export_layout,
    layout_to_json_object,
    target_folder_name,
    workflow_manifest_payload,
    write_workflow_manifest,
)


def test_target_folder_name_is_stable() -> None:
    assert target_folder_name("resolume") == "resolume"
    assert target_folder_name("shirt_print") == "shirt-print"


def test_build_workflow_export_layout_is_deterministic(tmp_path) -> None:
    layout = build_workflow_export_layout(tmp_path, "4k")

    assert layout.root_dir == tmp_path / "resolume" / "resolume_4k"
    assert layout.assets_dir == layout.root_dir / "assets"
    assert layout.reports_dir == layout.root_dir / "reports"
    assert layout.manifests_dir == layout.root_dir / "manifests"
    assert layout.previews_dir == layout.root_dir / "previews"
    assert not layout.assets_dir.exists()


def test_build_workflow_export_layout_can_create_folders(tmp_path) -> None:
    layout = build_workflow_export_layout(tmp_path, "shirt", create=True)

    assert layout.assets_dir.is_dir()
    assert layout.reports_dir.is_dir()
    assert layout.manifests_dir.is_dir()
    assert layout.previews_dir.is_dir()


def test_workflow_manifest_payload_contains_profile_and_layout(tmp_path) -> None:
    profile = get_profile("square")
    layout = build_workflow_export_layout(tmp_path, profile)

    payload = workflow_manifest_payload(profile=profile, layout=layout, extra={"items": 2})

    assert payload["schema_version"] == 1
    assert payload["profile"]["key"] == "resolume_square_1080"
    assert payload["layout"]["assets_dir"].endswith("/assets")
    assert payload["extra"] == {"items": 2}


def test_write_workflow_manifest_roundtrip(tmp_path) -> None:
    profile = get_profile("resolume")
    layout = build_workflow_export_layout(tmp_path, profile, create=True)

    path = write_workflow_manifest(layout.manifest_path(), profile=profile, layout=layout)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["profile"]["key"] == "resolume_1080p"
    assert payload["layout"]["root_dir"].endswith("/resolume/resolume_1080p")


def test_layout_to_json_object_is_path_safe(tmp_path) -> None:
    layout = build_workflow_export_layout(tmp_path, "resolume")

    payload = layout_to_json_object(layout)

    assert payload["profile_key"] == "resolume_1080p"
    assert payload["assets_dir"].endswith("assets")
