from dataclasses import dataclass, field

from models.materials import MaterialItem
from models.service import ServiceItem
from models.vehicle import Client, Vehicle


@dataclass(slots=True)
class Invoice:
    id: int | None = None
    date: str = ""
    client: Client = field(default_factory=Client)
    vehicle: Vehicle = field(default_factory=Vehicle)
    materials: list[MaterialItem] = field(default_factory=list)
    services: list[ServiceItem] = field(default_factory=list)

    @property
    def materials_total(self) -> float:
        return sum(item.total for item in self.materials)

    @property
    def services_total(self) -> float:
        return sum(item.total for item in self.services)

    @property
    def total(self) -> float:
        return self.materials_total + self.services_total
