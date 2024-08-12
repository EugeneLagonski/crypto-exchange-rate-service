from polyfactory.pytest_plugin import register_fixture

from tests.converter.factories import ExchangeRateFactory

exchange_rate_factory = register_fixture(ExchangeRateFactory)
