from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Awaitable, Callable

from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web_request import Request
from pydantic import ValidationError


class ApplicationError(Exception):
    """Code error. If ApplicationError is raised there is a bug in the code."""


ErrorHandler = Callable[[Exception], Awaitable[web.StreamResponse]]


@dataclass
class ErrorHandlerRegistry:
    registry: dict[type[Exception], ErrorHandler] = field(default_factory=dict)

    def add_handler(
        self,
        exc_type: type[Exception],
        handler: ErrorHandler,
    ) -> None:
        self.registry[exc_type] = handler

    async def handle(self, exception: Exception) -> web.StreamResponse:
        if handler := self.registry.get(type(exception)):
            return await handler(exception)
        raise exception


@web.middleware
async def error_handling_middleware(request: Request, handler: Handler) -> web.StreamResponse:
    error_handler_registry: ErrorHandlerRegistry = request.app["error_handler_registry"]
    try:
        return await handler(request)
    except Exception as exc:
        return await error_handler_registry.handle(exc)


async def pydantic_error_handler(exception: ValidationError) -> web.StreamResponse:
    return web.json_response(exception.errors(), status=HTTPStatus.BAD_REQUEST)
