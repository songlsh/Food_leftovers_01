from datetime import datetime
from app.event import EventRecord
from app.models.event import Event, EventCell

def main():
    e=Event(event_id="EV000001", timestamp=datetime(2026,9,25,12,30), cells=[EventCell(cell_id=1,food_id="F001",net_weight=298.5,confidence=.96),EventCell(cell_id=2,food_id="F002",net_weight=180.9,confidence=.91)])
    r=EventRecord.from_event(e)
    assert r.event_id=="EV000001" and r.total_weight==479.4 and len(r.cells)==2
    print("Event record test passed")
    print(f"Event ID: {r.event_id}")
    print(f"Total weight: {r.total_weight:.1f}g")

if __name__=="__main__": main()
