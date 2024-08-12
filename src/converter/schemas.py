from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_serializer, field_validator

from converter.constants import DECIMAL_ROUND_PREC
from converter.models import Exchange


class ConvertRequestSchema(BaseModel):
    currency_from: str
    currency_to: str
    exchange: Exchange | None
    amount: Decimal
    cache_max_seconds: int | None = None


class ConvertResponseSchema(BaseModel):
    currency_from: str
    currency_to: str
    exchange: Exchange
    rate: Decimal
    result: Decimal
    updated_at: datetime

    @field_validator("rate", "result")
    def round_decimal(cls, d: Decimal) -> Decimal:
        return round(d, DECIMAL_ROUND_PREC)

    @field_serializer("updated_at")
    def serialize_dt(self, dt: datetime, _info) -> int:
        return int(dt.timestamp())
