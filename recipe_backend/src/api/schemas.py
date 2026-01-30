from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class MessageResponse(BaseModel):
    message: str = Field(..., description="Human-readable message.")


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email (unique).")
    password: str = Field(..., min_length=6, description="User password (min 6 chars).")
    display_name: str | None = Field(None, description="Optional display name.")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email.")
    password: str = Field(..., description="User password.")


class AuthUser(BaseModel):
    id: str = Field(..., description="User UUID.")
    email: EmailStr = Field(..., description="User email.")
    display_name: str | None = Field(None, description="User display name.")
    created_at: datetime | None = Field(None, description="Account creation timestamp.")


class AuthResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token.")
    token_type: str = Field("bearer", description="Token type (bearer).")
    user: AuthUser = Field(..., description="Authenticated user profile.")


class RecipeSummary(BaseModel):
    id: str = Field(..., description="Recipe UUID.")
    title: str = Field(..., description="Recipe title.")
    description: str | None = Field(None, description="Short description.")
    image_url: str | None = Field(None, description="Image URL.")
    tags: list[str] = Field(default_factory=list, description="Recipe tags.")


class RecipeDetail(RecipeSummary):
    source_url: str | None = Field(None, description="Original source URL.")
    ingredients: list[Any] = Field(default_factory=list, description="Ingredients (JSON array).")
    instructions: list[Any] = Field(default_factory=list, description="Instructions (JSON array).")


class RecipeListResponse(BaseModel):
    items: list[RecipeSummary] = Field(..., description="Recipe list.")
    total: int = Field(..., description="Total matched recipes.")


class FavoriteCreateRequest(BaseModel):
    recipe_id: str = Field(..., description="Recipe UUID to favorite.")


class FavoriteItem(BaseModel):
    recipe: RecipeSummary = Field(..., description="Favorited recipe summary.")
    created_at: datetime | None = Field(None, description="When the recipe was favorited.")


class FavoritesListResponse(BaseModel):
    items: list[FavoriteItem] = Field(..., description="Favorite recipes.")
    total: int = Field(..., description="Total favorites.")
