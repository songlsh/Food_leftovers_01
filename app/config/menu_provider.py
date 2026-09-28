from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

from app.models.menu import DailyMenu, FoodClass


class DailyMenuProvider:
    """Load the fixed weekly cafeteria menu and expose today's menu."""

    WEEKDAY_KEYS = (
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
    )

    def __init__(self, config_path: str | Path = "config/weekly_menu.json"):
        self.config_path = Path(config_path)
        self._data: Optional[dict] = None

    def load(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(self.config_path)
        raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("weekly menu config must be a JSON object")
        self._data = raw

    def get_menu(self, target_date: date | str) -> DailyMenu:
        if self._data is None:
            self.load()

        if isinstance(target_date, str):
            target_date = date.fromisoformat(target_date)

        key = self.WEEKDAY_KEYS[target_date.weekday()]
        item = self._data.get(key)
        if item is None:
            raise ValueError(f"no menu configured for weekday: {key}")

        if isinstance(item, list):
            foods_raw = item
            version = str(self._data.get("version", "1.0"))
        elif isinstance(item, dict):
            foods_raw = item.get("foods", [])
            version = str(item.get("version", self._data.get("version", "1.0")))
        else:
            raise ValueError(f"invalid menu config for {key}")

        foods = []
        for food in foods_raw:
            if not isinstance(food, dict):
                raise ValueError(f"invalid food entry in {key}")
            foods.append(
                FoodClass(
                    food_id=str(food["food_id"]),
                    food_name=str(food["food_name"]),
                    prompt=food.get("prompt"),
                )
            )

        if not foods:
            raise ValueError(f"menu for {key} cannot be empty")

        return DailyMenu(
            date=target_date.isoformat(),
            weekday=key,
            foods=foods,
            version=version,
        )

    def get_today_menu(self) -> DailyMenu:
        return self.get_menu(date.today())
