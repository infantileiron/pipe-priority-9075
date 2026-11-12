import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI,Depends,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.config import database as db
from src.config.settings import SEED_DEMO,LOCAL_TEST
from src.middlewares.audit import AuditMiddleware
from src.middlewares.errors import value_error,server_error,ErrorBoundaryMiddleware
from src.services.auth_service import current_user
from src.utils.queue import command
from src.routes import auth,datasets,models,runs,plans,reports
@asynccontextmanager
async def lifespan(app):
    db.initialize()
    if SEED_DEMO:
        try:
            from scripts.seed_demo import seed
            seed()
        except Exception:logging.exception('演示数据初始化失败，可手动重试 seed')
    yield
app=FastAPI(title='澄川水务 · 漏损巡检优先级',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:18201','http://127.0.0.1:18201','http://localhost:5173'],allow_methods=['*'],allow_headers=['*'])
app.add_middleware(AuditMiddleware)
app.add_middleware(ErrorBoundaryMiddleware)
app.add_exception_handler(ValueError,value_error)
app.add_exception_handler(Exception,server_error)
for module in [auth,datasets,models,runs,plans,reports]:app.include_router(module.router)
@app.get('/health')
def health():
    try:
        db.all_rows('users')
        if not LOCAL_TEST:command('PING')
    except Exception:raise HTTPException(503,'数据库或Redis尚未就绪')
    return {'status':'ok','mode':'local-synchronous-test' if LOCAL_TEST else 'mysql-redis-worker'}
@app.get('/overview')
def overview(user=Depends(current_user)):
    data=db.all_rows('datasets');runs_=db.all_rows('runs');plans_=db.all_rows('plans')
    return {'datasets':len(data),'pipes':sum(len(x['rows']) for x in data),'runs':len(runs_),'completed':sum(x['status']=='completed' for x in runs_),'approved':sum(x['status']=='approved' for x in plans_),'districts':sorted({r.get('district','未标记') for d in data for r in d['rows']}),'latest_run':next((x for x in reversed(runs_) if x['status']=='completed'),None)}
@app.get('/audit')
def audit(user=Depends(current_user)):return db.all_rows('audit')[-100:]
