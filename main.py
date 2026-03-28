import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from starlette.middleware.cors import CORSMiddleware

from conf.db_conf import engine
from conf.settings import settings
from routers import router
from utils.cache import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()
    # redis-py 5.x recommends aclose(); keep compatibility with older versions.
    close = getattr(redis_client, "aclose", None)
    if close is not None:
        await close()
    else:
        await redis_client.close()


app = FastAPI(lifespan=lifespan)


cors_origins = [item.strip() for item in settings.cors_origins.split(",") if item.strip()]
cors_options = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

if cors_origins:
    cors_options["allow_origins"] = cors_origins
else:
    # Local Vue/Vite development usually runs on a random localhost port.
    cors_options["allow_origin_regex"] = r"https?://(localhost|127\.0\.0\.1)(:\d+)?$"

app.add_middleware(CORSMiddleware, **cors_options)


app.include_router(router.api_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


if __name__ == '__main__':
    uvicorn.run("main:app",port=8000,reload=True)
