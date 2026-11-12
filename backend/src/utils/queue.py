import socket
from src.config.settings import REDIS_HOST, REDIS_PORT
QUEUE="pipe-priority:runs"
def command(*args, timeout=8):
    encoded=[str(x).encode() for x in args]
    msg=b"*"+str(len(encoded)).encode()+b"\r\n"+b"".join(b"$"+str(len(x)).encode()+b"\r\n"+x+b"\r\n" for x in encoded)
    with socket.create_connection((REDIS_HOST,REDIS_PORT),timeout=timeout) as s:
        s.settimeout(timeout);s.sendall(msg); f=s.makefile("rb")
        def read():
            line=f.readline(); kind=line[:1]; body=line[1:-2]
            if kind==b"+":return body.decode()
            if kind==b"-":raise RuntimeError(body.decode())
            if kind==b":":return int(body)
            if kind==b"$":
                n=int(body)
                if n<0:return None
                v=f.read(n);f.read(2);return v.decode()
            if kind==b"*":
                n=int(body);return [read() for _ in range(n)] if n>=0 else None
            raise RuntimeError("Redis 响应无效")
        return read()
def push(run_id): return command("RPUSH",QUEUE,run_id)
def pop():
    data=command("BLPOP",QUEUE,5,timeout=8)
    return data[1] if data else None
