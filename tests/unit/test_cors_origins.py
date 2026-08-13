"""CORS origin expansion for local Vite ports."""

from app.config import Settings


def test_development_cors_includes_vite_bump_ports(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret-for-cors")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    )
    cfg = Settings(_env_file=None)
    origins = cfg.cors_origin_list
    assert "http://localhost:5173" in origins
    assert "http://localhost:5175" in origins
    assert "http://127.0.0.1:5175" in origins
    assert "*" not in origins


def test_production_cors_stays_explicit(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret-for-cors")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://mindguess.example",
    )
    cfg = Settings(_env_file=None)
    origins = cfg.cors_origin_list
    assert origins == ["https://mindguess.example"]
    assert "http://localhost:5175" not in origins
