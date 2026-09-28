from pathlib import Path

ROOT = Path(__file__).resolve().parent
UI = (ROOT / 'app/ui/food_config_window.py').read_text(encoding='utf-8')

# "启用" must use selection widgets, not hand-written 是/否 text cells.
assert 'def _enabled_combo' in UI
assert 'self.table.setCellWidget(row, 4, self._enabled_combo(food.enabled))' in UI
assert 'self.rules.setCellWidget(row, 4, self._enabled_combo(rule.get("enabled", True)))' in UI

# Rule CRUD uses one explicit workflow: add/edit -> save/cancel, delete only when idle.
for token in (
    'self.add_rule_button = QPushButton("新增规则")',
    'self.edit_rule_button = QPushButton("修改规则")',
    'self.save_rule_button = QPushButton("保存规则")',
    'self.cancel_rule_button = QPushButton("取消")',
    'self.delete_rule_button = QPushButton("删除选中规则")',
    'self._rule_mode = "add"',
    'self._rule_mode = "edit"',
    'self.save_rule_button.setEnabled(active)',
    'self.cancel_rule_button.setEnabled(active)',
    'self.delete_rule_button.setEnabled(not active and selected)',
    'self.edit_rule_button.setEnabled(not active and selected)',
):
    assert token in UI, token

# During add/edit, only the active row is editable.
assert 'row_editable = editable and (target_row is None or row == target_row)' in UI
assert 'self._set_rule_table_editable(True, row)' in UI

print('Food config UI contract test passed')
