from pydantic import BaseModel, Field
class ModelCreate(BaseModel):
    name: str = Field(min_length=2,max_length=100)
    dataset_id: str
    false_negative_cost: float = Field(default=25,gt=0,le=10000)
    false_positive_cost: float = Field(default=1,gt=0,le=10000)
    daily_budget: int = Field(default=40,ge=1,le=5000)
    seed: int = Field(default=42,ge=0,le=2147483647)
