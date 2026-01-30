from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.api.core.db import fetch_all, fetch_one
from src.api.schemas import RecipeDetail, RecipeListResponse, RecipeSummary

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get(
    "",
    response_model=RecipeListResponse,
    summary="Browse recipes",
    description="List recipes with optional query filter. Supports pagination.",
    operation_id="recipes_list",
)
def list_recipes(
    q: str | None = Query(None, description="Optional search query for title/description."),
    limit: int = Query(50, ge=1, le=200, description="Max items to return."),
    offset: int = Query(0, ge=0, description="Offset for pagination."),
) -> RecipeListResponse:
    """Browse recipes.

    Uses ILIKE match on title/description for q when provided.
    """
    if q:
        like = f"%{q}%"
        items = fetch_all(
            """
            SELECT id, title, description, image_url, tags
            FROM recipes
            WHERE title ILIKE %s OR COALESCE(description,'') ILIKE %s
            ORDER BY updated_at DESC
            LIMIT %s OFFSET %s
            """,
            (like, like, limit, offset),
        )
        total_row = fetch_one(
            """
            SELECT COUNT(*)::int AS total
            FROM recipes
            WHERE title ILIKE %s OR COALESCE(description,'') ILIKE %s
            """,
            (like, like),
        )
    else:
        items = fetch_all(
            """
            SELECT id, title, description, image_url, tags
            FROM recipes
            ORDER BY updated_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        total_row = fetch_one("SELECT COUNT(*)::int AS total FROM recipes")

    total = int(total_row["total"]) if total_row else 0
    return RecipeListResponse(items=[RecipeSummary(**i) for i in items], total=total)


@router.get(
    "/search",
    response_model=RecipeListResponse,
    summary="Search recipes",
    description="Search recipes by query string (q) on title/description.",
    operation_id="recipes_search",
)
def search_recipes(
    q: str = Query(..., min_length=1, description="Search query."),
    limit: int = Query(50, ge=1, le=200, description="Max items to return."),
    offset: int = Query(0, ge=0, description="Offset for pagination."),
) -> RecipeListResponse:
    """Search recipes (alias of browse with required q)."""
    return list_recipes(q=q, limit=limit, offset=offset)


@router.get(
    "/{recipe_id}",
    response_model=RecipeDetail,
    summary="Recipe detail",
    description="Fetch full recipe details by id.",
    operation_id="recipes_detail",
)
def get_recipe(recipe_id: str) -> RecipeDetail:
    """Get recipe detail."""
    row = fetch_one(
        """
        SELECT id, title, description, image_url, source_url, ingredients, instructions, tags
        FROM recipes
        WHERE id = %s
        """,
        (recipe_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # psycopg returns jsonb already decoded as Python object in many setups; keep safe fallback.
    return RecipeDetail(**row)
