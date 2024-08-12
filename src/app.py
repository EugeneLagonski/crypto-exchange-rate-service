from aiohttp import client, web
from pydantic import ValidationError
from redis.asyncio import Redis

from common import (
    error_handling_middleware,
    ErrorHandlerRegistry,
    pydantic_error_handler,
)
from converter.cache import ExchangeClientCacheProxy, ExchangeRateCache, RedisSettings
from converter.client import BinanceExchangeClient, KuCoinExchangeClient
from converter.errors import register_exchange_errors
from converter.models import Exchange
from converter.routes import convert_app
from converter.service import ConvertService


async def on_startup(app: web.Application) -> None:
    app["http_session"] = http_session = client.ClientSession()
    redis_settings = RedisSettings()  # type: ignore
    app["redis"] = redis = Redis(
        host=redis_settings.host,
        port=redis_settings.port,
        password=redis_settings.password,
        decode_responses=True,
    )
    exchange_rate_cache = ExchangeRateCache(redis, redis_settings.ttl)
    app["convert_service"] = ConvertService(
        {
            Exchange.BINANCE: ExchangeClientCacheProxy(BinanceExchangeClient(http_session), exchange_rate_cache),
            Exchange.KUCOIN: ExchangeClientCacheProxy(KuCoinExchangeClient(http_session), exchange_rate_cache),
        }
    )


async def on_cleanup(app: web.Application) -> None:
    await app["http_session"].close()
    await app["redis"].aclose()


async def create_app() -> web.Application:
    error_handler_registry = ErrorHandlerRegistry()
    error_handler_registry.add_handler(ValidationError, pydantic_error_handler)  # type: ignore
    register_exchange_errors(error_handler_registry)
    app = web.Application(middlewares=[error_handling_middleware])
    app["error_handler_registry"] = error_handler_registry
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.add_subapp("/api/v1/convert", convert_app)
    return app


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    web.run_app(create_app())
