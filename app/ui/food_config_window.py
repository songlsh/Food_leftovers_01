from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.food import Food


class FoodConfigWindow(QMainWindow):
    """V25 food/initial-weight/suggestion-rule configuration.

    UX rules:
    - Boolean "启用" fields are always combo boxes (是/否), never free text.
    - Suggestion rules use an explicit add/edit/save/delete workflow.
    - While adding a new rule, edit/delete are disabled; save/cancel are enabled.
    - While editing an existing rule, add/delete are disabled; save/cancel are enabled.
    - With no edit operation active, add/edit/delete are enabled according to selection.
    """

    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.db = database
        self._rule_mode = None  # None / "add" / "edit"
        self._editing_rule_id = None
        self.setWindowTitle("剩菜检测系统 - V25 食物与建议配置")
        self.resize(1100, 700)
        self._build()
        self._load()
        self._update_rule_buttons()

    # ---------- common widgets ----------
    @staticmethod
    def _enabled_combo(value=True):
        combo = QComboBox()
        combo.addItems(["是", "否"])
        combo.setCurrentIndex(0 if value else 1)
        return combo

    @staticmethod
    def _item_text(table, row, col, default=""):
        item = table.item(row, col)
        return item.text().strip() if item else default

    # ---------- UI ----------
    def _build(self):
        central = QWidget()
        root = QVBoxLayout(central)

        food_box = QGroupBox("食物初始重量配置（克）")
        food_layout = QVBoxLayout(food_box)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["食物ID", "食物名称", "类别", "初始重量(g)", "启用"])
        self.table.setAlternatingRowColors(True)
        food_layout.addWidget(self.table)
        food_save = QPushButton("保存食物配置")
        food_save.clicked.connect(self._save_foods)
        food_layout.addWidget(food_save, 0, Qt.AlignRight)
        root.addWidget(food_box)

        rule_box = QGroupBox("建议规则：按剩余率自动匹配")
        rule_layout = QVBoxLayout(rule_box)
        self.rules = QTableWidget(0, 5)
        self.rules.setHorizontalHeaderLabels(["规则ID", "最小剩余率", "最大剩余率", "建议语句", "启用"])
        self.rules.setAlternatingRowColors(True)
        self.rules.setSelectionBehavior(QTableWidget.SelectRows)
        self.rules.itemSelectionChanged.connect(self._update_rule_buttons)
        rule_layout.addWidget(self.rules)

        buttons = QHBoxLayout()
        self.add_rule_button = QPushButton("新增规则")
        self.edit_rule_button = QPushButton("修改规则")
        self.save_rule_button = QPushButton("保存规则")
        self.cancel_rule_button = QPushButton("取消")
        self.delete_rule_button = QPushButton("删除选中规则")
        self.add_rule_button.clicked.connect(self._start_add_rule)
        self.edit_rule_button.clicked.connect(self._start_edit_rule)
        self.save_rule_button.clicked.connect(self._save_current_rule)
        self.cancel_rule_button.clicked.connect(self._cancel_rule_edit)
        self.delete_rule_button.clicked.connect(self._delete_rule)
        for button in (
            self.add_rule_button,
            self.edit_rule_button,
            self.save_rule_button,
            self.cancel_rule_button,
            self.delete_rule_button,
        ):
            buttons.addWidget(button)
        buttons.addStretch(1)
        rule_layout.addLayout(buttons)
        root.addWidget(rule_box)

        hint = QLabel(
            "操作方式：先选中规则→修改规则→保存；新增规则后填写内容→保存。\n"
            "新增/修改过程中，其他冲突操作会自动禁用；删除前请先选中要删除的规则。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#666; padding:4px;")
        root.addWidget(hint)

        self.setCentralWidget(central)

    # ---------- loading ----------
    def _load(self):
        self._rule_mode = None
        self._editing_rule_id = None

        foods = self.db.get_foods()
        self.table.setRowCount(0)
        for food in foods:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                food.food_id or "",
                food.food_name,
                food.category or "",
                "" if food.initial_weight is None else f"{food.initial_weight:g}",
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))
            self.table.setCellWidget(row, 4, self._enabled_combo(food.enabled))

        rules = self.db.get_suggestion_rules()
        self.rules.setRowCount(0)
        for rule in rules:
            self._append_rule_row(rule)

        self._set_rule_table_editable(False)
        self._update_rule_buttons()

    def _append_rule_row(self, rule):
        row = self.rules.rowCount()
        self.rules.insertRow(row)
        values = [
            str(rule["rule_id"]),
            f'{rule["min_value"]:.4f}',
            f'{rule["max_value"]:.4f}',
            rule["suggestion"],
        ]
        for col, value in enumerate(values):
            self.rules.setItem(row, col, QTableWidgetItem(value))
        self.rules.setCellWidget(row, 4, self._enabled_combo(rule.get("enabled", True)))

    # ---------- food config ----------
    def _save_foods(self):
        try:
            for row in range(self.table.rowCount()):
                food_id = self._item_text(self.table, row, 0)
                food_name = self._item_text(self.table, row, 1)
                category = self._item_text(self.table, row, 2) or None
                initial_text = self._item_text(self.table, row, 3)
                initial_weight = float(initial_text) if initial_text else None
                if initial_weight is not None and initial_weight < 0:
                    raise ValueError(f"第 {row + 1} 行初始重量不能小于 0")
                enabled = self.table.cellWidget(row, 4).currentIndex() == 0
                self.db.update_food(
                    Food(food_id, food_name, category, enabled, initial_weight)
                )
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return
        QMessageBox.information(self, "保存完成", "食物配置已保存。")

    # ---------- rule edit state ----------
    def _set_rule_table_editable(self, editable, target_row=None):
        # Rule ID is always read-only. Only the active row can be edited.
        for row in range(self.rules.rowCount()):
            row_editable = editable and (target_row is None or row == target_row)
            for col in range(1, 4):
                item = self.rules.item(row, col)
                if item:
                    item.setFlags(
                        (item.flags() | Qt.ItemIsEditable)
                        if row_editable
                        else (item.flags() & ~Qt.ItemIsEditable)
                    )
            combo = self.rules.cellWidget(row, 4)
            if combo:
                combo.setEnabled(row_editable)

    def _update_rule_buttons(self):
        active = self._rule_mode is not None
        selected = self.rules.currentRow() >= 0
        self.add_rule_button.setEnabled(not active)
        self.edit_rule_button.setEnabled(not active and selected)
        self.save_rule_button.setEnabled(active)
        self.cancel_rule_button.setEnabled(active)
        self.delete_rule_button.setEnabled(not active and selected)

    def _start_add_rule(self):
        if self._rule_mode is not None:
            return
        self._rule_mode = "add"
        self._editing_rule_id = None
        row = self.rules.rowCount()
        self.rules.insertRow(row)
        values = ["新规则", "0.0000", "1.0000", "请输入建议语句"]
        for col, value in enumerate(values):
            self.rules.setItem(row, col, QTableWidgetItem(value))
        self.rules.setCellWidget(row, 4, self._enabled_combo(True))
        self.rules.selectRow(row)
        self._set_rule_table_editable(True, row)
        self.rules.item(row, 1).setFocus()
        self.rules.editItem(self.rules.item(row, 1))
        self._update_rule_buttons()

    def _start_edit_rule(self):
        if self._rule_mode is not None:
            return
        row = self.rules.currentRow()
        if row < 0:
            return
        rule_id_text = self._item_text(self.rules, row, 0)
        if not rule_id_text or rule_id_text == "新规则":
            return
        self._rule_mode = "edit"
        self._editing_rule_id = int(rule_id_text)
        self._set_rule_table_editable(True, row)
        self.rules.selectRow(row)
        self._update_rule_buttons()

    def _validate_current_rule(self):
        row = self.rules.currentRow()
        if row < 0:
            raise ValueError("没有正在编辑的规则")
        min_value = float(self._item_text(self.rules, row, 1))
        max_value = float(self._item_text(self.rules, row, 2))
        suggestion = self._item_text(self.rules, row, 3)
        if not 0 <= min_value <= 1:
            raise ValueError("最小剩余率必须在 0～1 之间")
        if not 0 <= max_value <= 1:
            raise ValueError("最大剩余率必须在 0～1 之间")
        if min_value >= max_value:
            raise ValueError("最小剩余率必须小于最大剩余率")
        if not suggestion:
            raise ValueError("建议语句不能为空")
        return row, min_value, max_value, suggestion

    def _save_current_rule(self):
        if self._rule_mode is None:
            return
        try:
            row, min_value, max_value, suggestion = self._validate_current_rule()
            combo = self.rules.cellWidget(row, 4)
            enabled = combo.currentIndex() == 0 if combo else True
            rule_id = self._editing_rule_id if self._rule_mode == "edit" else None
            self.db.save_suggestion_rule(
                {
                    "rule_id": rule_id,
                    "metric": "remaining_rate",
                    "min_value": min_value,
                    "max_value": max_value,
                    "suggestion": suggestion,
                    "enabled": enabled,
                }
            )
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return
        self._load()
        QMessageBox.information(self, "保存完成", "建议规则已保存。")

    def _cancel_rule_edit(self):
        if self._rule_mode is None:
            return
        self._load()

    def _delete_rule(self):
        if self._rule_mode is not None:
            return
        row = self.rules.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中要删除的规则。")
            return
        rule_id_text = self._item_text(self.rules, row, 0)
        if rule_id_text == "新规则" or not rule_id_text:
            self._load()
            return
        answer = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除规则 {rule_id_text} 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self.db.delete_suggestion_rule(int(rule_id_text))
        self._load()
