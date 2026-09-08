import pytest
from pydantic import ValidationError

from app.schemas.schedule import IntervalIn, ScheduleBlockCreate, WorkingHoursIn


def test_working_hours_reject_overlaps() -> None:
    with pytest.raises(ValidationError):
        WorkingHoursIn(intervals=[
            IntervalIn(weekday=0, start_time='09:00', end_time='13:00'),
            IntervalIn(weekday=0, start_time='12:00', end_time='18:00'),
        ])


def test_working_hours_allow_adjacent_intervals() -> None:
    value = WorkingHoursIn(intervals=[
        IntervalIn(weekday=0, start_time='09:00', end_time='13:00'),
        IntervalIn(weekday=0, start_time='13:00', end_time='18:00'),
    ])
    assert len(value.intervals) == 2


def test_schedule_block_requires_positive_range() -> None:
    with pytest.raises(ValidationError):
        ScheduleBlockCreate(
            barber_id=1,
            starts_at='2026-09-20T15:00:00',
            ends_at='2026-09-20T15:00:00',
        )
