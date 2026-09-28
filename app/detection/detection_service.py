from datetime import datetime
import json
from typing import Any, Optional

from app.ai import AIRecognizer
from app.database import Database
from app.models.enums import EventStatus, RecognitionStatus, WeightStatus
from app.models.event import Event, EventCell
from app.detection.measurement_manager import MeasurementManager
from app.config import TrayConfigManager, DailyMenuProvider
from app.image_processing import ImageRegionProcessor


class DetectionService:
    """Coordinate tray detection and its automatic trigger state machine."""

    WAITING = "WAITING"
    TRAY_PRESENT = "TRAY_PRESENT"
    STABILIZING = "STABILIZING"
    READY = "READY"
    TRIGGERED = "TRIGGERED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    WAITING_FOR_REMOVAL = "WAITING_FOR_REMOVAL"
    STOPPED = "STOPPED"

    def __init__(
        self,
        measurement_manager: MeasurementManager,
        ai_recognizer: AIRecognizer,
        database: Database,
        camera: Optional[Any] = None,
        tray_config_id: Optional[str] = "TRAY_DEFAULT",
        tray_config_manager: Optional[TrayConfigManager] = None,
        image_region_processor: Optional[ImageRegionProcessor] = None,
        daily_menu_provider: Optional[DailyMenuProvider] = None,
        presence_threshold: float = 100.0,
        removal_threshold: float = 20.0,
    ):
        if removal_threshold > presence_threshold:
            raise ValueError("removal_threshold must not exceed presence_threshold")

        self.measurement_manager = measurement_manager
        self.ai_recognizer = ai_recognizer
        self.database = database
        self.camera = camera
        self.tray_config_id = tray_config_id
        self.tray_config_manager = tray_config_manager
        self.image_region_processor = image_region_processor or ImageRegionProcessor()
        self.daily_menu_provider = daily_menu_provider
        self.presence_threshold = float(presence_threshold)
        self.removal_threshold = float(removal_threshold)

        self.state = self.WAITING
        self.last_error: Optional[str] = None
        self.last_event: Optional[Event] = None
        self._event_counter = self._load_event_counter()

    def start(self) -> None:
        # Starting a new monitoring session must not reuse a stale stable
        # measurement from the previous session.
        self.measurement_manager.reset()
        self.last_error = None
        self.last_event = None
        self.state = self.WAITING

    def stop(self) -> None:
        self.state = self.STOPPED

    def get_state(self) -> str:
        return self.state

    def update(self, raw_data: Optional[dict[int, float]] = None) -> Optional[Event]:
        """Advance the automatic trigger state machine safely.

        A tray is detected once, processed once, and then locked until it is
        physically removed. A failed/partial manual trigger is also prevented
        from immediately retriggering while the same tray remains present.
        """
        if self.state == self.STOPPED:
            return None

        try:
            if raw_data is not None:
                measurement = self.measurement_manager.update(raw_data)
            else:
                measurement = self.measurement_manager.get_result()
        except Exception as exc:
            self.last_error = f"MEASUREMENT_FAILED: {type(exc).__name__}: {exc}"
            return None

        self.last_error = None
        total_weight = self._total_valid_weight(measurement)
        measurement_ready = self._measurement_ready(measurement)

        if self.state == self.WAITING:
            if total_weight >= self.presence_threshold:
                self.state = self.TRAY_PRESENT
            return None

        if self.state == self.TRAY_PRESENT:
            if total_weight < self.removal_threshold:
                self.state = self.WAITING
            elif measurement_ready:
                self.state = self.READY
            else:
                self.state = self.STABILIZING
            return None

        if self.state == self.STABILIZING:
            if total_weight < self.removal_threshold:
                self.state = self.WAITING
            elif measurement_ready:
                self.state = self.READY
            return None

        if self.state == self.READY:
            if total_weight < self.removal_threshold:
                self.state = self.WAITING
                return None
            if not measurement_ready:
                self.state = self.STABILIZING
                return None
            event = self.trigger()
            if event is not None:
                # Regardless of success/failure, do not process the same tray
                # again until it is removed.
                self.state = self.WAITING_FOR_REMOVAL
            return event

        if self.state == self.WAITING_FOR_REMOVAL:
            if total_weight <= self.removal_threshold:
                self.state = self.WAITING
            return None

        # Manual-trigger terminal states are normalized on the next weight
        # update. This prevents COMPLETED/PARTIAL/FAILED from becoming stuck.
        if self.state in (self.COMPLETED, self.PARTIAL, self.FAILED):
            if total_weight <= self.removal_threshold:
                self.state = self.WAITING
            else:
                self.state = self.WAITING_FOR_REMOVAL
            return None

        return None

    @staticmethod
    def _measurement_ready(measurement) -> bool:
        """Only a fully valid and stable four-channel measurement may trigger."""
        return bool(
            measurement
            and measurement.stable
            and measurement.valid_cells > 0
            and measurement.status == "OK"
        )

    def trigger(self) -> Optional[Event]:
        """Manual trigger retained for tests and future UI use."""
        if self.state not in (
            self.WAITING,
            self.TRAY_PRESENT,
            self.STABILIZING,
            self.READY,
            self.COMPLETED,
            self.PARTIAL,
            self.FAILED,
        ):
            return None

        measurement = self.measurement_manager.get_result()
        if not self._measurement_ready(measurement):
            self.last_error = "TRIGGER_BLOCKED: measurement is not fully valid and stable"
            return None

        self.state = self.TRIGGERED
        event = self.process_event()
        self.last_event = event
        return event

    def process_event(self) -> Event:
        """Run the complete detection workflow."""
        self.state = self.PROCESSING
        self.last_error = None

        event = Event(
            event_id=self._next_event_id(),
            timestamp=datetime.now(),
            tray_config_id=self.tray_config_id,
            status=EventStatus.CREATED,
        )

        try:
            event.status = EventStatus.PROCESSING
            measurement = self.measurement_manager.get_result()

            if measurement.valid_cells == 0:
                return self._finish_failed(event, "WEIGHT_FAILED: no valid weight cells")

            image_path = self._capture_image(event.event_id)
            event.image_path = image_path

            regions = None
            if self.tray_config_manager is not None:
                tray_config = self.tray_config_manager.get(self.tray_config_id)
                if tray_config is None:
                    return self._finish_failed(event, "INVALID_DATA: tray config not found")
                regions = self.image_region_processor.extract_regions(image_path, tray_config)

            daily_menu = None
            if self.daily_menu_provider is not None:
                daily_menu = self.daily_menu_provider.get_today_menu()
                event.menu_date = daily_menu.date
                event.menu_weekday = daily_menu.weekday
                event.menu_version = daily_menu.version
                event.menu_snapshot = json.dumps(
                    daily_menu.to_snapshot(), ensure_ascii=False, separators=(",", ":")
                )

            try:
                recognition = self.ai_recognizer.recognize(
                    image=image_path, regions=regions, daily_menu=daily_menu
                )
            except TypeError:
                # Preserve compatibility with older third-party/mock recognizers.
                recognition = self.ai_recognizer.recognize(image=image_path, regions=regions)
            if recognition.status == "FAILED":
                return self._finish_failed(event, "AI_FAILED: recognition failed")

            event.cells = self._merge_cells(measurement, recognition)

            if any(
                cell.weight_status != WeightStatus.OK
                or cell.recognition_status != RecognitionStatus.OK
                for cell in event.cells
            ):
                event.status = EventStatus.PARTIAL
                self.state = self.PARTIAL
            else:
                event.status = EventStatus.COMPLETED
                self.state = self.COMPLETED

            self.database.save_event(event)
            return event

        except Exception as exc:
            return self._finish_failed(event, f"FAILED: {type(exc).__name__}: {exc}")

    def _merge_cells(self, measurement, recognition):
        recognition_by_cell = {cell.cell_id: cell for cell in recognition.cells}
        result = []

        for measurement_cell in measurement.cells:
            recognition_cell = recognition_by_cell.get(measurement_cell.cell_id)
            event_cell = EventCell(
                event_cell_id=f"{measurement_cell.cell_id}_{self._next_cell_suffix()}",
                event_id=None,
                cell_id=measurement_cell.cell_id,
                gross_weight=measurement_cell.weight,
                tare_weight=0.0,
                net_weight=measurement_cell.weight,
                initial_weight=None,
                weight_status=measurement_cell.status,
                confidence=recognition_cell.confidence if recognition_cell else None,
                recognition_status=(
                    recognition_cell.status if recognition_cell else RecognitionStatus.FAILED
                ),
                recognition_result_type=(
                    recognition_cell.result_type if recognition_cell else "UNKNOWN"
                ),
            )
            if recognition_cell:
                event_cell.food_id = recognition_cell.food_id
                try:
                    food_map = {f.food_id: f for f in self.database.get_foods()}
                    configured = food_map.get(recognition_cell.food_id)
                    if configured and configured.initial_weight:
                        event_cell.initial_weight = float(configured.initial_weight)
                except Exception:
                    pass
            result.append(event_cell)
        return result

    def _capture_image(self, event_id: str) -> str:
        if self.camera is not None:
            return self.camera.capture(event_id)
        return f"images/{event_id}.jpg"

    def _finish_failed(self, event: Event, message: str) -> Event:
        event.status = EventStatus.FAILED
        event.error_message = message
        self.last_error = message
        self.state = self.FAILED
        try:
            self.database.save_event(event)
        except Exception as save_exc:
            self.last_error = f"{message}; SAVE_FAILED: {type(save_exc).__name__}: {save_exc}"
        self.last_event = event
        return event

    @staticmethod
    def _total_valid_weight(measurement) -> float:
        return round(
            sum(
                float(cell.weight)
                for cell in measurement.cells
                if cell.status == WeightStatus.OK and cell.weight is not None
            ),
            2,
        )

    def _load_event_counter(self) -> int:
        """Continue Event numbering when the process is restarted."""
        try:
            events = self.database.get_events()
        except Exception:
            return 0
        maximum = 0
        for event in events:
            event_id = event.event_id or ""
            if event_id.startswith("EV") and event_id[2:].isdigit():
                maximum = max(maximum, int(event_id[2:]))
        return maximum

    def _next_event_id(self) -> str:
        self._event_counter += 1
        return f"EV{self._event_counter:06d}"

    def _next_cell_suffix(self) -> str:
        return f"{self._event_counter:06d}"
