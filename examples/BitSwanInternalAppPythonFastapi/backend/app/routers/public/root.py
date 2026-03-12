from app.routers.public import router


@router.get("/")
async def root():
    return {"message": "Hello from the public API!"}
