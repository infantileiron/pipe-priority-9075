from fastapi import APIRouter,Depends
from src.controllers import plan_controller as ctl
from src.schemas.plan import PlanCreate
from src.services.auth_service import current_user,editor
router=APIRouter(prefix='/plans',tags=['plans'])
@router.get('')
def listing(user=Depends(current_user)):return ctl.listing()
@router.get('/{key}')
def detail(key:str,user=Depends(current_user)):return ctl.get(key)
@router.post('',status_code=201)
def create(body:PlanCreate,user=Depends(editor)):return ctl.create(body.model_dump())
from src.schemas.plan import PlanReview
from src.services.auth_service import admin
@router.post('/{key}/approve')
def approve(key:str,body:PlanReview,user=Depends(admin)):return ctl.approve(key,body.note,user)
