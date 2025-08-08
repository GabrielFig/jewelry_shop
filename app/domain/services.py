from typing import List, Optional
from app.domain.models import Batch, OrderLine

def allocate(line: OrderLine, batches: List[Batch]) -> Optional[str]:
    """
    Allocates an order line to a batch if possible.
    
    :param line: The order line to allocate.
    :param batches: List of available batches.
    :return: The reference of the batch if allocation is successful, None otherwise.
    """
    for batch in batches:
        if batch.can_allocate(line):
            batch.allocate(line)
            return batch.ref