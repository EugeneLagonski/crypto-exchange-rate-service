from polyfactory.factories import DataclassFactory

from converter.models import ExchangeRate


class ExchangeRateFactory(DataclassFactory[ExchangeRate]):
    @classmethod
    def currency_from(cls) -> str:
        return cls.__faker__.cryptocurrency_code()

    @classmethod
    def currency_to(cls) -> str:
        return cls.__faker__.cryptocurrency_code()
