from fastapi import FastAPI
from contextlib import asynccontextmanager
from conf.db_conf import engine
from routers import router
from utils.cache import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()
    await redis_client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(router.api_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
