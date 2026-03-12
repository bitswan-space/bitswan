from starlette.requests import Request

from app.auth import get_username_from_request
from app.routers.internal import router


@router.get("/")
async def root(request: Request):
    return {"message": "Hello from FastAPI!", "user": get_username_from_request(request)}
