from __future__ import annotations

from datetime import datetime, time
from pathlib import Path

from app.history import HistoryQuery, HistoryService
from app.models.enums import EventStatus
from app.models.event import Event

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDateEdit,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover - exercised only without Qt
    raise ImportError(
        "PySide6 is required for the history UI. Install it with "
        "python3 -m pip install -r requirements.txt"
    ) from exc


_STATUS_LABELS = {
    "": "全部",
    EventStatus.CREATED.value: "已创建",
    EventStatus.PROCESSING.value: "处理中",
    EventStatus.COMPLETED.value: "已完成",
    EventStatus.PARTIAL.value: "部分完成",
    EventStatus.FAILED.value: "失败",
}


class HistoryWindow(QMainWindow):
    """Simple history browser backed exclusively by HistoryService."""

    def __init__(self, history_service: HistoryService, parent=None):
        super().__init__(parent)
        self.history_service = history_service
        self._events: list[Event] = []
        self.setWindowTitle("剩菜检测系统 - 历史记录")
        self.resize(1100, 700)
        self._build_ui()
        self._load_events()

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)

        filters = QGroupBox("查询条件")
        form = QFormLayout(filters)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)

        # QDateEdit without an explicit date starts from Qt's default date
        # (2000-01-01). The previous implementation subtracted 30 days from
        # that value, which produced 1999-12-02 and made every initial query
        # miss current history. Keep the defaults anchored to today's date.
        self._set_default_date_range()

        self.status_combo = QComboBox()
        for value, label in _STATUS_LABELS.items():
            self.status_combo.addItem(label, value)

        self.event_id_edit = QLineEdit()
        self.event_id_edit.setPlaceholderText("可选，例如 EV000001")

        form.addRow("开始日期", self.start_date)
        form.addRow("结束日期", self.end_date)
        form.addRow("状态", self.status_combo)
        form.addRow("Event ID", self.event_id_edit)

        self.completed_only = QCheckBox("仅显示已完成")
        self.completed_only.toggled.connect(self._completed_toggled)

        search_button = QPushButton("查询")
        search_button.clicked.connect(self._load_events)
        reset_button = QPushButton("重置")
        reset_button.clicked.connect(self._reset_filters)

        buttons = QHBoxLayout()
        buttons.addWidget(self.completed_only)
        buttons.addStretch()
        buttons.addWidget(reset_button)
        buttons.addWidget(search_button)
        form.addRow(buttons)
        root.addWidget(filters)

        splitter = QSplitter(Qt.Horizontal)
        self.event_list = QListWidget()
        self.event_list.currentItemChanged.connect(self._event_selected)
        splitter.addWidget(self.event_list)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        self.detail_title = QLabel("请选择一条历史记录")
        self.detail_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        detail_layout.addWidget(self.detail_title)

        self.summary_label = QLabel("-")
        self.summary_label.setWordWrap(True)
        detail_layout.addWidget(self.summary_label)

        self.cells_table = QTableWidget(0, 4)
        self.cells_table.setHorizontalHeaderLabels(["格位", "食物 ID", "净重量(g)", "AI 置信度"])
        self.cells_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cells_table.horizontalHeader().setStretchLastSection(True)
        detail_layout.addWidget(self.cells_table)

        self.image_label = QLabel("图片：未加载（点击按钮查看）")
        self.image_label.setWordWrap(True)
        detail_layout.addWidget(self.image_label)
        self.view_photo_button = QPushButton("查看本次照片")
        self.view_photo_button.clicked.connect(self._view_photo)
        self.view_photo_button.setEnabled(False)
        detail_layout.addWidget(self.view_photo_button)

        splitter.addWidget(detail)
        splitter.setSizes([360, 700])
        root.addWidget(splitter, 1)
        self.setCentralWidget(central)

    def _completed_toggled(self, checked: bool):
        if checked:
            self.status_combo.setCurrentIndex(
                self.status_combo.findData(EventStatus.COMPLETED.value)
            )
        elif self.status_combo.currentData() == EventStatus.COMPLETED.value:
            self.status_combo.setCurrentIndex(0)

    def _date_range(self):
        start = self.start_date.date().toPython()
        end = self.end_date.date().toPython()
        return (
            datetime.combine(start, time.min),
            datetime.combine(end, time.max),
        )

    def _load_events(self):
        try:
            start, end = self._date_range()
            status_value = self.status_combo.currentData()
            if self.completed_only.isChecked():
                status_value = EventStatus.COMPLETED.value
            status = EventStatus(status_value) if status_value else None
            query = HistoryQuery(
                event_id=self.event_id_edit.text().strip() or None,
                start_time=start,
                end_time=end,
                status=status,
            )
            self._events = self.history_service.list_events(query)
        except Exception as exc:
            QMessageBox.critical(self, "查询失败", str(exc))
            return

        self.event_list.clear()
        for event in self._events:
            item = QListWidgetItem(self._event_text(event))
            item.setData(Qt.UserRole, event.event_id)
            self.event_list.addItem(item)

        if self._events:
            self.event_list.setCurrentRow(0)
        else:
            self._clear_detail()

    @staticmethod
    def _event_text(event: Event) -> str:
        total = round(sum(c.net_weight or 0 for c in event.cells), 2)
        event_id = event.event_id or "-"
        return f"{event.timestamp:%Y-%m-%d %H:%M:%S} | {event_id} | {event.status.value} | {total:.2f} g"

    def _event_selected(self, current, previous):
        if current is None:
            self._clear_detail()
            return
        event_id = current.data(Qt.UserRole)
        event = self.history_service.get_event(event_id)
        if event is None:
            self._clear_detail()
            return
        self._show_event(event)

    def _show_event(self, event: Event):
        total = round(sum(c.net_weight or 0 for c in event.cells), 2)
        self.detail_title.setText(event.event_id or "未命名事件")
        self.summary_label.setText(
            f"时间：{event.timestamp:%Y-%m-%d %H:%M:%S}\n"
            f"状态：{_STATUS_LABELS.get(event.status.value, event.status.value)}\n"
            f"托盘配置：{event.tray_config_id or '-'}\n"
            f"总净重量：{total:.2f} g\n"
            f"错误信息：{event.error_message or '-'}"
        )

        self.cells_table.setRowCount(0)
        for cell in event.cells:
            row = self.cells_table.rowCount()
            self.cells_table.insertRow(row)
            values = [
                str(cell.cell_id),
                cell.food_id or "-",
                f"{cell.net_weight:.2f}" if cell.net_weight is not None else "-",
                f"{cell.confidence:.1%}" if cell.confidence is not None else "-",
            ]
            for col, value in enumerate(values):
                self.cells_table.setItem(row, col, QTableWidgetItem(value))

        self._current_image_path = event.image_path
        self.image_label.setText(f"图片：{event.image_path or '-'}（默认不加载）")
        self.view_photo_button.setEnabled(bool(event.image_path))

    def _view_photo(self):
        from PySide6.QtGui import QPixmap
        path=getattr(self,"_current_image_path",None)
        if not path or not Path(path).exists():
            QMessageBox.information(self,"提示","照片文件不存在。")
            return
        pix=QPixmap(path)
        if pix.isNull():
            QMessageBox.information(self,"提示","照片无法读取。")
            return
        w=QDialog(self); w.setWindowTitle("本次检测照片"); w.resize(760,520); l=QVBoxLayout(w); lab=QLabel(); lab.setAlignment(Qt.AlignCenter); lab.setPixmap(pix.scaled(720,460,Qt.KeepAspectRatio,Qt.SmoothTransformation)); l.addWidget(lab); w.exec()

    def _clear_detail(self):
        self.detail_title.setText("请选择一条历史记录")
        self.summary_label.setText("-")
        self.cells_table.setRowCount(0)
        self.image_label.setText("图片：未加载（点击按钮查看）")
        self.view_photo_button.setEnabled(False)
        self._current_image_path = None

    def _set_default_date_range(self):
        """Set the history window to the last 30 calendar days through today."""
        today = self.end_date.date().currentDate()
        self.start_date.setDate(today.addDays(-30))
        self.end_date.setDate(today)

    def _reset_filters(self):
        # Reset must be idempotent: repeated clicks should not keep moving the
        # start date backwards by another 30 days.
        self._set_default_date_range()
        self.status_combo.setCurrentIndex(0)
        self.completed_only.setChecked(False)
        self.event_id_edit.clear()
        self._load_events()
