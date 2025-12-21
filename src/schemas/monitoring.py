from datetime import datetime

from pydantic import BaseModel, ConfigDict

from database.models.circuit_breaker import StateServiceEnum


class CreateServiceMonitoringSchema(BaseModel):
    name: str
    url: str
    state: StateServiceEnum = StateServiceEnum.CLOSED
    failure_threshold: int | None = 5
    recovery_timeout: int | None = 60

class CreateServiceMonitoringResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    state: str
    failure_threshold: int
    recovery_timeout: int
    failure_count: int
    last_failure_time: datetime | None
    last_check: datetime | None

class HealthServiceMonitoringSchema(BaseModel):
    id: str
    name: str
    url: str
    state: str
    failure_count: int
    last_failure_time: datetime | None
    last_check: datetime | None