"""API-level tests: address validation, error hygiene, endpoint contract."""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import app as app_module
from app import app, sanitize_address

client = TestClient(app)

VALID = "0x" + "1" * 40


class TestSanitizeAddress:
    def test_accepts_valid_address(self):
        assert sanitize_address(VALID) == VALID

    def test_strips_whitespace(self):
        assert sanitize_address(f"  {VALID}  ") == VALID

    def test_accepts_cmc_placeholder(self):
        assert sanitize_address("cmc_1234") == "cmc_1234"

    def test_rejects_42_char_non_hex(self):
        with pytest.raises(HTTPException) as exc:
            sanitize_address("0x" + "z" * 40)
        assert exc.value.status_code == 400

    def test_rejects_wrong_length_hexish_garbage(self):
        with pytest.raises(HTTPException) as exc:
            sanitize_address("0x1234")
        assert exc.value.status_code == 400

    def test_rejects_long_garbage(self):
        with pytest.raises(HTTPException) as exc:
            sanitize_address("definitely-not-an-address-or-a-ticker")
        assert exc.value.status_code == 400

    def test_rejects_empty(self):
        with pytest.raises(HTTPException) as exc:
            sanitize_address("")
        assert exc.value.status_code == 400


class TestEndpoints:
    def test_root_names_the_right_service(self):
        body = client.get("/").json()
        assert body["service"] == "token-sentry"

    def test_status_endpoint(self):
        response = client.get("/health/status")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_endpoint_is_implemented(self, monkeypatch):
        """POST /health must run an analysis, not return 501."""
        called = {}

        def fake_analyze(request, include_llm=False, github_repo=None):
            called["contract"] = request.contract
            raise HTTPException(status_code=503, detail="stubbed")

        monkeypatch.setattr(app_module, "run_comprehensive_analysis", fake_analyze, raising=False)
        response = client.post("/health", json={"contract": VALID})
        assert response.status_code != 501
        assert called["contract"] == VALID

    def test_invalid_address_returns_400_not_500(self):
        response = client.post("/health/comprehensive", json={"contract": "0x1234"})
        assert response.status_code == 400

    def test_analysis_error_does_not_leak_exception_detail(self, monkeypatch):
        class ExplodingPipeline:
            @classmethod
            def from_env(cls):
                return cls()

            def analyze_token(self, *args, **kwargs):
                raise ValueError("secret-internal-detail sk-abc123")

        monkeypatch.setattr(app_module, "TokenHealthPipeline", ExplodingPipeline)
        response = client.post("/health/comprehensive", json={"contract": VALID})
        assert response.status_code == 500
        assert "secret-internal-detail" not in response.text


class TestCorsConfig:
    def test_no_wildcard_origin_with_credentials(self):
        """allow_origins=['*'] with allow_credentials=True is invalid and unsafe."""
        cors = next(
            m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"
        )
        allows_all = "*" in cors.kwargs.get("allow_origins", [])
        credentials = cors.kwargs.get("allow_credentials", False)
        assert not (allows_all and credentials)
