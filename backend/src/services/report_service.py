import csv,io
from fastapi import HTTPException
from src.config import database as db
from src.constants.enums import PlanStatus
from src.services.plan_service import get as get_plan
from src.models.report import Report
from src.utils.ids import new_id,now

def create(data):
    plan=get_plan(data['plan_id'])
    if plan['status']!=PlanStatus.APPROVED.value:raise HTTPException(409,'计划审批通过后才能生成正式报告')
    report=Report(new_id('report'),data['name'],data['plan_id']).to_dict();report['created_at']=now();return db.insert('reports',report)
def get(key):
    obj=db.get('reports',key)
    if not obj:raise HTTPException(404,'报告不存在')
    return obj
def listing():return db.all_rows('reports')
def export(key):
    report=get(key);plan=get_plan(report['plan_id']);out=io.StringIO();writer=csv.writer(out)
    writer.writerow(['priority','pipe_id','district','material','age','leak_probability','approved_by'])
    def cell(value):
        text=str(value)
        return "'"+text if text[:1] in ('=','+','-','@') else text
    for i,p in enumerate(plan['pipes'],1):writer.writerow([i,cell(p['pipe_id']),cell(p['district']),cell(p['material']),p['age'],round(p['probability'],6),cell(plan.get('approved_by',''))])
    return '\ufeff'+out.getvalue()
