from pathlib import Path
from datetime import datetime, timedelta
from app.database import Database
from app.config.seed_data import seed_foods
from app.statistics import StatisticsService, StatisticsQuery, SuggestionEngine
from app.report import ReportGenerator

ROOT=Path(__file__).resolve().parent
DB=ROOT/'data'/'test_statistics_report.db'; DB.unlink(missing_ok=True)
db=Database(str(DB)); db.initialize(); seed_foods(db)
# Use existing seeded demo data if available; otherwise verify an empty but valid workbook can be generated.
service=StatisticsService(db); q=StatisticsQuery(start_time=datetime.now()-timedelta(days=30), end_time=datetime.now()+timedelta(days=1))
out=ROOT/'reports_test'/'statistics_report_test.xlsx'; out.unlink(missing_ok=True)
suggestions=[]
for x in service.get_food_statistics(q): suggestions.extend(f"{x.food_name}：{z}" for z in SuggestionEngine(db).match(x.remaining_rate))
p=Path(ReportGenerator(out.parent).generate_statistics_xlsx(service,q,suggestions,out))
assert p.exists() and p.stat().st_size>1000
from openpyxl import load_workbook
wb=load_workbook(p, read_only=True, data_only=True)
assert wb.sheetnames==['统计总览','食物统计','每日统计']
assert wb['统计总览']['A1'].value=='剩菜统计分析报告'
print('Statistics Excel report test passed')
print(f'Report: {p}')
