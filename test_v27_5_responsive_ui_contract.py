from pathlib import Path

src = Path(__file__).parent / "app" / "ui" / "runtime_window.py"
text = src.read_text(encoding="utf-8")

required = [
    'subtitle = QLabel("实时检测工作台 · V27.7")',
    'left_widget.setMinimumWidth(350)',
    'left_widget.setMaximumWidth(390)',
    'action.setMinimumHeight(244)',
    'action.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)',
    'root.addLayout(body, 1)',
    'result.setMinimumHeight(150)',
    'self.photo_label.setCursor(Qt.PointingHandCursor)',
    'dialog = PhotoPreviewDialog(image_path, self)',
    'pix.scaled(',
]
for item in required:
    assert item in text, f"Missing V27.7 layout contract: {item}"

for forbidden in [
    'body_container.setMinimumHeight(360)',
    'body_container.setMaximumHeight(380)',
    'root.addWidget(body_container, 3)',
    'root.addWidget(result, 2)',
    'action.setMinimumHeight(0)',
]:
    assert forbidden not in text, f"Old compressing layout still present: {forbidden}"

print("V27.7 responsive operation-layout contract test passed")
