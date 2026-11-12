from pydantic import BaseModel, Field
class PlanCreate(BaseModel):
    name: str = Field(min_length=2,max_length=100)
    run_id: str
    budget: int = Field(default=40,ge=1,le=5000)
class PlanReview(BaseModel):
    note: str = Field(min_length=2,max_length=500)
