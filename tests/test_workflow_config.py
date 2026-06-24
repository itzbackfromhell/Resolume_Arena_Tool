from resolume_alpha_tool.core.settings import AppSettings
from resolume_alpha_tool.core.workflow_config import resolve_workflow_config


def test_resolve_workflow_config_uses_settings_without_profile() -> None:
    settings = AppSettings(export_target="resolume", resolume_preset="4k", fit_mode="cover", edge_profile="soft")

    config = resolve_workflow_config(settings, model="u2netp")

    assert config.target == "resolume"
    assert config.profile is None
    assert config.options.rembg_model == "u2netp"
    assert config.options.canvas_width == 3840
    assert config.options.canvas_height == 2160
    assert config.options.fit_mode == "cover"


def test_resolve_workflow_config_uses_profile_when_requested() -> None:
    settings = AppSettings(export_target="shirt_print")

    config = resolve_workflow_config(settings, profile_key="4k", model="u2netp")

    assert config.target == "resolume"
    assert config.profile is not None
    assert config.profile.key == "resolume_4k"
    assert config.options.rembg_model == "u2netp"
    assert config.options.canvas_width == 3840


def test_resolve_workflow_config_can_build_layout(tmp_path) -> None:
    settings = AppSettings(export_target="shirt_print", shirt_padding=128)

    config = resolve_workflow_config(settings, output_root=tmp_path, create_layout=True)

    assert config.layout is not None
    assert config.layout.assets_dir.is_dir()
    assert config.layout.root_dir == tmp_path / "shirt-print" / "settings_shirt_print"
    assert config.options.padding == 128
