from resolume_alpha_tool.core.rembg_runtime import package_version, runtime_summary


def test_package_version_returns_string() -> None:
    assert isinstance(package_version("definitely-not-installed-package-name"), str)


def test_runtime_summary_contains_core_fields() -> None:
    summary = runtime_summary()
    assert "python=" in summary
    assert "rembg=" in summary
    assert "onnxruntime=" in summary
    assert "pillow=" in summary
