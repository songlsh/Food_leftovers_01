from enum import Enum


class EventStatus(str, Enum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class WeightStatus(str, Enum):
    OK = "OK"
    SENSOR_ERROR = "SENSOR_ERROR"
    INVALID = "INVALID"


class RecognitionStatus(str, Enum):
    OK = "OK"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    UNKNOWN = "UNKNOWN"
    FAILED = "FAILED"
