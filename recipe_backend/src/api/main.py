from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.core.config import get_settings
from src.api.routes import auth, favorites, recipes

openapi_tags = [
    {
        "name": "meta",
        "description": "Service metadata and health checks.",
    },
    {
        "name": "auth",
        "description": "User registration, login, and identity.",
    },
    {
        "name": "recipes",
        "description": "Browse, search, and fetch recipe details.",
    },
    {
        "name": "favorites",
        "description": "CRUD for user favorites (requires Bearer JWT).",
    },
]

settings = get_settings()

app = FastAPI(
    title="Recipe Finder & Saver API",
    description=(
        "Backend API for the Recipe Finder & Saver app.\n\n"
        "Auth: Use `Authorization: Bearer <token>` for endpoints requiring authentication."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# CORS for the React frontend. Configure via CORS_ALLOW_ORIGINS env var.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(recipes.router)
app.include_router(favorites.router)


@app.get("/", tags=["meta"], summary="Health check", operation_id="health_check")
def health_check():
    """Health check endpoint.

    Returns:
        A simple JSON payload indicating the service is running.
    """
    return {"message": "Healthy"}
