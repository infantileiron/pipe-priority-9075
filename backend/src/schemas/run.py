from pydantic import BaseModel, ConfigDict
class RunCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_id: str
