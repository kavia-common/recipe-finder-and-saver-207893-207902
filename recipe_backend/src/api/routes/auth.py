from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.core.auth import (
    create_access_token_for_user_id,
    get_current_user,
    hash_password,
    verify_password,
)
from src.api.core.db import fetch_one
from src.api.schemas import AuthResponse, LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account using email + password and return an access token.",
    operation_id="auth_register",
)
def register(payload: RegisterRequest) -> AuthResponse:
    """Register endpoint.

    Args:
        payload: RegisterRequest containing email/password/display_name.

    Returns:
        AuthResponse with access token and created user profile.
    """
    existing = fetch_one("SELECT id FROM users WHERE email = %s", (str(payload.email).lower(),))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    pw_hash = hash_password(payload.password)
    row = fetch_one(
        """
        INSERT INTO users (email, password_hash, display_name)
        VALUES (%s, %s, %s)
        RETURNING id, email, display_name, created_at
        """,
        (str(payload.email).lower(), pw_hash, payload.display_name),
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create user")

    token = create_access_token_for_user_id(str(row["id"]))
    return AuthResponse(access_token=token, user=row)  # pydantic will coerce


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login",
    description="Authenticate using email + password and return a JWT access token.",
    operation_id="auth_login",
)
def login(payload: LoginRequest) -> AuthResponse:
    """Login endpoint.

    Args:
        payload: LoginRequest containing email/password.

    Returns:
        AuthResponse with access token and user profile.
    """
    user = fetch_one(
        "SELECT id, email, display_name, password_hash, created_at FROM users WHERE email = %s",
        (str(payload.email).lower(),),
    )
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token_for_user_id(str(user["id"]))
    # Remove sensitive field before returning
    user.pop("password_hash", None)
    return AuthResponse(access_token=token, user=user)


@router.get(
    "/me",
    response_model=dict,
    summary="Get current user",
    description="Return the currently authenticated user profile.",
    operation_id="auth_me",
)
def me(user: dict = Depends(get_current_user)) -> dict:
    """Get current user profile."""
    return {"user": user}


@router.post(
    "/logout",
    response_model=dict,
    summary="Logout (client-side)",
    description="JWTs are stateless; the client should delete its token to log out.",
    operation_id="auth_logout",
)
def logout() -> dict:
    """Logout endpoint (stateless).

    This is provided for frontend convenience. No server-side session is stored.
    """
    return {"message": "Logged out"}
