import pickle

import aiohttp
import pydantic
from aioredis import from_url
from fastapi import APIRouter, FastAPI, Query, Request


class Settings(pydantic.BaseSettings):
    DEFAULT_QUERY: str = "USDT"
    API_URL: str = "https://api.coincap.io/v2/assets?search={name}"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    DEBUG: bool = False
    REDIS_TTL: int = 600

    URI: str = "/api"

    @property
    def redis_url(self):
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()
router = APIRouter()


async def perform_query(name):
    async with aiohttp.ClientSession() as session:
        async with session.get(settings.API_URL.format(name=name)) as resp:
            return await resp.json()


async def cached_result(name, *, redis):
    cached_result = await redis.get(name)
    if cached_result:
        return pickle.loads(cached_result)

    response = await perform_query(name)

    await redis.set(name, pickle.dumps(response), ex=settings.REDIS_TTL)

    return response


@router.get(settings.URI)
async def index(name: str = Query(default=settings.DEFAULT_QUERY), *, request: Request):
    return await cached_result(name.lower(), redis=request.app.state.redis)


routers = [
    router,
]


def get_webapp():
    app = FastAPI(name=__name__)
    list(map(app.include_router, routers))
    app.state.redis = redis = from_url(settings.redis_url)

    @app.on_event("startup")
    async def startup():
        await redis.ping()

    return app


if __name__ == "__main__":
    import uvicorn

    app = get_webapp()
    uvicorn.run(
        "main:get_webapp", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )
