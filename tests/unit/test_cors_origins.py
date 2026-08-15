"""Environment-aware CORS: Vite localhost range in development, explicit list in production."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.config import Settings


def _settings(**env: str) -> Settings:
    data = {
        "JWT_SECRET": "test-secret-for-cors",
        "ENVIRONMENT": "development",
        "CORS_ORIGINS": "http://127.0.0.1:5173,http://localhost:5173",
        **env,
    }
    return Settings(_env_file=None, **{k.lower(): v for k, v in data.items()})


def _cors_client(cfg: Settings) -> TestClient:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origin_list,
        allow_origin_regex=cfg.cors_allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/game/start")
    def start():
        return {"status": "started"}

    return TestClient(app)


def _preflight(client: TestClient, origin: str, method: str = "GET", path: str = "/health"):
    return client.options(
        path,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "content-type",
        },
    )


def test_development_allows_vite_5173():
    cfg = _settings()
    assert cfg.is_cors_origin_allowed("http://localhost:5173")
    assert cfg.is_cors_origin_allowed("http://127.0.0.1:5173")


def test_development_allows_vite_5174():
    cfg = _settings()
    assert cfg.is_cors_origin_allowed("http://localhost:5174")
    assert cfg.is_cors_origin_allowed("http://127.0.0.1:5174")


def test_development_allows_vite_5175():
    cfg = _settings()
    assert cfg.is_cors_origin_allowed("http://localhost:5175")
    assert cfg.is_cors_origin_allowed("http://127.0.0.1:5175")


def test_development_allows_another_vite_fallback_port():
    cfg = _settings()
    assert cfg.is_cors_origin_allowed("http://localhost:5176")
    assert cfg.is_cors_origin_allowed("http://localhost:5199")
    assert cfg.is_cors_origin_allowed("http://127.0.0.1:5188")


def test_development_rejects_unrelated_external_origin():
    cfg = _settings()
    assert not cfg.is_cors_origin_allowed("https://evil.example")
    assert not cfg.is_cors_origin_allowed("http://attacker.test:5175")
    assert not cfg.is_cors_origin_allowed("http://localhost:3000")
    assert not cfg.is_cors_origin_allowed("http://localhost:80")
    assert "*" not in cfg.cors_origin_list


def test_production_does_not_auto_allow_localhost():
    cfg = _settings(
        ENVIRONMENT="production",
        CORS_ORIGINS="https://mindguess.example",
    )
    assert cfg.cors_allow_origin_regex is None
    assert not cfg.is_cors_origin_allowed("http://localhost:5173")
    assert not cfg.is_cors_origin_allowed("http://localhost:5175")
    assert not cfg.is_cors_origin_allowed("http://127.0.0.1:5174")


def test_production_explicit_cors_origins_still_work():
    cfg = _settings(
        ENVIRONMENT="production",
        CORS_ORIGINS="https://mindguess.example,https://www.mindguess.example",
    )
    assert cfg.cors_origin_list == [
        "https://mindguess.example",
        "https://www.mindguess.example",
    ]
    assert cfg.is_cors_origin_allowed("https://mindguess.example")
    assert cfg.is_cors_origin_allowed("https://www.mindguess.example")
    assert not cfg.is_cors_origin_allowed("https://other.example")


def test_never_expands_wildcard_even_if_configured():
    cfg = _settings(CORS_ORIGINS="*,http://localhost:5173")
    assert "*" not in cfg.cors_origin_list
    assert cfg.is_cors_origin_allowed("http://localhost:5173")


def test_middleware_reflects_vite_fallback_origin_in_development():
    client = _cors_client(_settings())
    for origin in (
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5175",
    ):
        preflight = _preflight(client, origin, method="POST", path="/game/start")
        assert preflight.status_code == 200
        assert preflight.headers.get("access-control-allow-origin") == origin
        assert preflight.headers.get("access-control-allow-credentials") == "true"

        actual = client.post("/game/start", headers={"Origin": origin})
        assert actual.status_code == 200
        assert actual.json()["status"] == "started"
        assert actual.headers.get("access-control-allow-origin") == origin


def test_middleware_blocks_external_origin_in_development():
    client = _cors_client(_settings())
    origin = "https://evil.example"
    preflight = _preflight(client, origin)
    assert preflight.headers.get("access-control-allow-origin") != origin

    actual = client.get("/health", headers={"Origin": origin})
    assert actual.status_code == 200
    assert actual.headers.get("access-control-allow-origin") != origin


def test_middleware_production_blocks_localhost_allows_explicit():
    client = _cors_client(
        _settings(
            ENVIRONMENT="production",
            CORS_ORIGINS="https://mindguess.example",
        )
    )
    local = _preflight(client, "http://localhost:5175")
    assert local.headers.get("access-control-allow-origin") != "http://localhost:5175"

    allowed = _preflight(client, "https://mindguess.example")
    assert allowed.headers.get("access-control-allow-origin") == "https://mindguess.example"
