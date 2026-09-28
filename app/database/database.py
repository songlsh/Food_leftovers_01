import sqlite3
from pathlib import Path
from typing import Optional

from app.models.event import Event
from app.models.food import Food
from app.models.tray import TrayConfig


class Database:
    """SQLite database access layer."""

    def __init__(self, db_path: str = "data/database.db"):
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        """Create the database directory and required tables."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS event (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    tray_config_id TEXT,
                    image_path TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    menu_date TEXT,
                    menu_weekday TEXT,
                    menu_version TEXT,
                    menu_snapshot TEXT
                );

                CREATE TABLE IF NOT EXISTS event_cell (
                    event_cell_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    cell_id INTEGER NOT NULL,
                    food_id TEXT,
                    gross_weight REAL,
                    tare_weight REAL,
                    net_weight REAL,
                    initial_weight REAL,
                    weight_status TEXT NOT NULL,
                    confidence REAL,
                    recognition_status TEXT NOT NULL,
                    recognition_result_type TEXT NOT NULL DEFAULT 'FOOD',
                    FOREIGN KEY (event_id) REFERENCES event(event_id)
                );

                CREATE TABLE IF NOT EXISTS food (
                    food_id TEXT PRIMARY KEY,
                    food_name TEXT NOT NULL,
                    category TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    initial_weight REAL
                );

                CREATE TABLE IF NOT EXISTS suggestion_rule (
                    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric TEXT NOT NULL DEFAULT 'remaining_rate',
                    min_value REAL NOT NULL,
                    max_value REAL NOT NULL,
                    suggestion TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS tray_config (
                    tray_config_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    cell_count INTEGER NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS tray_cell_config (
                    tray_config_id TEXT NOT NULL,
                    cell_id INTEGER NOT NULL,
                    weight_channel INTEGER NOT NULL,
                    image_region TEXT,
                    tare_weight REAL NOT NULL DEFAULT 0,
                    PRIMARY KEY (tray_config_id, cell_id),
                    FOREIGN KEY (tray_config_id) REFERENCES tray_config(tray_config_id)
                );
                """
            )
            # Backward-compatible migration for V20-V24 databases.
            columns = {row[1] for row in conn.execute("PRAGMA table_info(food)").fetchall()}
            if "initial_weight" not in columns:
                conn.execute("ALTER TABLE food ADD COLUMN initial_weight REAL")

            event_columns = {row[1] for row in conn.execute("PRAGMA table_info(event)").fetchall()}
            for column in ("menu_date", "menu_weekday", "menu_version", "menu_snapshot"):
                if column not in event_columns:
                    conn.execute(f"ALTER TABLE event ADD COLUMN {column} TEXT")

            cell_columns = {row[1] for row in conn.execute("PRAGMA table_info(event_cell)").fetchall()}
            if "recognition_result_type" not in cell_columns:
                conn.execute("ALTER TABLE event_cell ADD COLUMN recognition_result_type TEXT NOT NULL DEFAULT 'FOOD'")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def save_event(self, event: Event) -> None:
        """Save an Event and all of its EventCells."""
        if not event.event_id:
            raise ValueError("event.event_id cannot be empty")

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO event
                (event_id, timestamp, tray_config_id, image_path, status, error_message,
                 menu_date, menu_weekday, menu_version, menu_snapshot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.tray_config_id,
                    event.image_path,
                    event.status.value,
                    event.error_message,
                    event.menu_date,
                    event.menu_weekday,
                    event.menu_version,
                    event.menu_snapshot,
                ),
            )

            conn.execute(
                "DELETE FROM event_cell WHERE event_id = ?",
                (event.event_id,),
            )

            for cell in event.cells:
                event_cell_id = cell.event_cell_id or (
                    f"{event.event_id}_C{cell.cell_id}"
                )

                conn.execute(
                    """
                    INSERT INTO event_cell
                    (
                        event_cell_id,
                        event_id,
                        cell_id,
                        food_id,
                        gross_weight,
                        tare_weight,
                        net_weight,
                        initial_weight,
                        weight_status,
                        confidence,
                        recognition_status,
                        recognition_result_type
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_cell_id,
                        event.event_id,
                        cell.cell_id,
                        cell.food_id,
                        cell.gross_weight,
                        cell.tare_weight,
                        cell.net_weight,
                        cell.initial_weight,
                        cell.weight_status.value,
                        cell.confidence,
                        cell.recognition_status.value,
                        cell.recognition_result_type,
                    ),
                )

    def get_event(self, event_id: str) -> Optional[Event]:
        """Return one Event together with its EventCells."""
        from datetime import datetime
        from app.models.enums import EventStatus, RecognitionStatus, WeightStatus
        from app.models.event import EventCell

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT event_id, timestamp, tray_config_id,
                       image_path, status, error_message,
                       menu_date, menu_weekday, menu_version, menu_snapshot
                FROM event
                WHERE event_id = ?
                """,
                (event_id,),
            ).fetchone()

            if row is None:
                return None

            cell_rows = conn.execute(
                """
                SELECT event_cell_id, event_id, cell_id, food_id,
                       gross_weight, tare_weight, net_weight, initial_weight,
                       weight_status, confidence, recognition_status, recognition_result_type
                FROM event_cell
                WHERE event_id = ?
                ORDER BY cell_id
                """,
                (event_id,),
            ).fetchall()

        cells = [
            EventCell(
                event_cell_id=r[0], event_id=r[1], cell_id=r[2], food_id=r[3],
                gross_weight=r[4], tare_weight=r[5], net_weight=r[6],
                initial_weight=r[7], weight_status=WeightStatus(r[8]),
                confidence=r[9], recognition_status=RecognitionStatus(r[10]),
                recognition_result_type=r[11],
            )
            for r in cell_rows
        ]

        return Event(
            event_id=row[0], timestamp=datetime.fromisoformat(row[1]),
            tray_config_id=row[2], image_path=row[3],
            status=EventStatus(row[4]), error_message=row[5],
            menu_date=row[6], menu_weekday=row[7], menu_version=row[8], menu_snapshot=row[9],
            cells=cells,
        )

    def get_events(self, filters=None) -> list[Event]:
        """Return event summaries with optional history filters."""
        from datetime import datetime
        from app.models.enums import EventStatus

        query = """
            SELECT event_id, timestamp, tray_config_id,
                   image_path, status, error_message
            FROM event
        """
        params = []
        conditions = []
        filters = filters or {}

        if filters.get("event_id"):
            conditions.append("event_id = ?")
            params.append(filters["event_id"])

        if filters.get("start_time") is not None:
            value = filters["start_time"]
            params.append(value.isoformat() if hasattr(value, "isoformat") else str(value))
            conditions.append("timestamp >= ?")

        if filters.get("end_time") is not None:
            value = filters["end_time"]
            params.append(value.isoformat() if hasattr(value, "isoformat") else str(value))
            conditions.append("timestamp <= ?")

        if filters.get("status"):
            status = filters["status"]
            status = status.value if isinstance(status, EventStatus) else str(status)
            conditions.append("status = ?")
            params.append(status)

        if filters.get("tray_config_id"):
            conditions.append("tray_config_id = ?")
            params.append(filters["tray_config_id"])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC"

        if filters.get("limit") is not None:
            limit = max(1, int(filters["limit"]))
            query += " LIMIT ?"
            params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            Event(
                event_id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                tray_config_id=row[2],
                image_path=row[3],
                status=EventStatus(row[4]),
                error_message=row[5],
            )
            for row in rows
        ]

    def get_foods(self) -> list[Food]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT food_id, food_name, category, enabled, initial_weight
                FROM food
                ORDER BY food_name
                """
            ).fetchall()

        return [
            Food(
                food_id=row[0],
                food_name=row[1],
                category=row[2],
                enabled=bool(row[3]),
                initial_weight=row[4],
            )
            for row in rows
        ]

    def update_food(self, food: Food) -> None:
        if not food.food_id:
            raise ValueError("food.food_id cannot be empty")
        with self._connect() as conn:
            conn.execute(
                "UPDATE food SET food_name=?, category=?, enabled=?, initial_weight=? WHERE food_id=?",
                (food.food_name, food.category, 1 if food.enabled else 0, food.initial_weight, food.food_id),
            )

    def get_suggestion_rules(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT rule_id, metric, min_value, max_value, suggestion, enabled FROM suggestion_rule ORDER BY min_value, rule_id"
            ).fetchall()
        return [dict(rule_id=r[0], metric=r[1], min_value=r[2], max_value=r[3], suggestion=r[4], enabled=bool(r[5])) for r in rows]

    def save_suggestion_rule(self, rule: dict) -> int:
        with self._connect() as conn:
            if rule.get("rule_id"):
                conn.execute("UPDATE suggestion_rule SET metric=?, min_value=?, max_value=?, suggestion=?, enabled=? WHERE rule_id=?",
                             (rule["metric"], rule["min_value"], rule["max_value"], rule["suggestion"], 1 if rule.get("enabled", True) else 0, rule["rule_id"]))
                return int(rule["rule_id"])
            cur=conn.execute("INSERT INTO suggestion_rule(metric,min_value,max_value,suggestion,enabled) VALUES(?,?,?,?,?)",
                             (rule["metric"], rule["min_value"], rule["max_value"], rule["suggestion"], 1 if rule.get("enabled", True) else 0))
            return int(cur.lastrowid)

    def delete_suggestion_rule(self, rule_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM suggestion_rule WHERE rule_id=?", (rule_id,))

    def get_tray_configs(self) -> list[TrayConfig]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT tray_config_id, name, description,
                       cell_count, enabled
                FROM tray_config
                ORDER BY name
                """
            ).fetchall()

        return [
            TrayConfig(
                tray_config_id=row[0],
                name=row[1],
                description=row[2],
                cell_count=row[3],
                enabled=bool(row[4]),
            )
            for row in rows
        ]
