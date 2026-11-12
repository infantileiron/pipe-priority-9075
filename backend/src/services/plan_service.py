from fastapi import HTTPException
from src.config import database as db
from src.constants.enums import PlanStatus,RunStatus
from src.services.run_service import get as get_run
from src.models.inspection_plan import InspectionPlan
from src.utils.ids import new_id,now

def create(data):
    run=get_run(data['run_id'])
    if run['status']!=RunStatus.COMPLETED.value:raise HTTPException(409,'请先完成模型训练')
    pipes=run['result']['ranking'][:data['budget']]
    obj=InspectionPlan(new_id('plan'),data['name'],data['run_id'],PlanStatus.DRAFT.value,pipes).to_dict();obj.update(created_at=now(),budget=data['budget'],review_note='')
    return db.insert('plans',obj)
def get(key):
    obj=db.get('plans',key)
    if not obj:raise HTTPException(404,'巡检计划不存在')
    return obj
def approve(key,note,user):
    obj=get(key)
    if obj['status']==PlanStatus.APPROVED.value:raise HTTPException(409,'计划已审批')
    obj.update(status=PlanStatus.APPROVED.value,review_note=note,approved_by=user['email'],approved_at=now());return db.insert('plans',obj)
def listing():return db.all_rows('plans')
