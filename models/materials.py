from dataclasses import dataclass


@dataclass(slots=True)
class MaterialItem:
    name: str
    qty: float = 1.0
    price: float = 0.0

    @property
    def total(self) -> float:
        return self.qty * self.price
