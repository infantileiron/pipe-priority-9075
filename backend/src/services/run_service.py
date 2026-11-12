import logging
from fastapi import HTTPException
from src.config import database as db
from src.config.settings import LOCAL_TEST
from src.constants.enums import RunStatus
from src.services.model_service import get as get_model
from src.services.dataset_service import get as get_dataset
from src.services.modeling import train
from src.models.training_run import TrainingRun
from src.utils.ids import new_id,now
from src.utils.queue import push

def create(model_id):
    get_model(model_id)
    if sum(x['status'] in (RunStatus.QUEUED.value,RunStatus.RUNNING.value) for x in db.all_rows('runs'))>=8:raise HTTPException(429,"队列已满，请稍后重试")
    run=TrainingRun(new_id('run'),model_id,RunStatus.QUEUED.value).to_dict();run['created_at']=now();db.insert('runs',run)
    if LOCAL_TEST:execute(run['id'])
    else:
        try:push(run['id'])
        except Exception:
            run.update(status=RunStatus.FAILED.value,error='Redis 队列不可用，请恢复后新建运行');db.insert('runs',run);raise HTTPException(503,run['error'])
    return get(run['id'])
def execute(key):
    run=get(key)
    if run['status'] in (RunStatus.COMPLETED.value,RunStatus.FAILED.value):return run
    run.update(status=RunStatus.RUNNING.value,started_at=now());db.insert('runs',run)
    try:
        config=get_model(run['model_id']);data=get_dataset(config['dataset_id']);result=train(data['rows'],config)
        run.update(status=RunStatus.COMPLETED.value,result=result,completed_at=now(),error=None)
    except Exception as e:
        logging.exception('训练失败');run.update(status=RunStatus.FAILED.value,error=str(e),completed_at=now())
    return db.insert('runs',run)
def get(key):
    obj=db.get('runs',key)
    if not obj:raise HTTPException(404,'运行不存在')
    return obj
def listing():return [{k:v for k,v in x.items() if k!='result'} for x in db.all_rows('runs')]
