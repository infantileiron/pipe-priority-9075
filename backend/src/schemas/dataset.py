from pydantic import BaseModel, Field
class DatasetCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    filename: str = Field(default="pipe_inspection_202611.csv", max_length=120)
    rows: list[dict] = Field(min_length=40, max_length=5000)
class DatasetCSV(BaseModel):
    name: str = Field(min_length=2,max_length=100)
    filename: str = "uploaded.csv"
    csv_text: str = Field(max_length=2000000)
