from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class Exchange(StrEnum):
    BINANCE = "binance"
    KUCOIN = "kucoin"


@dataclass
class ExchangeRate:
    currency_from: str
    currency_to: str
    exchange: Exchange
    rate: Decimal
    updated_at: datetime = field(compare=False)
    _intermediate: list[str] = field(default_factory=list)  # Used for debug purposes

    def merge(self, other: "ExchangeRate") -> "ExchangeRate":
        if self.exchange != other.exchange:
            raise ValueError("Exchanges must match to merge rates")
        if self.currency_to != other.currency_from:
            raise ValueError("Currencies must match to merge rates")
        return ExchangeRate(
            currency_from=self.currency_from,
            currency_to=other.currency_to,
            exchange=self.exchange,
            rate=self.rate * other.rate,
            updated_at=max(self.updated_at, other.updated_at),
            _intermediate=self._intermediate + [self.currency_to],
        )

    @property
    def reversed(self) -> "ExchangeRate":
        return ExchangeRate(
            currency_from=self.currency_to,
            currency_to=self.currency_from,
            exchange=self.exchange,
            rate=1 / self.rate,
            updated_at=self.updated_at,
            _intermediate=self._intermediate[::-1],
        )

    def convert(self, amount: Decimal) -> Decimal:
        return self.rate * amount


@dataclass
class Conversion:
    currency_from: str
    currency_to: str
    exchange: Exchange
    rate: Decimal
    updated_at: datetime
    amount: Decimal
    result: Decimal

    @staticmethod
    def convert(amount: Decimal, rate: ExchangeRate) -> "Conversion":
        return Conversion(
            currency_from=rate.currency_from,
            currency_to=rate.currency_to,
            exchange=rate.exchange,
            rate=rate.rate,
            updated_at=rate.updated_at,
            amount=amount,
            result=rate.convert(amount),
        )
