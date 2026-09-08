from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ScheduleBlock(Base):
    __tablename__ = "schedule_blocks"
    __table_args__ = (CheckConstraint("ends_at > starts_at", name="ck_schedule_block_time_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    barber_member_id: Mapped[int] = mapped_column(ForeignKey("business_members.id", ondelete="CASCADE"), index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    barber = relationship("BusinessMember", back_populates="schedule_blocks")
