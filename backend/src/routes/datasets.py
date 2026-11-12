from fastapi import APIRouter,Depends
from src.controllers import dataset_controller as ctl
from src.schemas.dataset import DatasetCreate
from src.services.auth_service import current_user,editor
router=APIRouter(prefix='/datasets',tags=['datasets'])
@router.get('')
def listing(user=Depends(current_user)):return ctl.listing()
@router.get('/{key}')
def detail(key:str,user=Depends(current_user)):return ctl.get(key)
@router.post('',status_code=201)
def create(body:DatasetCreate,user=Depends(editor)):return ctl.create(body.model_dump())
from src.schemas.dataset import DatasetCSV
@router.post('/import-csv',status_code=201)
def import_csv(body:DatasetCSV,user=Depends(editor)):return ctl.create_csv(body.model_dump())
