from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .redis import redis_client
from .routers import auth, diary, items, library, reviews, search, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.ping()
    yield
    await redis_client.aclose()

app = FastAPI(title="Trackify API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(search.router)
app.include_router(items.router)
app.include_router(library.router)
app.include_router(diary.router)
app.include_router(reviews.router)

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}