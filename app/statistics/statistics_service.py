from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.database import Database

@dataclass
class StatisticsQuery:
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    food_id: Optional[str] = None
    tray_config_id: Optional[str] = None

@dataclass
class StatisticsResult:
    event_count: int = 0
    total_remaining_weight: float = 0.0
    average_remaining_weight: float = 0.0
    remaining_rate: Optional[float] = None
    total_initial_weight: float = 0.0
    total_consumed_weight: Optional[float] = None
    consumption_rate: Optional[float] = None

@dataclass
class FoodStatistics:
    food_id: Optional[str]
    food_name: str
    count: int = 0
    total_remaining_weight: float = 0.0
    average_remaining_weight: float = 0.0
    remaining_rate: Optional[float] = None
    total_initial_weight: float = 0.0
    total_consumed_weight: Optional[float] = None
    consumption_rate: Optional[float] = None

@dataclass
class DailyStatistics:
    date: str
    event_count: int = 0
    total_remaining_weight: float = 0.0
    average_remaining_weight: float = 0.0
    total_initial_weight: float = 0.0
    total_consumed_weight: Optional[float] = None
    remaining_rate: Optional[float] = None
    consumption_rate: Optional[float] = None

class StatisticsService:
    def __init__(self, database: Database):
        self.database = database

    def get_summary(self, query: Optional[StatisticsQuery] = None) -> StatisticsResult:
        rows = self._get_event_rows(query or StatisticsQuery())
        count = len(rows)
        remaining = sum(r["total_remaining"] or 0 for r in rows)
        initial = sum(r["total_initial"] or 0 for r in rows)
        consumed = initial - remaining if initial > 0 else None
        rr = remaining / initial if initial > 0 else None
        cr = consumed / initial if initial > 0 and consumed is not None else None
        return StatisticsResult(count, round(remaining,2), round(remaining/count,2) if count else 0.0,
            round(rr,4) if rr is not None else None, round(initial,2), round(consumed,2) if consumed is not None else None,
            round(cr,4) if cr is not None else None)

    def get_food_statistics(self, query: Optional[StatisticsQuery] = None) -> list[FoodStatistics]:
        rows = self._get_cell_rows(query or StatisticsQuery())
        grouped = {}
        for r in rows:
            key = r["food_id"] or "__UNKNOWN__"
            item = grouped.setdefault(key, {"food_id":r["food_id"],"food_name":r["food_name"] or "未知","count":0,"remaining":0.0,"initial":0.0})
            item["count"] += 1; item["remaining"] += r["net_weight"] or 0; item["initial"] += r["initial_weight"] or 0
        result=[]
        for x in grouped.values():
            rr=x["remaining"]/x["initial"] if x["initial"]>0 else None
            consumed=x["initial"]-x["remaining"] if x["initial"]>0 else None
            cr=consumed/x["initial"] if consumed is not None and x["initial"]>0 else None
            result.append(FoodStatistics(x["food_id"],x["food_name"],x["count"],round(x["remaining"],2),round(x["remaining"]/x["count"],2) if x["count"] else 0,round(rr,4) if rr is not None else None,round(x["initial"],2),round(consumed,2) if consumed is not None else None,round(cr,4) if cr is not None else None))
        return sorted(result,key=lambda x:x.food_name)

    def get_daily_statistics(self, query: Optional[StatisticsQuery] = None) -> list[DailyStatistics]:
        rows=self._get_event_rows(query or StatisticsQuery()); grouped={}
        for r in rows:
            d=r["timestamp"][:10]; x=grouped.setdefault(d,{"count":0,"remaining":0.0,"initial":0.0}); x["count"]+=1; x["remaining"]+=r["total_remaining"] or 0; x["initial"]+=r["total_initial"] or 0
        out=[]
        for d,x in grouped.items():
            rr=x["remaining"]/x["initial"] if x["initial"]>0 else None; consumed=x["initial"]-x["remaining"] if x["initial"]>0 else None; cr=consumed/x["initial"] if consumed is not None and x["initial"]>0 else None
            out.append(DailyStatistics(d,x["count"],round(x["remaining"],2),round(x["remaining"]/x["count"],2) if x["count"] else 0,round(x["initial"],2),round(consumed,2) if consumed is not None else None,round(rr,4) if rr is not None else None,round(cr,4) if cr is not None else None))
        return sorted(out,key=lambda x:x.date)

    def _where(self, query):
        conditions=[]; params=[]
        if query.start_time: conditions.append("e.timestamp >= ?"); params.append(query.start_time.isoformat())
        if query.end_time: conditions.append("e.timestamp <= ?"); params.append(query.end_time.isoformat())
        if query.tray_config_id: conditions.append("e.tray_config_id = ?"); params.append(query.tray_config_id)
        if query.food_id: conditions.append("ec.food_id = ?"); params.append(query.food_id)
        return (" WHERE "+" AND ".join(conditions)) if conditions else "", params

    def _get_event_rows(self, query):
        conditions=[]; params=[]
        if query.start_time: conditions.append("e.timestamp >= ?"); params.append(query.start_time.isoformat())
        if query.end_time: conditions.append("e.timestamp <= ?"); params.append(query.end_time.isoformat())
        if query.tray_config_id: conditions.append("e.tray_config_id = ?"); params.append(query.tray_config_id)
        where=" WHERE "+" AND ".join(conditions) if conditions else ""
        sql=f'''SELECT e.event_id,e.timestamp,e.tray_config_id,COALESCE(SUM(ec.net_weight),0),COALESCE(SUM(ec.initial_weight),0) FROM event e LEFT JOIN event_cell ec ON e.event_id=ec.event_id{where} GROUP BY e.event_id,e.timestamp,e.tray_config_id ORDER BY e.timestamp'''
        with self.database._connect() as conn: rows=conn.execute(sql,params).fetchall()
        return [{"event_id":r[0],"timestamp":r[1],"tray_config_id":r[2],"total_remaining":r[3],"total_initial":r[4]} for r in rows]

    def _get_cell_rows(self, query):
        conditions=[]; params=[]
        if query.start_time: conditions.append("e.timestamp >= ?"); params.append(query.start_time.isoformat())
        if query.end_time: conditions.append("e.timestamp <= ?"); params.append(query.end_time.isoformat())
        if query.tray_config_id: conditions.append("e.tray_config_id = ?"); params.append(query.tray_config_id)
        if query.food_id: conditions.append("ec.food_id = ?"); params.append(query.food_id)
        where=" WHERE "+" AND ".join(conditions) if conditions else ""
        sql=f'''SELECT ec.food_id, f.food_name, ec.net_weight, ec.initial_weight FROM event e JOIN event_cell ec ON e.event_id=ec.event_id LEFT JOIN food f ON ec.food_id=f.food_id{where} ORDER BY e.timestamp'''
        with self.database._connect() as conn: rows=conn.execute(sql,params).fetchall()
        return [{"food_id":r[0],"food_name":r[1],"net_weight":r[2],"initial_weight":r[3]} for r in rows]
