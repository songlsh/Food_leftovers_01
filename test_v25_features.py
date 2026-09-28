from pathlib import Path
from app.database import Database
from app.config.seed_data import seed_foods
from app.statistics import StatisticsService, SuggestionEngine
from app.ai import AIRecognizer
from app.detection import DetectionService, MeasurementManager
from app.devices import MockCamera

ROOT=Path(__file__).resolve().parent
DB=ROOT/'data'/'test_v25_features.db'; DB.unlink(missing_ok=True)
IMG=ROOT/'images'/'test_v25_features'; IMG.mkdir(parents=True,exist_ok=True)
for p in IMG.glob('*'): p.unlink()

db=Database(str(DB)); db.initialize(); seed_foods(db)
foods={f.food_id:f for f in db.get_foods()}
assert foods['F001'].initial_weight==300.0
assert len(db.get_suggestion_rules())>=3

m=MeasurementManager(filter_window=5,stability_threshold=2.0,stability_samples=3); ai=AIRecognizer(); ai.load_model()
svc=DetectionService(m,ai,db,camera=MockCamera(str(IMG)),presence_threshold=100,removal_threshold=20)
e=None
for _ in range(8): e=svc.update({1:300,2:182,3:252,4:103}) or e
assert e is not None
assert all(c.initial_weight is not None for c in e.cells)
assert Path(e.image_path).exists()
assert b'MOCK_CAMERA_IMAGE' in Path(e.image_path).read_bytes()
full=db.get_event(e.event_id); assert full.cells[0].initial_weight==300.0
stats=StatisticsService(db).get_summary(); assert stats.total_initial_weight==980.0; assert stats.total_consumed_weight==143.0
assert stats.remaining_rate is not None and stats.consumption_rate is not None
assert SuggestionEngine(db).match(stats.remaining_rate)
print('V25 feature test passed')
print(f'Initial={stats.total_initial_weight:.1f}g Remaining={stats.total_remaining_weight:.1f}g Consumed={stats.total_consumed_weight:.1f}g')
print(f'Remaining rate={stats.remaining_rate:.1%} Consumption rate={stats.consumption_rate:.1%}')
