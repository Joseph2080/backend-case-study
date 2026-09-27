import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text

from src.career_details.router import router as career_details_router
from src.cv.router import router as cv_router
from src.db.service import DatabaseService

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import all models to register them with SQLModel
    import src.db.models  # noqa: F401

    db = DatabaseService()
    try:
        await db.create_db_and_tables()
        yield
    finally:
        await db.engine.dispose()


class HealthResponse(BaseModel):
    status: str


app = FastAPI(title="CV workspace", lifespan=lifespan)
app.include_router(cv_router)
app.include_router(career_details_router)


@app.get("/ping", tags=["health"])
async def ping() -> HealthResponse:
    async with await DatabaseService().get_session() as session:
        await session.execute(text("SELECT 1"))
    return HealthResponse(status="ok")


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
