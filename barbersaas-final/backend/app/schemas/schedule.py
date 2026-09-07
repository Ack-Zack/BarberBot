from datetime import datetime, time
from pydantic import BaseModel, Field, model_validator


class IntervalIn(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def validate_order(self):
        if self.start_time >= self.end_time:
            raise ValueError("end_time must be later than start_time")
        return self


class WorkingHoursIn(BaseModel):
    intervals: list[IntervalIn]

    @model_validator(mode="after")
    def validate_no_overlap(self):
        grouped: dict[int, list[IntervalIn]] = {}
        for interval in self.intervals:
            grouped.setdefault(interval.weekday, []).append(interval)
        for weekday, items in grouped.items():
            items.sort(key=lambda item: item.start_time)
            for previous, current in zip(items, items[1:]):
                if previous.end_time > current.start_time:
                    raise ValueError(f"Working intervals overlap on weekday {weekday}")
        return self


class ScheduleBlockCreate(BaseModel):
    barber_id: int
    starts_at: datetime
    ends_at: datetime
    reason: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_order(self):
        if self.starts_at >= self.ends_at:
            raise ValueError("ends_at must be later than starts_at")
        return self


class ScheduleBlockOut(BaseModel):
    id: int
    barber_id: int
    starts_at: datetime
    ends_at: datetime
    reason: str | None

    model_config = {"from_attributes": True}
