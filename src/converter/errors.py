from http import HTTPStatus

from aiohttp import web

from common import ErrorHandlerRegistry


class ExchangeError(Exception):
    pass


class ExchangeNotFound(ExchangeError):
    def __init__(self) -> None:
        super().__init__("Exchange not found")


class ExchangeIsNotAvailable(ExchangeError):
    def __init__(self) -> None:
        super().__init__("Exchanges are not available")


async def handle_exchange_not_found(exception: ExchangeNotFound) -> web.Response:
    return web.Response(text=str(exception), status=HTTPStatus.NOT_FOUND)


async def handle_exchange_is_not_available(exception: ExchangeIsNotAvailable) -> web.Response:
    return web.Response(text=str(exception), status=HTTPStatus.BAD_GATEWAY)


def register_exchange_errors(registry: ErrorHandlerRegistry) -> None:
    registry.add_handler(ExchangeNotFound, handle_exchange_not_found)  # type: ignore
    registry.add_handler(ExchangeIsNotAvailable, handle_exchange_is_not_available)  # type: ignore
