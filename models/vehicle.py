from dataclasses import dataclass


@dataclass(slots=True)
class Client:
    id: int | None = None
    name: str = ""
    phone: str = ""
    notes: str = ""


@dataclass(slots=True)
class Vehicle:
    id: int | None = None
    client_id: int | None = None
    brand: str = ""
    model: str = ""
    vin: str = ""
    number: str = ""
    mileage: str = ""
    notes: str = ""
