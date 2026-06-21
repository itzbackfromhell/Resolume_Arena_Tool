import sysconfig
from importlib import metadata

import pytest
from PIL import Image

from resolume_alpha_tool.core import rembg_runtime


def test_package_version_reports_missing_package() -> None:
    assert rembg_runtime.package_version("definitely-not-installed-package") == "not installed"


def test_runtime_summary_includes_versions(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_version(name: str) -> str:
        if name == "rembg":
            return "2.test"
        if name == "onnxruntime":
            return "1.test"
        if name == "Pillow":
            return "10.test"
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(rembg_runtime.metadata, "version", fake_version)

    summary = rembg_runtime.runtime_summary()

    assert "python=" in summary
    assert "abi=" in summary
    assert "rembg=2.test" in summary
    assert "onnxruntime=1.test" in summary
    assert "pillow=10.test" in summary


def test_free_threaded_detection_uses_python_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sysconfig, "get_config_var", lambda name: 1 if name == "Py_GIL_DISABLED" else None)

    assert rembg_runtime.is_free_threaded_python() is True
    assert "free-threaded" in rembg_runtime.python_abi_note()


def test_free_threaded_detection_treats_zero_string_as_standard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sysconfig,
        "get_config_var",
        lambda name: "0" if name == "Py_GIL_DISABLED" else None,
    )

    assert rembg_runtime.is_free_threaded_python() is False
    assert rembg_runtime.python_abi_note() == "standard CPython ABI"


def test_import_rembg_symbols_blocks_free_threaded_python(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rembg_runtime, "is_free_threaded_python", lambda: True)

    with pytest.raises(rembg_runtime.DependencyMissingError) as exc_info:
        rembg_runtime.import_rembg_symbols()

    assert "free-threaded" in str(exc_info.value)
    assert "standard CPython" in str(exc_info.value)


def test_rembg_healthcheck_runs_probe_removal(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    def fake_remove(image: Image.Image, *, session: object) -> Image.Image:
        calls["session"] = session
        output = image.convert("RGBA")
        output.putpixel((0, 0), (0, 0, 0, 0))
        return output

    monkeypatch.setattr(rembg_runtime, "create_rembg_session", lambda model: f"session:{model}")
    monkeypatch.setattr(rembg_runtime, "import_rembg_symbols", lambda: (object, fake_remove))

    result = rembg_runtime.rembg_healthcheck("u2net-test")

    assert calls["session"] == "session:u2net-test"
    assert "test removal completed" in result


def test_rembg_healthcheck_rejects_non_image_probe_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rembg_runtime, "create_rembg_session", lambda _model: object())
    monkeypatch.setattr(
        rembg_runtime,
        "import_rembg_symbols",
        lambda: (object, lambda *_args, **_kwargs: b"nope"),
    )

    with pytest.raises(rembg_runtime.ProcessingError, match="unexpected output type"):
        rembg_runtime.rembg_healthcheck()
