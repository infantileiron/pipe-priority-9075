from dataclasses import dataclass, asdict
@dataclass
class Report:
    id: str
    name: str
    plan_id: str
    format: str = "csv"
    def to_dict(self):
        return asdict(self)
