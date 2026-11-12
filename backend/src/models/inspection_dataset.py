from dataclasses import dataclass, asdict
@dataclass
class InspectionDataset:
    id: str
    name: str
    rows: list[dict]
    filename: str
    def to_dict(self):
        return asdict(self)
