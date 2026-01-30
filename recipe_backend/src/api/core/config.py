from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application configuration loaded from environment variables.

    Notes:
      - Do not hardcode secrets in code; configure via .env in deployment/runtime.
      - Database container exports POSTGRES_URL/USER/PASSWORD/DB/PORT, but we prefer POSTGRES_URL
        if available (it can already include host/port/db).
    """

    postgres_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_exp_minutes: int
    cors_allow_origins: list[str]
    site_url: str | None


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load settings from env vars.

    Required env vars:
      - POSTGRES_URL (preferred) OR (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT)
      - JWT_SECRET_KEY

    Optional env vars:
      - JWT_ALGORITHM (default: HS256)
      - ACCESS_TOKEN_EXP_MINUTES (default: 10080 = 7 days)
      - CORS_ALLOW_ORIGINS (default: "*")
      - SITE_URL (optional; useful for docs and future email redirects)
    """
    postgres_url = os.getenv("POSTGRES_URL", "").strip()

    # Fallback assembly if POSTGRES_URL isn't provided (avoid assuming host value beyond localhost).
    if not postgres_url:
        user = os.getenv("POSTGRES_USER", "").strip()
        password = os.getenv("POSTGRES_PASSWORD", "").strip()
        db = os.getenv("POSTGRES_DB", "").strip()
        port = os.getenv("POSTGRES_PORT", "").strip()
        host = os.getenv("POSTGRES_HOST", "localhost").strip()

        if all([user, password, db, port]):
            postgres_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"

    jwt_secret_key = os.getenv("JWT_SECRET_KEY", "").strip()
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256").strip()
    access_token_exp_minutes = int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "10080"))
    # When allow_credentials=True, browsers reject Access-Control-Allow-Origin="*".
    # So we default to common dev origins rather than "*".
    cors_allow_origins_raw = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).strip()
    site_url = os.getenv("SITE_URL", "").strip() or None

    if cors_allow_origins_raw == "*":
        cors_allow_origins = ["*"]
    else:
        cors_allow_origins = _split_csv(cors_allow_origins_raw)

    # Fail fast for required settings.
    missing = []
    if not postgres_url:
        missing.append("POSTGRES_URL (or POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB/POSTGRES_PORT)")
    if not jwt_secret_key:
        missing.append("JWT_SECRET_KEY")
    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Please configure them in the backend container .env."
        )

    return Settings(
        postgres_url=postgres_url,
        jwt_secret_key=jwt_secret_key,
        jwt_algorithm=jwt_algorithm,
        access_token_exp_minutes=access_token_exp_minutes,
        cors_allow_origins=cors_allow_origins,
        site_url=site_url,
    )
