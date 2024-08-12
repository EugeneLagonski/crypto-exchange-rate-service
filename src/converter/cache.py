import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio import Redis

from converter.client import ExchangeClient, ExchangeClientHTTPBase
from converter.models import Exchange, ExchangeRate


class RedisSettings(BaseSettings):
    host: str
    port: int
    password: str | None = None
    ttl: int

    model_config = SettingsConfigDict(env_prefix="redis_")


@dataclass
class ExchangeRateCache:
    redis: Redis
    ttl: int

    async def set(self, rate: ExchangeRate) -> None:
        key = self.generate_key(rate.currency_from, rate.currency_to, rate.exchange)
        raw_rate = asdict(rate)
        raw_rate["updated_at"] = int(raw_rate["updated_at"].timestamp())
        raw_rate["rate"] = str(raw_rate["rate"])
        await self.redis.set(key, json.dumps(raw_rate), ex=self.ttl)

    async def get(self, currency_from: str, currency_to: str, exchange: Exchange) -> ExchangeRate | None:
        key = self.generate_key(currency_from, currency_to, exchange)
        raw_rate = await self.redis.get(key)
        if not raw_rate:
            return None
        raw_rate = json.loads(raw_rate)
        raw_rate["updated_at"] = datetime.fromtimestamp(raw_rate["updated_at"])
        raw_rate["rate"] = Decimal(raw_rate["rate"])
        return ExchangeRate(**raw_rate)

    @staticmethod
    def generate_key(currency_from: str, currency_to: str, exchange: Exchange) -> str:
        return f"{currency_from}:{currency_to}:{exchange}"


@dataclass
class ExchangeClientCacheProxy(ExchangeClient):
    client: ExchangeClientHTTPBase
    cache: ExchangeRateCache

    async def get_direct_rate(self, currency_from: str, currency_to: str, **kwargs) -> ExchangeRate:
        cache_max_seconds = kwargs.get("cache_max_seconds")
        if cache_max_seconds:
            rate = await self.cache.get(currency_from, currency_to, self.client.name)
            if rate and rate.updated_at + timedelta(seconds=cache_max_seconds) >= datetime.utcnow():
                return rate
        rate = await self.client.get_direct_rate(currency_from, currency_to)
        await self.cache.set(rate)
        return rate

    async def get_non_direct_rate(self, currency_from: str, currency_to: str) -> ExchangeRate:
        rate = await self.client.get_non_direct_rate(currency_from, currency_to)
        await self.cache.set(rate)
        return rate
