from fastapi import APIRouter,Depends
from src.controllers import report_controller as ctl
from src.schemas.report import ReportCreate
from src.services.auth_service import current_user,editor
router=APIRouter(prefix='/reports',tags=['reports'])
@router.get('')
def listing(user=Depends(current_user)):return ctl.listing()
@router.get('/{key}')
def detail(key:str,user=Depends(current_user)):return ctl.get(key)
@router.post('',status_code=201)
def create(body:ReportCreate,user=Depends(editor)):return ctl.create(body.model_dump())
from fastapi.responses import Response
@router.get('/{key}/download')
def download(key:str,user=Depends(current_user)):
    return Response(ctl.export(key),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="pipe-inspection-{key}.csv"'})
