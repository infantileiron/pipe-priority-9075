from dataclasses import dataclass, asdict
@dataclass
class InspectionPlan:
    id: str
    name: str
    run_id: str
    status: str
    pipes: list[dict]
    def to_dict(self):
        return asdict(self)
