from dataclasses import dataclass, asdict
@dataclass
class ModelSpec:
    id: str
    name: str
    dataset_id: str
    false_negative_cost: float
    false_positive_cost: float
    daily_budget: int
    def to_dict(self):
        return asdict(self)
