from dataclasses import dataclass, field, asdict
@dataclass
class InspectionPlan:
    id: str
    name: str
    run_id: str
    status: str
    pipes: list[dict]
    work_date: str = ""
    crew: str = ""
    budget: int = 0
    shortfall: int = 0
    occupied_pipe_ids: list[str] = field(default_factory=list)
    conflicts: list[dict] = field(default_factory=list)
    def to_dict(self):
        return asdict(self)
