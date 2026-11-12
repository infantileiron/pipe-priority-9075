from fastapi import APIRouter,Depends
from src.controllers import model_controller as ctl
from src.schemas.model import ModelCreate
from src.services.auth_service import current_user,editor
router=APIRouter(prefix='/models',tags=['models'])
@router.get('')
def listing(user=Depends(current_user)):return ctl.listing()
@router.get('/{key}')
def detail(key:str,user=Depends(current_user)):return ctl.get(key)
@router.post('',status_code=201)
def create(body:ModelCreate,user=Depends(editor)):return ctl.create(body.model_dump())
