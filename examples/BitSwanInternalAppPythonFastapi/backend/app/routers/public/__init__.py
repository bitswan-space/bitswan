"""Public (unauthenticated) API routes.

Read-only endpoints that require no authentication.
"""

from fastapi import APIRouter

router = APIRouter()

# Import sub-modules so their routes are registered on the router.
from app.routers.public import root, gallery  # noqa: E402, F401
