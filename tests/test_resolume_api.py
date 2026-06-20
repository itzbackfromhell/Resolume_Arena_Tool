import pytest
import requests

from resolume_alpha_tool.core.exceptions import ResolumeApiError
from resolume_alpha_tool.core.models import ResolumeConfig
from resolume_alpha_tool.core.resolume_api import ResolumeClient, _response_payload


class DummyResponse:
    def __init__(self, text: str, content_type: str = "text/plain") -> None:
        self.text = text
        self.headers = {"content-type": content_type}

    def raise_for_status(self) -> None:
        return None

    def json(self):  # type: ignore[no-untyped-def]
        raise ValueError("bad json")


def test_response_payload_returns_text_for_non_json_response() -> None:
    assert _response_payload(DummyResponse("ok")) == "ok"  # type: ignore[arg-type]


def test_response_payload_reports_invalid_json() -> None:
    with pytest.raises(ResolumeApiError):
        _response_payload(DummyResponse("not-json", "application/json"))  # type: ignore[arg-type]


def test_resolume_client_normalizes_paths() -> None:
    client = ResolumeClient(ResolumeConfig(host="127.0.0.1", port=8080, timeout_seconds=1.0))

    assert client._url("api/v1/product") == "http://127.0.0.1:8080/api/v1/product"
    assert client._url("/api/v1/product") == "http://127.0.0.1:8080/api/v1/product"


def test_resolume_client_wraps_request_errors(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def boom(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise requests.RequestException("connection refused")

    monkeypatch.setattr(requests, "get", boom)

    with pytest.raises(ResolumeApiError):
        ResolumeClient().get("/api/v1/product")
