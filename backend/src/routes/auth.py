from fastapi import APIRouter,Depends
from src.schemas.auth import Login
from src.services.auth_service import login,current_user
router=APIRouter(prefix='/auth',tags=['auth'])
@router.post('/login')
def sign_in(body:Login):return login(body.email,body.password)
@router.get('/me')
def me(user=Depends(current_user)):return user
