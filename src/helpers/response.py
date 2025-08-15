from typing import Any
from fastapi import Response
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

def api_response(data: Any, status_code: int = 200) -> Response:
    return JSONResponse(
        content={
            "data": jsonable_encoder(data),
            "status_code": status_code,
        },
        status_code=status_code,
    )