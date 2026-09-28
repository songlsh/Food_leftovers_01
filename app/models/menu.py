from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class FoodClass:
    food_id: str
    food_name: str
    prompt: Optional[str] = None

    def __post_init__(self):
        if not self.food_id:
            raise ValueError("food_id cannot be empty")
        if not self.food_name:
            raise ValueError("food_name cannot be empty")

    @property
    def model_prompt(self) -> str:
        return self.prompt or f"一份{self.food_name}"


@dataclass
class DailyMenu:
    date: str
    weekday: str
    foods: list[FoodClass] = field(default_factory=list)
    version: str = "1.0"

    def food_ids(self) -> list[str]:
        return [food.food_id for food in self.foods]

    def get_food(self, food_id: str) -> Optional[FoodClass]:
        return next((food for food in self.foods if food.food_id == food_id), None)

    def to_snapshot(self) -> dict:
        return {
            "date": self.date,
            "weekday": self.weekday,
            "version": self.version,
            "foods": [
                {
                    "food_id": food.food_id,
                    "food_name": food.food_name,
                    "prompt": food.prompt,
                }
                for food in self.foods
            ],
        }
