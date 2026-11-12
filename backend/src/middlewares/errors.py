import logging
from fastapi import Request
from fastapi.responses import JSONResponse
async def value_error(request:Request,error:ValueError):
    return JSONResponse({'detail':str(error)},status_code=422)
async def server_error(request:Request,error:Exception):
    logging.exception('请求失败',exc_info=error)
    return JSONResponse({'detail':'服务暂时不可用，请检查依赖并重试'},status_code=500)

from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4
class ErrorBoundaryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        request_id=uuid4().hex[:12]
        try:
            response=await call_next(request)
        except Exception as error:
            response=await server_error(request,error)
        response.headers['X-Request-ID']=request_id
        return response
