import json
import sqlite3
from typing import Optional

from app.models.tray import TrayCellConfig, TrayConfig


class TrayConfigManager:
    """Save and load tray configuration using SQLite."""

    def __init__(self, database_path: str = "data/tray_config.db"):
        self.database_path = database_path

    def initialize(self) -> None:
        conn = sqlite3.connect(self.database_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tray_config (
                    tray_config_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    cell_count INTEGER NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tray_cell_config (
                    tray_config_id TEXT NOT NULL,
                    cell_id INTEGER NOT NULL,
                    weight_channel INTEGER NOT NULL,
                    image_region TEXT,
                    tare_weight REAL NOT NULL DEFAULT 0,
                    PRIMARY KEY (tray_config_id, cell_id),
                    FOREIGN KEY (tray_config_id)
                        REFERENCES tray_config(tray_config_id)
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def save(self, config: TrayConfig) -> None:
        self.initialize()
        conn = sqlite3.connect(self.database_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO tray_config
                (tray_config_id, name, description, cell_count, enabled)
                VALUES (?, ?, ?, ?, ?)
            """, (
                config.tray_config_id,
                config.name,
                config.description,
                config.cell_count,
                1 if config.enabled else 0,
            ))

            conn.execute(
                "DELETE FROM tray_cell_config WHERE tray_config_id = ?",
                (config.tray_config_id,),
            )

            for cell in config.cells:
                image_region = (
                    json.dumps(cell.image_region, ensure_ascii=False)
                    if cell.image_region is not None
                    else None
                )
                conn.execute("""
                    INSERT INTO tray_cell_config
                    (tray_config_id, cell_id, weight_channel, image_region, tare_weight)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    cell.tray_config_id,
                    cell.cell_id,
                    cell.weight_channel,
                    image_region,
                    cell.tare_weight,
                ))

            conn.commit()
        finally:
            conn.close()

    def get(self, tray_config_id: str) -> Optional[TrayConfig]:
        self.initialize()
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute("""
                SELECT * FROM tray_config
                WHERE tray_config_id = ?
            """, (tray_config_id,)).fetchone()

            if row is None:
                return None

            cell_rows = conn.execute("""
                SELECT * FROM tray_cell_config
                WHERE tray_config_id = ?
                ORDER BY cell_id
            """, (tray_config_id,)).fetchall()

            cells = []
            for cell_row in cell_rows:
                image_region = (
                    json.loads(cell_row["image_region"])
                    if cell_row["image_region"] is not None
                    else None
                )
                cells.append(
                    TrayCellConfig(
                        tray_config_id=cell_row["tray_config_id"],
                        cell_id=cell_row["cell_id"],
                        weight_channel=cell_row["weight_channel"],
                        image_region=image_region,
                        tare_weight=cell_row["tare_weight"],
                    )
                )

            return TrayConfig(
                tray_config_id=row["tray_config_id"],
                name=row["name"],
                description=row["description"],
                cell_count=row["cell_count"],
                enabled=bool(row["enabled"]),
                cells=cells,
            )
        finally:
            conn.close()
