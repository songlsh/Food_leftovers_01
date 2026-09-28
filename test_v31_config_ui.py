from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app.config.system_config import SystemConfigService, WEEKDAYS


def main():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        svc = SystemConfigService()
        import app.config.system_config as sc
        old_menu, old_device = sc.WEEKLY_MENU_PATH, sc.DEVICE_CONFIG_PATH
        sc.WEEKLY_MENU_PATH = root / "weekly_menu.json"
        sc.DEVICE_CONFIG_PATH = root / "device_config.json"
        try:
            menu = {"version":"1.0"}
            for day in WEEKDAYS:
                menu[day] = {"foods":[{"food_id":"F001","food_name":"米饭","prompt":"一份米饭"}]}
            svc.save_weekly_menu(menu)
            loaded = svc.load_weekly_menu()
            assert loaded["monday"]["foods"][0]["food_name"] == "米饭"
            foods = svc.list_foods(); assert foods[0]["food_id"] == "F001"
            foods.append({"food_id":"F002","food_name":"土豆丝","prompt":"一份土豆丝"})
            menu["monday"]["foods"].append(dict(foods[-1]))
            svc.save_weekly_menu(menu)
            assert any(x["food_id"] == "F002" for x in svc.list_foods())
            svc.save_device_config({"weight":{"mode":"arduino","serial_port":"COM3"},"camera":{"mode":"esp32cam","ip_address":"192.168.1.100"}})
            device = svc.load_device_config()
            assert device["weight"]["mode"] == "arduino"
            assert device["camera"]["mode"] == "esp32cam"
            print("V31 config service test passed")
            print("Menu persistence: OK")
            print("Food management persistence: OK")
            print("Device config persistence: OK")
        finally:
            sc.WEEKLY_MENU_PATH, sc.DEVICE_CONFIG_PATH = old_menu, old_device


if __name__ == "__main__":
    main()
