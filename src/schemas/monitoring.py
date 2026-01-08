from datetime import datetime

from pydantic import BaseModel, ConfigDict, AnyHttpUrl, field_validator

from database.models.circuit_breaker import StateServiceEnum


class CreateServiceMonitoringSchema(BaseModel):
    name: str
    url: AnyHttpUrl
    state: StateServiceEnum = StateServiceEnum.CLOSED
    failure_threshold: int | None = 5
    recovery_timeout: int | None = 60

    @field_validator("url", mode="after")
    @classmethod
    def url_to_str(cls, v):
        return str(v)


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    state: str
    failure_count: int
    last_failure_time: datetime | None
    last_check: datetime | None


class CreateCircuitBreakerLogsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    service_id: int
    old_state: StateServiceEnum
    new_state: StateServiceEnum
    detail: str | None
