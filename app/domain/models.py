from dataclasses import dataclass

@dataclass(frozen=True)
class OrderLine:
    order_id: str
    sku : str
    quantity: int


class Batch:
    def __init__(self, ref: str, sku: str, purchased_quantity: int):
        self.ref = ref
        self.sku = sku
        self.purchased_quantity = purchased_quantity
        self._allocations = set()
        self.events = []

    def __eq__(self, other):
        return self.ref == other.ref

    def __hash__(self):
        return hash(self.ref)
    
    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)
    
    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.quantity
    
    @property
    def allocated_quantity(self) -> int:
        return sum(line.quantity for line in self._allocations)
    
    @property
    def available_quantity(self) -> int:
        return self.purchased_quantity - self.allocated_quantity
