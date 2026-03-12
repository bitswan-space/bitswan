"""Internal (authenticated) API routes.

All endpoints in this package are automatically protected by Keycloak JWT
validation. The validated claims are available via ``request.state.claims``.
"""

from fastapi import APIRouter, Depends

from app.auth import require_auth

router = APIRouter(dependencies=[Depends(require_auth)])

# Import sub-modules so their routes are registered on the router.
from app.routers.internal import root, count, gallery  # noqa: E402, F401
