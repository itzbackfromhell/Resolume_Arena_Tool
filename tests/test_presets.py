from resolume_alpha_tool.core.models import ProcessingOptions
from resolume_alpha_tool.core.presets import options_from_preset


def test_options_from_preset_overrides_known_fields() -> None:
    options = options_from_preset({"alpha_threshold": 42, "unknown": "ignored"})
    assert isinstance(options, ProcessingOptions)
    assert options.alpha_threshold == 42
