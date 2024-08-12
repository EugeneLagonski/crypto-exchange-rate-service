from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
from typing import ClassVar

from aiohttp.client import _RequestContextManager, ClientError, ClientSession

from converter.errors import ExchangeIsNotAvailable, ExchangeNotFound
from converter.models import Exchange, ExchangeRate


class ExchangeClient(ABC):
    @abstractmethod
    async def get_direct_rate(self, currency_from: str, currency_to: str, **kwargs) -> ExchangeRate:
        pass

    @abstractmethod
    async def get_non_direct_rate(self, currency_from: str, currency_to: str) -> ExchangeRate:
        pass


class ExchangeClientHTTPBase(ExchangeClient):
    name: ClassVar[Exchange]

    async def get_direct_rate(self, currency_from: str, currency_to: str, **kwargs) -> ExchangeRate:
        reversed_rate = kwargs.get("reversed_rate")
        try:
            async with self._make_get_rate_request(currency_from, currency_to) as response:
                if response.status == HTTPStatus.BAD_REQUEST:
                    raise ExchangeNotFound()
                if response.status != HTTPStatus.OK:
                    raise ExchangeIsNotAvailable()
                data = await response.json()
                rate = self._process_rate_data(data, currency_from, currency_to)
                return rate.reversed if reversed_rate else rate
        except ExchangeNotFound:
            if reversed_rate:
                raise
            return await self.get_direct_rate(currency_to, currency_from, reversed_rate=True)
        except ClientError as exc:
            raise ExchangeIsNotAvailable() from exc

    async def get_non_direct_rate(self, currency_from: str, currency_to: str) -> ExchangeRate:
        related_rates = await self._get_related_rates(currency_from, currency_to)
        from_intermediate_mapping = {
            rate.currency_to: rate for rate in related_rates if rate.currency_from == currency_from
        }
        intermediate_to_mapping = {
            rate.currency_from: rate for rate in related_rates if rate.currency_to == currency_to
        }
        if rate := from_intermediate_mapping.get(currency_to):
            return rate
        possible_intermediate_currencies = set(from_intermediate_mapping) & set(intermediate_to_mapping)
        best_rate = None
        for intermediate_currency in possible_intermediate_currencies:
            to_intermediate_rate = from_intermediate_mapping[intermediate_currency]
            from_intermediate_rate = intermediate_to_mapping[intermediate_currency]
            rate = to_intermediate_rate.merge(from_intermediate_rate)
            if best_rate is None:
                best_rate = rate
            else:
                best_rate = max(best_rate, rate, key=lambda r: r.rate)
        if not best_rate:
            raise ExchangeNotFound()
        return best_rate

    async def _get_related_rates(self, currency_from: str, currency_to: str) -> list[ExchangeRate]:
        """Get all <currency_from> to <any currency> and <any currency> to <currency_to> rates"""
        try:
            async with self._make_get_all_rates_request() as response:
                if response.status != HTTPStatus.OK:
                    raise ExchangeIsNotAvailable()
                data = await response.json()
                rates = self._process_all_rates_data(data, currency_from, currency_to)
                return rates
        except ClientError as exc:
            raise ExchangeIsNotAvailable() from exc

    @abstractmethod
    def _make_get_rate_request(self, currency_from: str, currency_to: str) -> _RequestContextManager:
        pass

    @abstractmethod
    def _process_rate_data(self, data: dict, currency_from: str, currency_to: str) -> ExchangeRate:
        pass

    @abstractmethod
    def _make_get_all_rates_request(self) -> _RequestContextManager:
        pass

    @abstractmethod
    def _process_all_rates_data(self, data: dict, currency_from: str, currency_to: str) -> list[ExchangeRate]:
        pass


@dataclass
class BinanceExchangeClient(ExchangeClientHTTPBase):
    name = Exchange.BINANCE
    session: ClientSession
    BASE_URL = "https://api4.binance.com"

    def _make_get_rate_request(self, currency_from: str, currency_to: str) -> _RequestContextManager:
        return self.session.get(
            f"{self.BASE_URL}/api/v3/ticker/price",
            params={"symbol": f"{currency_from}{currency_to}"},
        )

    def _process_rate_data(self, data: dict, currency_from: str, currency_to: str) -> ExchangeRate:
        return ExchangeRate(
            currency_from=currency_from,
            currency_to=currency_to,
            exchange=self.name,
            rate=Decimal(data["price"]),
            updated_at=datetime.utcnow(),
        )

    def _make_get_all_rates_request(self) -> _RequestContextManager:
        return self.session.get(f"{self.BASE_URL}/api/v3/ticker/price")

    def _process_all_rates_data(self, data: dict, currency_from: str, currency_to: str) -> list[ExchangeRate]:
        rates = []
        for raw_rate in data:
            symbol: str = raw_rate["symbol"]
            if "DOWN" in symbol or "UP" in symbol:  # Breaks calculations
                continue
            if symbol.startswith(currency_from):
                rate = self._process_rate_data(raw_rate, currency_from, symbol.removeprefix(currency_from))
            elif symbol.endswith(currency_from):
                rate = self._process_rate_data(raw_rate, symbol.removesuffix(currency_from), currency_from).reversed
            elif symbol.startswith(currency_to):
                rate = self._process_rate_data(raw_rate, currency_to, symbol.removeprefix(currency_to)).reversed
            else:
                rate = self._process_rate_data(raw_rate, symbol.removesuffix(currency_to), currency_to)
            rates.append(rate)
        return rates


@dataclass
class KuCoinExchangeClient(ExchangeClientHTTPBase):
    name = Exchange.KUCOIN
    session: ClientSession
    BASE_URL = "https://api.kucoin.com"

    def _make_get_rate_request(self, currency_from: str, currency_to: str) -> _RequestContextManager:
        return self.session.get(
            f"{self.BASE_URL}/api/v1/market/orderbook/level1",
            params={"symbol": f"{currency_from}-{currency_to}"},
        )

    def _process_rate_data(self, data: dict, currency_from: str, currency_to: str) -> ExchangeRate:
        if not data.get("data"):
            raise ExchangeNotFound()
        return ExchangeRate(
            currency_from=currency_from,
            currency_to=currency_to,
            exchange=self.name,
            rate=Decimal(data["data"]["price"]),
            updated_at=datetime.utcnow(),
        )

    def _make_get_all_rates_request(self) -> _RequestContextManager:
        return self.session.get(f"{self.BASE_URL}/api/v1/market/allTickers")

    def _process_all_rates_data(self, data: dict, currency_from: str, currency_to: str) -> list[ExchangeRate]:
        rates = []
        for raw_rate in data["data"]["ticker"]:
            rate_from, rate_to = raw_rate["symbol"].split("-")
            if not ({rate_from, rate_to} & {currency_to, currency_from}):
                continue
            rate = ExchangeRate(
                currency_from=rate_from,
                currency_to=rate_to,
                exchange=self.name,
                rate=Decimal(raw_rate["last"]),
                updated_at=datetime.utcnow(),
            )
            if currency_from == rate.currency_to or currency_to == rate.currency_from:
                rate = rate.reversed
            rates.append(rate)
        return rates
