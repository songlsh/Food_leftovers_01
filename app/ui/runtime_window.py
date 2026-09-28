from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QDialog, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget, QSizePolicy,
)

from app.detection import DetectionService
from app.history import HistoryService
from app.devices import MockDeviceBundle

_STATE_LABELS = {
    DetectionService.WAITING: "等待餐盘",
    DetectionService.TRAY_PRESENT: "检测到餐盘",
    DetectionService.STABILIZING: "重量稳定中",
    DetectionService.READY: "已就绪，准备检测",
    DetectionService.TRIGGERED: "已触发检测",
    DetectionService.PROCESSING: "检测处理中",
    DetectionService.COMPLETED: "检测完成",
    DetectionService.PARTIAL: "部分完成",
    DetectionService.FAILED: "检测失败",
    DetectionService.WAITING_FOR_REMOVAL: "等待取走餐盘",
    DetectionService.STOPPED: "已停止",
}

APP_QSS = """
QMainWindow, QWidget {
    background: #f4f6f8;
    color: #243447;
    font-family: "PingFang SC", "Helvetica Neue", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}
QLabel#pageTitle {
    font-size: 24px;
    font-weight: 700;
    color: #172b3a;
}
QLabel#pageSubtitle {
    color: #7a8794;
    font-size: 12px;
}
QFrame#statusCard, QFrame#weightCard, QFrame#photoCard, QFrame#resultCard, QFrame#actionCard {
    background: #ffffff;
    border: 1px solid #e3e8ed;
    border-radius: 12px;
}
QFrame#metricCell {
    background: #f8fafc;
    border: 1px solid #edf1f4;
    border-radius: 8px;
}
QLabel#metricTitle {
    color: #7b8794;
    font-size: 11px;
}
QLabel#metricValue {
    color: #253746;
    font-size: 14px;
    font-weight: 650;
}
QLabel#metricValue[state="good"] { color: #16734a; }
QLabel#metricValue[state="accent"] { color: #1769aa; }
QLabel#sectionTitle {
    font-size: 15px;
    font-weight: 700;
    color: #253746;
}
QLabel#smallTitle {
    color: #7a8794;
    font-size: 12px;
}
QLabel#stateValue {
    font-size: 15px;
    font-weight: 700;
    color: #1769aa;
}
QLabel#weightValue {
    font-size: 19px;
    font-weight: 650;
    color: #145b87;
}
QLabel#totalCaption {
    color: #64748b;
    font-size: 12px;
}
QLabel#totalValue {
    font-size: 18px;
    font-weight: 700;
    color: #243447;
}
QLabel#photoPlaceholder {
    border: 1px dashed #cbd5df;
    border-radius: 9px;
    background: #f8fafc;
    color: #8492a0;
    font-size: 13px;
}
QLabel#resultSummary {
    color: #526273;
    font-size: 12px;
    padding: 4px 2px 8px 2px;
}
QPushButton {
    min-height: 36px;
    padding: 0 14px;
    border-radius: 7px;
    border: 1px solid #d5dce3;
    background: #ffffff;
    color: #344454;
    font-size: 13px;
}
QPushButton:hover {
    background: #f5f8fb;
    border-color: #bfc9d3;
}
QPushButton:pressed { background: #edf2f6; }
QPushButton:disabled {
    color: #a2acb6;
    background: #f0f2f4;
    border-color: #e1e5e8;
}
QPushButton#primaryButton {
    min-height: 40px;
    background: #1677d2;
    color: white;
    border: 0;
    font-weight: 650;
}
QPushButton#primaryButton:hover { background: #1268ba; }
QPushButton#dangerButton {
    min-height: 40px;
    background: #ffffff;
    color: #b42318;
    border: 1px solid #e7b7b2;
    font-weight: 600;
}
QPushButton#dangerButton:hover { background: #fff6f5; }
QPushButton#secondaryButton {
    min-height: 34px;
    background: #f8fafc;
    color: #5d6b78;
    border-color: #e1e7ec;
    font-size: 12px;
}
QPushButton#navButton {
    min-height: 34px;
    background: #ffffff;
    border-color: #d7dee6;
    color: #435466;
}
QPushButton#configButton {
    min-height: 36px;
    background: #f6f9fc;
    color: #365a78;
    font-weight: 600;
}
QPushButton#testToggleButton {
    min-height: 30px;
    padding: 0 10px;
    background: #f8fafc;
    color: #7a8794;
    border: 1px solid #e5e9ee;
    font-size: 11px;
    font-weight: 500;
    text-align: left;
}
QPushButton#testToggleButton:hover {
    background: #f1f5f8;
    color: #526273;
}
QFrame#testPanel {
    background: #fafbfc;
    border: 1px dashed #d9e0e7;
    border-radius: 8px;
}
QScrollArea#testScroll {
    background: transparent;
    border: 0;
}
QTableWidget {
    background: #ffffff;
    border: 1px solid #e3e8ed;
    border-radius: 8px;
    gridline-color: #e9edf1;
    alternate-background-color: #f8fafc;
    selection-background-color: #e8f2fb;
    selection-color: #243447;
    font-size: 12px;
}
QTableWidget::item { padding: 6px; }
QHeaderView::section {
    background: #f5f7f9;
    color: #5d6b78;
    border: 0;
    border-bottom: 1px solid #e1e7ec;
    padding: 8px 6px;
    font-size: 12px;
    font-weight: 650;
}
"""


class PhotoPreviewDialog(QDialog):
    """Click-to-enlarge preview for the current detection photo."""

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("检测照片 - 大图查看")
        self.setModal(True)
        self.setMinimumSize(640, 480)
        self.resize(1000, 700)
        self._pixmap = QPixmap(image_path)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "background:#f8fafc;border:1px solid #e3e8ed;border-radius:8px;"
        )
        layout.addWidget(self.image_label, 1)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, 0, Qt.AlignRight)
        self._refresh_image()

    def _refresh_image(self):
        if self._pixmap.isNull():
            self.image_label.setText("无法读取照片")
            return
        size = self.image_label.size()
        self.image_label.setPixmap(
            self._pixmap.scaled(
                max(1, size.width() - 12),
                max(1, size.height() - 12),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_image()


class RuntimeWindow(QMainWindow):
    """Product-style runtime dashboard while retaining the V25 workflow."""

    def __init__(self, service: DetectionService, history_service: HistoryService,
                 db_path: Path, device_bundle: MockDeviceBundle | None = None, parent=None):
        super().__init__(parent)
        self.service = service
        self.history_service = history_service
        self.db_path = db_path
        self.device_bundle = device_bundle
        self.weight_device = device_bundle.weight if device_bundle else None
        self.camera_device = device_bundle.camera if device_bundle else None
        self.device_manager = device_bundle.manager if device_bundle else None
        self._demo_active = False
        self._demo_phase = None
        self._demo_index = 0
        self._weights = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        self._current_photo_path = None
        self._target_weights = {1: 300.0, 2: 182.0, 3: 252.0, 4: 103.0}
        self._place_factors = [0.00, 0.08, 0.20, 0.38, 0.58, 0.76, 0.90, 1.00, 1.00, 1.00, 1.00, 1.00]
        self._remove_factors = [1.00, 0.82, 0.62, 0.42, 0.24, 0.10, 0.03, 0.00, 0.00, 0.00, 0.00]
        self.setWindowTitle("剩菜检测系统 - 实时检测")
        self.resize(1280, 820)
        # Cross-platform minimum: keep the formal controls intact on common
        # Windows 1366x768 / 125% DPI and Mac notebook layouts. The window
        # remains freely resizable above this boundary; we never compress
        # buttons below their usable size.
        self.setMinimumSize(1000, 720)
        self.setStyleSheet(APP_QSS)
        self._build_ui()
        self._load_latest_event()
        self._refresh_view()
        self.demo_timer = QTimer(self); self.demo_timer.setInterval(350); self.demo_timer.timeout.connect(self._demo_tick)
        self.refresh_timer = QTimer(self); self.refresh_timer.setInterval(1000); self.refresh_timer.timeout.connect(self._refresh_view); self.refresh_timer.start()

    def _card(self, object_name):
        f = QFrame(); f.setObjectName(object_name); return f

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)
        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title = QLabel("剩菜检测系统")
        title.setObjectName("pageTitle")
        subtitle = QLabel("实时检测工作台 · V27.7")
        subtitle.setObjectName("pageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        self.running_badge = QLabel("● 已停止")
        self.running_badge.setAlignment(Qt.AlignCenter)
        header.addWidget(self.running_badge)
        root.addLayout(header, 0)

        # Status overview: compact and stable; it should not steal space from
        # the operation area when the window becomes shorter.
        status = self._card("statusCard")
        sg = QGridLayout(status)
        sg.setContentsMargins(9, 8, 9, 8)
        sg.setHorizontalSpacing(7)
        sg.setVerticalSpacing(6)
        self.state_label = QLabel("等待餐盘")
        self.state_label.setObjectName("metricValue")
        self.state_label.setProperty("state", "accent")
        self.event_id_label = QLabel("暂无")
        self.event_id_label.setObjectName("metricValue")
        self.weight_device_label = QLabel("-")
        self.weight_device_label.setObjectName("metricValue")
        self.camera_device_label = QLabel("-")
        self.camera_device_label.setObjectName("metricValue")
        self.ai_device_label = QLabel("Mock / OK")
        self.ai_device_label.setObjectName("metricValue")
        self.database_label = QLabel("正常")
        self.database_label.setObjectName("metricValue")
        self.device_mode_label = QLabel("Mock")
        self.device_mode_label.setObjectName("metricValue")
        status_items = [
            ("检测状态", self.state_label, 0, 0),
            ("最近 Event", self.event_id_label, 0, 1),
            ("称重设备", self.weight_device_label, 0, 2),
            ("摄像头", self.camera_device_label, 0, 3),
            ("AI 检测", self.ai_device_label, 1, 0),
            ("数据库", self.database_label, 1, 1),
            ("设备模式", self.device_mode_label, 1, 2),
        ]
        for title_text, value_widget, row, col in status_items:
            cell = QFrame()
            cell.setObjectName("metricCell")
            cell.setMinimumHeight(43)
            layout = QVBoxLayout(cell)
            layout.setContentsMargins(9, 5, 9, 5)
            layout.setSpacing(1)
            label = QLabel(title_text)
            label.setObjectName("metricTitle")
            layout.addWidget(label)
            layout.addWidget(value_widget)
            sg.addWidget(cell, row, col)
        sg.setColumnStretch(0, 1)
        sg.setColumnStretch(1, 1)
        sg.setColumnStretch(2, 1)
        sg.setColumnStretch(3, 1)
        root.addWidget(status, 0)

        # Main workspace. The left column is content-driven and protected from
        # vertical compression; the right photo column takes remaining width.
        body = QHBoxLayout()
        body.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(10)
        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setMinimumWidth(350)
        left_widget.setMaximumWidth(390)
        left_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Weight card: compact, predictable height.
        weight_box = self._card("weightCard")
        wg = QGridLayout(weight_box)
        wg.setContentsMargins(12, 10, 12, 10)
        wg.setHorizontalSpacing(9)
        wg.setVerticalSpacing(5)
        wg.addWidget(self._section("当前餐盘重量"), 0, 0, 1, 4)
        self.weight_labels = {}
        for cid in range(1, 5):
            r = 1 + (cid - 1) // 2
            c = ((cid - 1) % 2) * 2
            wg.addWidget(self._small_label(f"格位 {cid}"), r, c)
            lab = QLabel("0.00 g")
            lab.setObjectName("weightValue")
            self.weight_labels[cid] = lab
            wg.addWidget(lab, r, c + 1)
        total_caption = QLabel("当前总重量")
        total_caption.setObjectName("totalCaption")
        wg.addWidget(total_caption, 3, 0)
        self.total_weight_label = QLabel("0.00 g")
        self.total_weight_label.setObjectName("totalValue")
        wg.addWidget(self.total_weight_label, 3, 1, 1, 3)
        weight_box.setMinimumHeight(122)
        weight_box.setMaximumHeight(136)
        left.addWidget(weight_box, 0)

        # Formal operation card. It has an explicit minimum height so its
        # controls can never be squeezed into overlapping rows.
        action = self._card("actionCard")
        ag = QVBoxLayout(action)
        ag.setContentsMargins(12, 10, 12, 10)
        ag.setSpacing(6)
        ag.addWidget(self._section("操作"), 0)

        self.start_button = QPushButton("开始监测")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self._start_monitoring)
        self.stop_button = QPushButton("停止监测")
        self.stop_button.setObjectName("dangerButton")
        self.stop_button.clicked.connect(self._stop_monitoring)
        monitor_row = QHBoxLayout()
        monitor_row.setSpacing(8)
        monitor_row.setContentsMargins(0, 0, 0, 0)
        monitor_row.addWidget(self.start_button, 1)
        monitor_row.addWidget(self.stop_button, 1)
        ag.addLayout(monitor_row, 0)

        ag.addWidget(self._small_label("数据与记录"), 0)
        # UI contract legacy label: "打开历史记录"; visible production label is shorter.
        self.history_button = QPushButton("历史记录")
        self.history_button.setObjectName("navButton")
        self.history_button.clicked.connect(self._open_history)
        # UI contract legacy label: "打开统计分析"; visible production label is shorter.
        self.statistics_button = QPushButton("统计分析")
        self.statistics_button.setObjectName("navButton")
        self.statistics_button.clicked.connect(self._open_statistics)
        data_row = QHBoxLayout()
        data_row.setSpacing(8)
        data_row.setContentsMargins(0, 0, 0, 0)
        data_row.addWidget(self.history_button, 1)
        data_row.addWidget(self.statistics_button, 1)
        ag.addLayout(data_row, 0)

        self.config_button = QPushButton("系统配置")
        self.config_button.setObjectName("configButton")
        self.config_button.clicked.connect(self._open_config)
        ag.addWidget(self.config_button, 0)

        ag.addWidget(self._small_label("开发测试"), 0)
        self.test_toggle = QPushButton("▶ 开发测试工具")
        self.test_toggle.setObjectName("testToggleButton")
        self.test_toggle.setCheckable(True)
        self.test_toggle.clicked.connect(self._toggle_test_tools)
        ag.addWidget(self.test_toggle, 0)

        self.test_panel = QFrame()
        self.test_panel.setObjectName("testPanel")
        test_layout = QVBoxLayout(self.test_panel)
        test_layout.setContentsMargins(8, 6, 8, 6)
        test_layout.setSpacing(5)
        test_label = self._small_label("Mock 餐盘模拟（真实硬件接入后可移除）")
        test_layout.addWidget(test_label)
        self.place_button = QPushButton("模拟放入餐盘")
        self.place_button.setObjectName("secondaryButton")
        self.place_button.clicked.connect(self._simulate_place)
        self.remove_button = QPushButton("模拟取走餐盘")
        self.remove_button.setObjectName("secondaryButton")
        self.remove_button.clicked.connect(self._simulate_remove)
        test_row = QHBoxLayout()
        test_row.setSpacing(6)
        test_row.setContentsMargins(0, 0, 0, 0)
        test_row.addWidget(self.place_button, 1)
        test_row.addWidget(self.remove_button, 1)
        test_layout.addLayout(test_row)

        self.test_scroll = QScrollArea()
        self.test_scroll.setObjectName("testScroll")
        self.test_scroll.setWidgetResizable(True)
        self.test_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.test_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.test_scroll.setFrameShape(QFrame.NoFrame)
        self.test_scroll.setMaximumHeight(82)
        self.test_scroll.setWidget(self.test_panel)
        self.test_scroll.setVisible(False)
        ag.addWidget(self.test_scroll, 0)

        # The action card is never stretched; its contents determine its
        # height. This is the key difference from the previous broken layout.
        action.setMinimumHeight(244)
        action.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        left.addWidget(action, 0)
        left.addStretch(1)

        body.addWidget(left_widget, 0)

        # Photo card: compact preview, with click-to-enlarge for the original.
        right = self._card("photoCard")
        rg = QVBoxLayout(right)
        rg.setContentsMargins(12, 10, 12, 10)
        rg.setSpacing(7)
        rg.addWidget(self._section("当前检测照片"), 0)
        self.photo_label = QLabel("等待检测后显示照片")
        self.photo_label.setObjectName("photoPlaceholder")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setMinimumSize(260, 160)
        self.photo_label.setMaximumSize(560, 280)
        self.photo_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.photo_label.setCursor(Qt.PointingHandCursor)
        self.photo_label.mousePressEvent = self._photo_clicked
        rg.addWidget(self.photo_label, 1, Qt.AlignCenter)
        self.photo_hint = QLabel("点击照片查看大图；统计页面不加载照片，历史记录按需查看")
        self.photo_hint.setObjectName("pageSubtitle")
        self.photo_hint.setAlignment(Qt.AlignCenter)
        rg.addWidget(self.photo_hint, 0)
        body.addWidget(right, 1)

        # The workspace gets only the space that remains after the fixed header
        # and status cards. It is never given a hard-coded height.
        root.addLayout(body, 1)

        # Recent result uses the remaining lower area. The table itself can
        # scroll internally if the window is made smaller.
        result = self._card("resultCard")
        rl = QVBoxLayout(result)
        rl.setContentsMargins(12, 10, 12, 10)
        rl.setSpacing(3)
        rl.addWidget(self._section("最近检测结果"), 0)
        self.recent_summary = QLabel("尚未产生检测 Event")
        self.recent_summary.setObjectName("resultSummary")
        self.recent_summary.setWordWrap(True)
        rl.addWidget(self.recent_summary, 0)
        self.cells_table = QTableWidget(0, 8)
        self.cells_table.setHorizontalHeaderLabels(["格位", "食物 ID", "净重量(g)", "初始(g)", "剩余(g)", "消耗(g)", "剩余率", "AI 置信度"])
        self.cells_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cells_table.setSelectionMode(QTableWidget.NoSelection)
        self.cells_table.setAlternatingRowColors(True)
        self.cells_table.verticalHeader().setVisible(False)
        self.cells_table.horizontalHeader().setStretchLastSection(True)
        self.cells_table.horizontalHeader().setDefaultSectionSize(105)
        self.cells_table.setMinimumHeight(125)
        self.cells_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        rl.addWidget(self.cells_table, 1)
        result.setMinimumHeight(150)
        result.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(result, 1)
        self.setCentralWidget(central)
    @staticmethod
    def _small_label(text):
        x=QLabel(text); x.setObjectName("smallTitle"); return x
    @staticmethod
    def _section(text):
        x=QLabel(text); x.setObjectName("sectionTitle"); return x

    def _toggle_test_tools(self, checked):
        self.test_scroll.setVisible(checked)
        self.test_toggle.setText("▼ 开发测试工具" if checked else "▶ 开发测试工具")

    def _start_monitoring(self): self.service.start(); self._refresh_view()
    def _stop_monitoring(self):
        self.demo_timer.stop(); self._demo_active=False; self._demo_phase=None; self.service.stop(); self._refresh_view()
    def _simulate_place(self):
        if self.service.get_state()==DetectionService.STOPPED: QMessageBox.information(self,"提示","请先点击“开始监测”。"); return
        if self.service.get_state()!=DetectionService.WAITING or self._demo_active: QMessageBox.information(self,"提示","当前还在处理上一只餐盘，请先完成取走流程。"); return
        self._demo_phase="placing"; self._demo_index=0; self._demo_active=True; self.demo_timer.start(); self._refresh_view()
    def _simulate_remove(self):
        if self.service.get_state()!=DetectionService.WAITING_FOR_REMOVAL: QMessageBox.information(self,"提示","只有检测完成并等待取走餐盘时才能执行此操作。"); return
        self._demo_phase="removing"; self._demo_index=0; self._demo_active=True; self.demo_timer.start(); self._refresh_view()
    def _demo_tick(self):
        if not self._demo_active or self._demo_phase is None: return
        factors=self._place_factors if self._demo_phase=="placing" else self._remove_factors; factor=factors[min(self._demo_index,len(factors)-1)]
        self._weights={cid:round(weight*factor,2) for cid,weight in self._target_weights.items()}; event=self.service.update(self._weights); self._demo_index+=1
        if event is not None:
            self._demo_active=False; self._demo_phase=None; self.demo_timer.stop(); self._show_event(event)
        elif self._demo_phase=="removing" and self.service.get_state()==DetectionService.WAITING:
            self._demo_active=False; self._demo_phase=None; self.demo_timer.stop(); self._weights={1:0.0,2:0.0,3:0.0,4:0.0}
        elif self._demo_index>=len(factors): self._demo_index=len(factors)-1
        self._refresh_view()

    def _show_event(self,event):
        total=sum(c.net_weight or 0 for c in event.cells); self.event_id_label.setText(event.event_id or "-")
        self.recent_summary.setText(f"Event：{event.event_id}    时间：{event.timestamp:%Y-%m-%d %H:%M:%S}\n状态：{event.status.value}    总净重量：{total:.2f} g\n图片：{event.image_path or '-'}")
        self._current_photo_path = event.image_path
        self._update_photo_display()
        self.cells_table.setRowCount(0)
        for cell in event.cells:
            row=self.cells_table.rowCount(); self.cells_table.insertRow(row); initial=cell.initial_weight; remaining=cell.net_weight; consumed=(initial-remaining) if initial is not None and remaining is not None else None; rate=(remaining/initial) if initial and remaining is not None else None
            vals=[str(cell.cell_id),cell.food_id or "-",f"{remaining:.2f}" if remaining is not None else "-",f"{initial:.2f}" if initial is not None else "-",f"{remaining:.2f}" if remaining is not None else "-",f"{consumed:.2f}" if consumed is not None else "-",f"{rate:.1%}" if rate is not None else "-",f"{cell.confidence:.1%}" if cell.confidence is not None else "-"]
            for col,value in enumerate(vals): self.cells_table.setItem(row,col,QTableWidgetItem(value))

    def _photo_clicked(self, event):
        if event.button() != Qt.LeftButton:
            return
        image_path = self._current_photo_path
        if image_path and Path(image_path).exists():
            dialog = PhotoPreviewDialog(image_path, self)
            dialog.exec()

    def _update_photo_display(self):
        image_path = self._current_photo_path
        if image_path and Path(image_path).exists():
            pix = QPixmap(image_path)
            if not pix.isNull():
                size = self.photo_label.size()
                self.photo_label.setPixmap(
                    pix.scaled(
                        max(1, size.width() - 8),
                        max(1, size.height() - 8),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
                return
            self.photo_label.setText(f"无法读取照片：{image_path}")
        else:
            self.photo_label.setText(f"照片暂不可用：{image_path or '-'}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "photo_label"):
            self._update_photo_display()

    def _load_latest_event(self):
        try: events=self.history_service.list_events()
        except Exception: events=[]
        if events: self._show_event(events[0])
    def _refresh_view(self):
        state=self.service.get_state(); self.state_label.setText(_STATE_LABELS.get(state,state))
        running=state!=DetectionService.STOPPED; self.running_badge.setText("● 运行中" if running else "● 已停止"); self.running_badge.setStyleSheet("padding:7px 12px;border-radius:15px;font-weight:600;background:#ecfdf3;color:#087443;border:1px solid #b7ebc6;" if running else "padding:7px 12px;border-radius:15px;font-weight:600;background:#fff;color:#667085;border:1px solid #d7dde3;")
        for cid,value in self._weights.items(): self.weight_labels[cid].setText(f"{value:.2f} g")
        self.total_weight_label.setText(f"{sum(self._weights.values()):.2f} g")
        self.start_button.setEnabled(state==DetectionService.STOPPED); self.stop_button.setEnabled(state!=DetectionService.STOPPED); self.place_button.setEnabled(state==DetectionService.WAITING and not self._demo_active); self.remove_button.setEnabled(state==DetectionService.WAITING_FOR_REMOVAL)
        if self.device_manager is not None:
            info=self.device_manager.get_info_map(); weight=info.get("称重设备"); camera=info.get("摄像头")
            self.weight_device_label.setText(f"{weight.mode} / {weight.status}" if weight else "未配置"); self.camera_device_label.setText(f"{camera.mode} / {camera.status}" if camera else "未配置")
        else: self.weight_device_label.setText("未配置"); self.camera_device_label.setText("未配置")
        if self.device_manager is not None:
            modes = {item.mode for item in self.device_manager.get_info_map().values()}
            self.device_mode_label.setText(" / ".join(sorted(modes)) if modes else "未配置")
        else:
            self.device_mode_label.setText("未配置")
        self.ai_device_label.setText("Mock / OK"); self.database_label.setText("正常")

    def _open_config(self):
        from app.ui.system_config_window import SystemConfigWindow
        self.config_window=SystemConfigWindow(self); self.config_window.show(); self.config_window.raise_(); self.config_window.activateWindow()
    def _open_history(self):
        from app.ui.history_window import HistoryWindow
        self.history_window=HistoryWindow(self.history_service); self.history_window.show(); self.history_window.raise_(); self.history_window.activateWindow()
    def _open_statistics(self):
        from app.database import Database
        from app.statistics import StatisticsService
        from app.ui.statistics_window import StatisticsWindow
        database=Database(str(self.db_path)); database.initialize(); self.statistics_window=StatisticsWindow(StatisticsService(database)); self.statistics_window.show(); self.statistics_window.raise_(); self.statistics_window.activateWindow()
