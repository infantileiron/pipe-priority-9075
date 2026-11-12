from fastapi import APIRouter,Depends
from src.controllers import run_controller as ctl
from src.schemas.run import RunCreate
from src.services.auth_service import current_user,editor
router=APIRouter(prefix='/runs',tags=['runs'])
@router.get('')
def listing(user=Depends(current_user)):return ctl.listing()
@router.get('/{key}')
def detail(key:str,user=Depends(current_user)):return ctl.get(key)
@router.post('',status_code=201)
def create(body:RunCreate,user=Depends(editor)):return ctl.create(body.model_id)
