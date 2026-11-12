from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.config.database import all_rows, get
from src.constants.enums import Role
from src.utils.security import verify_password, token_for, decode
bearer=HTTPBearer(auto_error=False)
def login(email,password):
    user=next((u for u in all_rows("users") if u["email"]==email),None)
    if not user or not verify_password(password,user["password_hash"]): raise HTTPException(401,"账号或密码错误")
    return {"access_token":token_for(user),"token_type":"bearer","user":{k:v for k,v in user.items() if k!="password_hash"}}
def current_user(request: Request, credential: HTTPAuthorizationCredentials=Depends(bearer)):
    if not credential:raise HTTPException(401,"请先登录")
    claims=decode(credential.credentials); user=get("users",claims["sub"])
    if not user:raise HTTPException(401,"账号不存在")
    request.state.actor=user["email"]
    return {k:v for k,v in user.items() if k!="password_hash"}
def editor(user=Depends(current_user)):
    if user["role"] not in (Role.ADMIN.value,Role.ANALYST.value):raise HTTPException(403,"只读账号不能修改或运行分析")
    return user
def admin(user=Depends(current_user)):
    if user["role"]!=Role.ADMIN.value:raise HTTPException(403,"只有管理员可以审批巡检计划")
    return user
