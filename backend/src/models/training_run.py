from dataclasses import dataclass, asdict
@dataclass
class TrainingRun:
    id: str
    model_id: str
    status: str
    result: dict | None = None
    error: str | None = None
    def to_dict(self):
        return asdict(self)
