from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from http import HTTPStatus
from unittest import mock

import pytest

from converter.client import ExchangeClientHTTPBase


@dataclass
class AioHTTPResponseMock:
    status: int
    data: dict = field(default_factory=dict)

    async def json(self):
        return self.data


class ExchangeClientMock(ExchangeClientHTTPBase):
    def _make_get_rate_request(self, *args, **kwargs):
        pass

    def _make_get_all_rates_request(self, *args, **kwargs):
        pass

    def _process_rate_data(self, *args, **kwargs):
        pass

    def _process_all_rates_data(self, *args, **kwargs):
        pass


def mock_make_request(response):
    @asynccontextmanager
    async def mock_make_get_rate_request(*args, **kwargs):
        yield response

    return mock_make_get_rate_request()


@pytest.fixture
def exchange_client():
    return ExchangeClientMock()


@pytest.mark.asyncio
async def test_get_direct_rate_returns_rate(exchange_client: ExchangeClientHTTPBase, exchange_rate_factory):
    # Arrange
    rate = exchange_rate_factory.build()
    response = AioHTTPResponseMock(status=HTTPStatus.OK)
    exchange_client._make_get_rate_request = mock.Mock(return_value=mock_make_request(response))
    exchange_client._process_rate_data = mock.Mock(return_value=rate)
    # Act
    result = await exchange_client.get_direct_rate(rate.currency_from, rate.currency_to)
    # Assert
    assert result == rate


@pytest.mark.asyncio
async def test_get_direct_rate_retries_if_not_found(exchange_client: ExchangeClientHTTPBase, exchange_rate_factory):
    # Arrange
    rate = exchange_rate_factory.build()
    first_response = AioHTTPResponseMock(status=HTTPStatus.BAD_REQUEST)
    second_response = AioHTTPResponseMock(status=HTTPStatus.OK)
    exchange_client._make_get_rate_request = mock.Mock(
        side_effect=[mock_make_request(first_response), mock_make_request(second_response)]
    )
    exchange_client._process_rate_data = mock.Mock(return_value=rate)
    # Act
    await exchange_client.get_direct_rate(rate.currency_from, rate.currency_to)
    # Assert
    assert exchange_client._make_get_rate_request.call_count == 2
