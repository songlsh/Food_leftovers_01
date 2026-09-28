from dataclasses import dataclass
from typing import Optional


@dataclass
class Food:
    food_id: Optional[str] = None
    food_name: str = ""
    category: Optional[str] = None
    enabled: bool = True
    initial_weight: Optional[float] = None
