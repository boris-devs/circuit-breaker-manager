import datetime
import enum

from sqlalchemy import Integer, String, Enum, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class StateServiceEnum(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    HALF_OPEN = "HALF_OPEN"


class MonitoredServices(Base):
    __tablename__ = "monitored_services"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String(255))
    state: Mapped[StateServiceEnum] = mapped_column(Enum(StateServiceEnum), default=StateServiceEnum.CLOSED)
    failure_threshold: Mapped[int] = mapped_column(Integer, default=5)
    recovery_timeout: Mapped[int] = mapped_column(Integer, default=60)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_failure_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_check: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class CircuitBreakerLog(Base):
    __tablename__ = "circuit_breaker_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("monitored_services.id"))
    old_state: Mapped[StateServiceEnum] = mapped_column(Enum(StateServiceEnum), nullable=False)
    new_state: Mapped[StateServiceEnum] = mapped_column(Enum(StateServiceEnum), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    @classmethod
    def default_order_by(cls):
        return cls.created_at.desc()
