from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TrayCellConfig:
    tray_config_id: Optional[str] = None
    cell_id: int = 0
    weight_channel: int = 0
    image_region: Any = None
    tare_weight: float = 0.0


@dataclass
class TrayConfig:
    tray_config_id: Optional[str] = None
    name: str = ""
    description: Optional[str] = None
    cell_count: int = 4
    enabled: bool = True
    cells: list[TrayCellConfig] = field(default_factory=list)
