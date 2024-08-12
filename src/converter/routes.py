from aiohttp import web

from converter.schemas import ConvertRequestSchema, ConvertResponseSchema
from converter.service import ConvertService

convert_app = web.Application()
routes = web.RouteTableDef()


@routes.post("")
async def convert_currencies(request: web.Request) -> web.Response:
    service: ConvertService = request.config_dict["convert_service"]
    request_data = ConvertRequestSchema.model_validate_json(await request.text())

    conversion = await service.convert(
        request_data.currency_from,
        request_data.currency_to,
        request_data.exchange,
        request_data.amount,
        request_data.cache_max_seconds,
    )

    response_data = ConvertResponseSchema(
        currency_from=conversion.currency_from,
        currency_to=conversion.currency_to,
        exchange=conversion.exchange,
        rate=conversion.rate,
        result=conversion.result,
        updated_at=conversion.updated_at,
    )
    return web.json_response(text=response_data.model_dump_json())


convert_app.add_routes(routes)
