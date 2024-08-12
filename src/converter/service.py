from dataclasses import dataclass
from decimal import Decimal

from common import ApplicationError
from converter.client import ExchangeClient
from converter.errors import ExchangeError, ExchangeIsNotAvailable, ExchangeNotFound
from converter.models import Conversion, Exchange, ExchangeRate


@dataclass
class ConvertService:
    exchange_clients: dict[Exchange, ExchangeClient]

    async def convert(
        self,
        convert_from: str,
        convert_to: str,
        exchange: Exchange | None,
        amount: Decimal,
        cache_max_seconds: int | None,
    ) -> Conversion:
        exchanges = [exchange] if exchange else list(Exchange)

        rate, errors = await self._get_direct_rate(exchanges, convert_from, convert_to, cache_max_seconds)
        if not rate:
            rate, errors = await self._get_non_direct_rate(exchanges, convert_from, convert_to)
        if not rate:
            self._handle_errors(errors)
            return  # type: ignore # Unreachable
        return Conversion.convert(amount, rate)

    async def _get_direct_rate(
        self,
        exchanges: list[Exchange],
        convert_from: str,
        convert_to: str,
        cache_max_seconds: int | None,
    ) -> tuple[ExchangeRate | None, list[Exception]]:
        rate = None
        errors: list[Exception] = []
        for exchange in exchanges:
            client = self.exchange_clients[exchange]
            try:
                rate = await client.get_direct_rate(convert_from, convert_to, cache_max_seconds=cache_max_seconds)
            except ExchangeError as exc:
                errors.append(exc)
            if rate:
                break
        return rate, errors

    async def _get_non_direct_rate(
        self,
        exchanges: list[Exchange],
        convert_from: str,
        convert_to: str,
    ) -> tuple[ExchangeRate | None, list[Exception]]:
        rate = None
        errors: list[Exception] = []
        for exchange in exchanges:
            client = self.exchange_clients[exchange]
            try:
                rate = await client.get_non_direct_rate(convert_from, convert_to)
            except ExchangeError as exc:
                errors.append(exc)
            if rate:
                break
        return rate, errors

    @staticmethod
    def _handle_errors(errors: list[Exception]) -> None:
        if not errors:
            raise ApplicationError()  # Don't have errors and rate at the same time. Should be unreachable.
        if len(errors) == 1:
            raise errors[0]
        if all(isinstance(e, ExchangeNotFound) for e in errors):
            raise ExchangeNotFound() from ExceptionGroup("Exchange not found", errors)
        if all(isinstance(e, ExchangeError) for e in errors):
            raise ExchangeIsNotAvailable() from ExceptionGroup("Exchange are not available", errors)
        raise ApplicationError() from ExceptionGroup("Conversion unexpected errors", errors)
