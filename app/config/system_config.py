from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config.paths import BASE_DIR

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
WEEKDAY_NAMES = {
    "monday": "星期一", "tuesday": "星期二", "wednesday": "星期三",
    "thursday": "星期四", "friday": "星期五", "saturday": "星期六", "sunday": "星期日",
}
WEEKLY_MENU_PATH = BASE_DIR / "config" / "weekly_menu.json"
DEVICE_CONFIG_PATH = BASE_DIR / "config" / "device_config.json"

DEFAULT_DEVICE_CONFIG = {
    "version": "1.0",
    "weight": {"mode": "mock", "serial_port": ""},
    "camera": {"mode": "mock", "ip_address": ""},
}


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


class SystemConfigService:
    """Small cross-platform configuration service used by the V31 GUI."""

    def load_weekly_menu(self) -> dict:
        data = _read_json(WEEKLY_MENU_PATH, {"version": "1.0"})
        if not isinstance(data, dict):
            raise ValueError("weekly_menu.json 必须是 JSON 对象")
        for day in WEEKDAYS:
            data.setdefault(day, {"foods": []})
            if not isinstance(data[day], dict):
                raise ValueError(f"{day} 菜单配置格式错误")
            data[day].setdefault("foods", [])
        data.setdefault("version", "1.0")
        return data

    def save_weekly_menu(self, data: dict) -> None:
        if not isinstance(data, dict):
            raise ValueError("菜单配置格式错误")
        for day in WEEKDAYS:
            foods = data.get(day, {}).get("foods", [])
            if not foods:
                raise ValueError(f"{WEEKDAY_NAMES[day]}至少需要配置一道菜")
            ids = [str(item.get("food_id", "")).strip() for item in foods]
            if any(not item for item in ids):
                raise ValueError(f"{WEEKDAY_NAMES[day]}存在无效菜品")
            if len(ids) != len(set(ids)):
                raise ValueError(f"{WEEKDAY_NAMES[day]}存在重复菜品")
        data["version"] = str(data.get("version", "1.0"))
        _write_json(WEEKLY_MENU_PATH, data)

    def list_foods(self) -> list[dict]:
        data = self.load_weekly_menu()
        foods: dict[str, dict] = {}
        for day in WEEKDAYS:
            for item in data[day].get("foods", []):
                fid = str(item.get("food_id", "")).strip()
                if fid and fid not in foods:
                    foods[fid] = {
                        "food_id": fid,
                        "food_name": str(item.get("food_name", "")).strip(),
                        "prompt": str(item.get("prompt", "")).strip(),
                    }
        return sorted(foods.values(), key=lambda x: x["food_id"])

    def save_foods(self, foods: list[dict]) -> None:
        data = self.load_weekly_menu()
        catalog: dict[str, dict] = {}
        for food in foods:
            fid = str(food.get("food_id", "")).strip()
            name = str(food.get("food_name", "")).strip()
            prompt = str(food.get("prompt", "")).strip()
            if not fid or not name:
                raise ValueError("菜品编号和名称不能为空")
            if fid in catalog:
                raise ValueError(f"菜品编号重复：{fid}")
            catalog[fid] = {"food_id": fid, "food_name": name, "prompt": prompt or name}

        for day in WEEKDAYS:
            for item in data[day].get("foods", []):
                fid = str(item.get("food_id", "")).strip()
                if fid in catalog:
                    item.update(catalog[fid])
                else:
                    raise ValueError(f"菜品 {fid} 已从菜品管理中删除，请先从对应菜单移除")
        data["_catalog"] = None  # not persisted; keeps the on-disk format unchanged
        data.pop("_catalog", None)
        self.save_weekly_menu(data)

    def add_food_to_day(self, day: str, food: dict) -> None:
        data = self.load_weekly_menu()
        if day not in WEEKDAYS:
            raise ValueError("无效星期")
        fid = str(food["food_id"]).strip()
        if any(str(x.get("food_id")) == fid for x in data[day]["foods"]):
            return
        data[day]["foods"].append({
            "food_id": fid,
            "food_name": str(food["food_name"]),
            "prompt": str(food.get("prompt") or food["food_name"]),
        })
        self.save_weekly_menu(data)

    def load_device_config(self) -> dict:
        data = _read_json(DEVICE_CONFIG_PATH, DEFAULT_DEVICE_CONFIG.copy())
        if not isinstance(data, dict):
            raise ValueError("device_config.json 必须是 JSON 对象")
        result = json.loads(json.dumps(DEFAULT_DEVICE_CONFIG))
        result.update(data)
        result["weight"].update(data.get("weight", {}))
        result["camera"].update(data.get("camera", {}))
        return result

    def save_device_config(self, data: dict) -> None:
        weight_mode = data.get("weight", {}).get("mode", "mock")
        camera_mode = data.get("camera", {}).get("mode", "mock")
        if weight_mode not in {"mock", "arduino"}:
            raise ValueError("称重设备类型无效")
        if camera_mode not in {"mock", "esp32cam"}:
            raise ValueError("摄像头类型无效")
        _write_json(DEVICE_CONFIG_PATH, {
            "version": "1.0",
            "weight": {
                "mode": weight_mode,
                "serial_port": str(data.get("weight", {}).get("serial_port", "")).strip(),
            },
            "camera": {
                "mode": camera_mode,
                "ip_address": str(data.get("camera", {}).get("ip_address", "")).strip(),
            },
        })
