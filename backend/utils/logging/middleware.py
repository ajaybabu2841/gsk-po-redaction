# backend/utils/logging/middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from uuid import uuid4
from utils.logging.request_context import request_id_ctx


class RequestContextMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid4()))
        request_id_ctx.set(request_id)

        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response
