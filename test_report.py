from pathlib import Path
from app.models.event import Event, EventCell
from app.report import ReportGenerator

def main():
    e=Event(event_id="EV000001", cells=[EventCell(cell_id=1,food_id="F001",net_weight=298.5,confidence=.96),EventCell(cell_id=2,food_id="F002",net_weight=180.9,confidence=.91)])
    p=Path(ReportGenerator("reports_test").generate(e))
    assert p.exists()
    text=p.read_text(encoding="utf-8")
    assert "剩菜检测报告" in text and "EV000001" in text and "479.4g" in text
    print("Report test passed")
    print(f"Report: {p}")

if __name__=="__main__": main()
