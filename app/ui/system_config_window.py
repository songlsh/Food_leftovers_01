from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QAbstractItemView,
)

from app.config.system_config import SystemConfigService, WEEKDAYS, WEEKDAY_NAMES


class SystemConfigWindow(QMainWindow):
    """V31 cross-platform system configuration UI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = SystemConfigService()
        self.setWindowTitle("剩菜检测系统 - 系统配置")
        self.resize(1050, 700)
        self._build()
        self._load_all()

    def _build(self):
        central = QWidget()
        root = QVBoxLayout(central)
        title = QLabel("系统配置")
        title.setStyleSheet("font-size:22px;font-weight:700;")
        subtitle = QLabel("菜品、每周菜单和设备配置均可通过界面修改；当前硬件仍使用 Mock。")
        subtitle.setStyleSheet("color:#667085;")
        root.addWidget(title)
        root.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_food_tab(), "菜品管理")
        self.tabs.addTab(self._build_menu_tab(), "每周菜单")
        self.tabs.addTab(self._build_device_tab(), "设备配置")
        root.addWidget(self.tabs, 1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.reload_button = QPushButton("重新读取")
        self.reload_button.clicked.connect(self._load_all)
        bottom.addWidget(self.reload_button)
        self.save_all_button = QPushButton("保存当前配置")
        self.save_all_button.setObjectName("primaryButton")
        self.save_all_button.clicked.connect(self._save_all)
        bottom.addWidget(self.save_all_button)
        root.addLayout(bottom)
        self.setCentralWidget(central)

    def _build_food_tab(self):
        page = QWidget(); root = QVBoxLayout(page)
        root.addWidget(QLabel("菜品库（菜品编号在系统内保持稳定，建议不要随意修改已有编号）"))
        self.food_table = QTableWidget(0, 3)
        self.food_table.setHorizontalHeaderLabels(["菜品编号", "菜品名称", "AI识别提示"])
        self.food_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.food_table.setAlternatingRowColors(True)
        root.addWidget(self.food_table, 1)
        buttons = QHBoxLayout()
        add = QPushButton("新增菜品"); add.clicked.connect(self._add_food)
        delete = QPushButton("删除选中菜品"); delete.clicked.connect(self._delete_food)
        buttons.addWidget(add); buttons.addWidget(delete); buttons.addStretch(1)
        root.addLayout(buttons)
        return page

    def _build_menu_tab(self):
        page = QWidget(); root = QHBoxLayout(page)
        self.day_list = QListWidget()
        for day in WEEKDAYS:
            self.day_list.addItem(QListWidgetItem(WEEKDAY_NAMES[day]))
        self.day_list.currentRowChanged.connect(self._load_selected_day)
        root.addWidget(self.day_list, 0)

        right = QVBoxLayout()
        self.menu_table = QTableWidget(0, 3)
        self.menu_table.setHorizontalHeaderLabels(["菜品编号", "菜品名称", "AI识别提示"])
        self.menu_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.menu_table.setAlternatingRowColors(True)
        right.addWidget(self.menu_table, 1)
        buttons = QHBoxLayout()
        add = QPushButton("从菜品库添加"); add.clicked.connect(self._add_food_to_day)
        remove = QPushButton("移除选中菜品"); remove.clicked.connect(self._remove_food_from_day)
        buttons.addWidget(add); buttons.addWidget(remove); buttons.addStretch(1)
        right.addLayout(buttons)
        hint = QLabel("四个格子不绑定固定菜品；这里配置的是当天允许 AI 识别的候选菜品集合。")
        hint.setWordWrap(True); hint.setStyleSheet("color:#667085;padding:4px;")
        right.addWidget(hint)
        root.addLayout(right, 1)
        return page

    def _build_device_tab(self):
        page = QWidget(); root = QVBoxLayout(page)
        box = QGroupBox("重量设备")
        form = QFormLayout(box)
        self.weight_mode = QComboBox(); self.weight_mode.addItem("Mock（当前）", "mock"); self.weight_mode.addItem("Arduino UNO", "arduino")
        self.serial_port = QLineEdit(); self.serial_port.setPlaceholderText("例如：Windows COM3 / macOS /dev/cu.usbmodem...")
        form.addRow("设备类型", self.weight_mode); form.addRow("串口", self.serial_port)
        root.addWidget(box)
        box2 = QGroupBox("摄像头")
        form2 = QFormLayout(box2)
        self.camera_mode = QComboBox(); self.camera_mode.addItem("Mock（当前）", "mock"); self.camera_mode.addItem("ESP32-CAM", "esp32cam")
        self.camera_ip = QLineEdit(); self.camera_ip.setPlaceholderText("例如：192.168.1.100")
        form2.addRow("设备类型", self.camera_mode); form2.addRow("IP地址", self.camera_ip)
        root.addWidget(box2)
        note = QLabel("说明：V31 先完成配置保存与读取。真实 Arduino / ESP32-CAM 接入后，再让设备层读取这些参数；不会影响现有 Mock 测试。")
        note.setWordWrap(True); note.setStyleSheet("color:#667085;padding:8px;")
        root.addWidget(note)
        root.addStretch(1)
        return page

    def _load_all(self):
        try:
            self.menu_data = self.service.load_weekly_menu()
            self.foods = self.service.list_foods()
            self.device_data = self.service.load_device_config()
            self._fill_food_table()
            self.day_list.setCurrentRow(0)
            self._fill_device_form()
        except Exception as exc:
            QMessageBox.critical(self, "读取配置失败", str(exc))

    def _fill_food_table(self):
        self.food_table.setRowCount(0)
        for food in self.foods:
            row = self.food_table.rowCount(); self.food_table.insertRow(row)
            for col, value in enumerate((food["food_id"], food["food_name"], food["prompt"])):
                self.food_table.setItem(row, col, QTableWidgetItem(value))
        self.food_table.resizeColumnsToContents()

    def _fill_device_form(self):
        weight = self.device_data.get("weight", {})
        camera = self.device_data.get("camera", {})
        wi = self.weight_mode.findData(weight.get("mode", "mock")); self.weight_mode.setCurrentIndex(max(wi, 0))
        self.serial_port.setText(weight.get("serial_port", ""))
        ci = self.camera_mode.findData(camera.get("mode", "mock")); self.camera_mode.setCurrentIndex(max(ci, 0))
        self.camera_ip.setText(camera.get("ip_address", ""))

    def _add_food(self):
        row = self.food_table.rowCount(); self.food_table.insertRow(row)
        values = [f"F{self._next_food_number():03d}", "新菜品", "新菜品"]
        for col, value in enumerate(values): self.food_table.setItem(row, col, QTableWidgetItem(value))
        self.food_table.selectRow(row); self.food_table.editItem(self.food_table.item(row, 1))

    def _next_food_number(self):
        nums = []
        for row in range(self.food_table.rowCount()):
            text = self.food_table.item(row, 0).text().strip() if self.food_table.item(row, 0) else ""
            if text.startswith("F") and text[1:].isdigit(): nums.append(int(text[1:]))
        return max(nums, default=0) + 1

    def _delete_food(self):
        row = self.food_table.currentRow()
        if row < 0: return
        fid = self.food_table.item(row, 0).text().strip()
        used = [WEEKDAY_NAMES[d] for d in WEEKDAYS if any(str(x.get("food_id")) == fid for x in self.menu_data[d]["foods"])]
        if used:
            QMessageBox.warning(self, "无法删除", f"{fid} 正在用于：{'、'.join(used)}。请先从每周菜单移除。")
            return
        self.food_table.removeRow(row)

    def _current_day_key(self):
        row = self.day_list.currentRow()
        return WEEKDAYS[row] if 0 <= row < len(WEEKDAYS) else WEEKDAYS[0]

    def _load_selected_day(self, _row):
        if not hasattr(self, "menu_table"): return
        day = self._current_day_key(); self.menu_table.setRowCount(0)
        for food in self.menu_data[day]["foods"]:
            row = self.menu_table.rowCount(); self.menu_table.insertRow(row)
            for col, value in enumerate((food["food_id"], food["food_name"], food.get("prompt", ""))):
                item = QTableWidgetItem(str(value)); item.setFlags(item.flags() & ~Qt.ItemIsEditable); self.menu_table.setItem(row, col, item)
        self.menu_table.resizeColumnsToContents()

    def _add_food_to_day(self):
        day = self._current_day_key()
        choices = [f for f in self._read_food_table() if not any(str(x.get("food_id")) == f["food_id"] for x in self.menu_data[day]["foods"])]
        if not choices:
            QMessageBox.information(self, "没有可添加的菜品", "请先在菜品管理中新增菜品，或该日已经包含全部菜品。")
            return
        dialog = QDialog(self); dialog.setWindowTitle("选择菜品"); layout = QVBoxLayout(dialog)
        combo = QComboBox(); combo.addItems([f'{f["food_id"]} - {f["food_name"]}' for f in choices]); layout.addWidget(combo)
        buttons = QHBoxLayout(); ok = QPushButton("添加"); cancel = QPushButton("取消"); buttons.addWidget(ok); buttons.addWidget(cancel); layout.addLayout(buttons)
        ok.clicked.connect(dialog.accept); cancel.clicked.connect(dialog.reject)
        if dialog.exec() == QDialog.Accepted:
            food = choices[combo.currentIndex()]; self.menu_data[day]["foods"].append(dict(food)); self._load_selected_day(self.day_list.currentRow())

    def _remove_food_from_day(self):
        row = self.menu_table.currentRow()
        if row < 0: return
        day = self._current_day_key(); fid = self.menu_table.item(row, 0).text()
        if len(self.menu_data[day]["foods"]) <= 1:
            QMessageBox.warning(self, "无法移除", "每天至少保留一道菜。")
            return
        self.menu_data[day]["foods"] = [x for x in self.menu_data[day]["foods"] if str(x.get("food_id")) != fid]
        self._load_selected_day(self.day_list.currentRow())

    def _read_food_table(self):
        foods = []
        for row in range(self.food_table.rowCount()):
            foods.append({
                "food_id": self.food_table.item(row, 0).text().strip(),
                "food_name": self.food_table.item(row, 1).text().strip(),
                "prompt": self.food_table.item(row, 2).text().strip(),
            })
        return foods

    def _save_all(self):
        try:
            foods = self._read_food_table()
            catalog = {f["food_id"]: f for f in foods}
            if len(catalog) != len(foods): raise ValueError("菜品编号不能重复")
            for day in WEEKDAYS:
                for item in self.menu_data[day]["foods"]:
                    fid = str(item["food_id"])
                    if fid not in catalog: raise ValueError(f"{WEEKDAY_NAMES[day]}包含不存在的菜品：{fid}")
                    item.update(catalog[fid])
            self.menu_data["version"] = str(self.menu_data.get("version", "1.0"))
            self.service.save_weekly_menu(self.menu_data)
            self.service.save_device_config({
                "weight": {"mode": self.weight_mode.currentData(), "serial_port": self.serial_port.text()},
                "camera": {"mode": self.camera_mode.currentData(), "ip_address": self.camera_ip.text()},
            })
            self._load_all()
            QMessageBox.information(self, "保存完成", "系统配置已保存。\n现有历史 Event 不会被重新识别。")
        except Exception as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
