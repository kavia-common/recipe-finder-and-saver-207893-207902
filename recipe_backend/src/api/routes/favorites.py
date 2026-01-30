from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.core.auth import get_current_user
from src.api.core.db import execute, fetch_all, fetch_one
from src.api.schemas import FavoriteCreateRequest, FavoritesListResponse, FavoriteItem, RecipeSummary

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get(
    "",
    response_model=FavoritesListResponse,
    summary="List favorites",
    description="List the current user's favorite recipes.",
    operation_id="favorites_list",
)
def list_favorites(
    user: dict = Depends(get_current_user),
    limit: int = Query(200, ge=1, le=500, description="Max items to return."),
    offset: int = Query(0, ge=0, description="Offset for pagination."),
) -> FavoritesListResponse:
    """List favorites for the authenticated user."""
    rows = fetch_all(
        """
        SELECT f.created_at, r.id, r.title, r.description, r.image_url, r.tags
        FROM favorites f
        JOIN recipes r ON r.id = f.recipe_id
        WHERE f.user_id = %s
        ORDER BY f.created_at DESC
        LIMIT %s OFFSET %s
        """,
        (user["id"], limit, offset),
    )
    total_row = fetch_one(
        "SELECT COUNT(*)::int AS total FROM favorites WHERE user_id = %s",
        (user["id"],),
    )
    total = int(total_row["total"]) if total_row else 0

    items: list[FavoriteItem] = []
    for r in rows:
        recipe = RecipeSummary(
            id=str(r["id"]),
            title=r["title"],
            description=r.get("description"),
            image_url=r.get("image_url"),
            tags=r.get("tags") or [],
        )
        items.append(FavoriteItem(recipe=recipe, created_at=r.get("created_at")))

    return FavoritesListResponse(items=items, total=total)


@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Add favorite",
    description="Favorite a recipe for the current user.",
    operation_id="favorites_create",
)
def add_favorite(payload: FavoriteCreateRequest, user: dict = Depends(get_current_user)) -> dict:
    """Create a favorite relation for the authenticated user."""
    recipe = fetch_one("SELECT id FROM recipes WHERE id = %s", (payload.recipe_id,))
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Idempotent insert.
    row = fetch_one(
        """
        INSERT INTO favorites (user_id, recipe_id)
        VALUES (%s, %s)
        ON CONFLICT (user_id, recipe_id) DO UPDATE SET created_at = now()
        RETURNING user_id, recipe_id, created_at
        """,
        (user["id"], payload.recipe_id),
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to add favorite")

    return {"favorite": row}


@router.delete(
    "/{recipe_id}",
    response_model=dict,
    summary="Remove favorite",
    description="Remove a recipe from the current user's favorites.",
    operation_id="favorites_delete",
)
def remove_favorite(recipe_id: str, user: dict = Depends(get_current_user)) -> dict:
    """Remove a favorite relation for the authenticated user."""
    affected = execute("DELETE FROM favorites WHERE user_id = %s AND recipe_id = %s", (user["id"], recipe_id))
    if affected == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"message": "Removed"}
