import logging,time
from src.config.database import initialize
from src.config.settings import ARTIFACT_DIR
from src.utils.queue import pop
from src.services.run_service import execute

def main():
    initialize();ARTIFACT_DIR.mkdir(parents=True,exist_ok=True)
    while True:
        (ARTIFACT_DIR/'worker.heartbeat').touch()
        try:
            key=pop()
            if key:execute(key)
        except Exception:
            logging.exception('worker 队列故障');time.sleep(3)
if __name__=='__main__':main()
