from fastapi import HTTPException
from src.config import database as db
from src.services.dataset_service import get as get_dataset
from src.models.model_spec import ModelSpec
from src.utils.ids import new_id, now

def create(data):
    get_dataset(data["dataset_id"])
    obj=ModelSpec(new_id("model"),data["name"],data["dataset_id"],data["false_negative_cost"],data["false_positive_cost"],data["daily_budget"]).to_dict()
    obj.update(seed=data["seed"],created_at=now());return db.insert("models",obj)
def get(key):
    obj=db.get("models",key)
    if not obj:raise HTTPException(404,"模型配置不存在")
    return obj
def listing():return db.all_rows("models")
