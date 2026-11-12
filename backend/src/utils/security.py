import base64, hashlib, hmac, json, os, time
from fastapi import HTTPException
from src.config.settings import JWT_SECRET

def b64(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def unb64(s): return base64.urlsafe_b64decode(s+"="*(-len(s)%4))
def hash_password(password):
    salt=os.urandom(16)
    return b64(salt)+"."+b64(hashlib.pbkdf2_hmac("sha256",password.encode(),salt,180000))
def verify_password(password, stored):
    salt,digest=stored.split(".")
    return hmac.compare_digest(b64(hashlib.pbkdf2_hmac("sha256",password.encode(),unb64(salt),180000)),digest)
def token_for(user):
    head=b64(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
    body=b64(json.dumps({"sub":user["id"],"role":user["role"],"exp":int(time.time())+28800}).encode())
    return head+"."+body+"."+b64(hmac.new(JWT_SECRET.encode(),(head+"."+body).encode(),hashlib.sha256).digest())
def decode(token):
    try:
        head,body,sig=token.split(".")
        assert json.loads(unb64(head))["alg"]=="HS256"
        assert hmac.compare_digest(sig,b64(hmac.new(JWT_SECRET.encode(),(head+"."+body).encode(),hashlib.sha256).digest()))
        obj=json.loads(unb64(body)); assert obj["exp"]>time.time()
        return obj
    except Exception:
        raise HTTPException(401,"登录已过期，请重新登录")
