import logging,time
from starlette.middleware.base import BaseHTTPMiddleware
from src.config.database import insert
from src.utils.ids import new_id,now
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        started=time.monotonic();response=await call_next(request)
        if request.url.path!='/health':
            try:insert('audit',{'id':new_id('audit'),'at':now(),'actor':getattr(request.state,'actor','anonymous'),'method':request.method,'path':request.url.path,'status':response.status_code,'duration_ms':round((time.monotonic()-started)*1000,1)})
            except Exception:logging.exception('审计写入失败')
        response.headers['X-Content-Type-Options']='nosniff'
        return response
