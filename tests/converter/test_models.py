from decimal import Decimal

import pytest

from converter.models import Conversion, Exchange
from tests.converter.factories import ExchangeRateFactory


def test_reversed_rate_generated_correctly(exchange_rate_factory: ExchangeRateFactory):
    # Arrange
    exchange_rate = exchange_rate_factory.build(rate=Decimal("2.5"))
    # Act
    reversed_rate = exchange_rate.reversed
    # Assert
    assert reversed_rate.currency_to == exchange_rate.currency_from
    assert reversed_rate.currency_from == exchange_rate.currency_to
    assert reversed_rate.rate == Decimal("0.4")


def test_merge_cant_be_done_when_exchanges_are_different(exchange_rate_factory: ExchangeRateFactory):
    # Arrange
    binance_rate = exchange_rate_factory.build(exchange=Exchange.BINANCE)
    kucoin_rate = exchange_rate_factory.build(currency_from=binance_rate.currency_to, exchange=Exchange.KUCOIN)
    # Act & Assert
    with pytest.raises(ValueError):
        binance_rate.merge(kucoin_rate)


def test_merge_cant_be_done_when_they_are_not_related(exchange_rate_factory: ExchangeRateFactory):
    # Arrange
    to_btc_rate = exchange_rate_factory.build(exchange=Exchange.BINANCE, currency_to="BTC")
    from_eth_rate = exchange_rate_factory.build(exchange=Exchange.BINANCE, currency_from="ETH")
    # Act & Assert
    with pytest.raises(ValueError):
        to_btc_rate.merge(from_eth_rate)


def test_merge_returns_correct_rate(exchange_rate_factory: ExchangeRateFactory):
    # Arrange
    to_btc_rate = exchange_rate_factory.build(exchange=Exchange.BINANCE, currency_to="BTC", rate=Decimal("0.01"))
    from_btc_rate = exchange_rate_factory.build(exchange=Exchange.BINANCE, currency_from="BTC", rate=Decimal("1000"))
    # Act
    merged_rate = to_btc_rate.merge(from_btc_rate)
    # Assert
    assert merged_rate.currency_from == to_btc_rate.currency_from
    assert merged_rate.currency_to == from_btc_rate.currency_to
    assert merged_rate.rate == Decimal("10")
    assert merged_rate._intermediate == ["BTC"]


def test_exchange_rate_converts_correctly(exchange_rate_factory: ExchangeRateFactory):
    # Arrange
    rate = exchange_rate_factory.build(rate=Decimal("5"))
    amount = Decimal("10")
    # Act
    result = rate.convert(amount)
    # Assert
    assert result == Decimal("50")


def test_convertion_generated_correctly(exchange_rate_factory: ExchangeRateFactory):
    # Arrange
    rate = exchange_rate_factory.build(rate=Decimal("5"))
    amount = Decimal("10")
    # Act
    conversion = Conversion.convert(amount, rate)
    # Arrange
    assert conversion.currency_from == rate.currency_from
    assert conversion.currency_to == rate.currency_to
    assert conversion.exchange == rate.exchange
    assert conversion.rate == rate.rate
    assert conversion.updated_at == rate.updated_at
    assert conversion.amount == amount
    assert conversion.result == Decimal("50")
