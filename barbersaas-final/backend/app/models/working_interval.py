from datetime import time
from sqlalchemy import ForeignKey, Integer, Time, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class WorkingInterval(Base):
    __tablename__ = "working_intervals"
    __table_args__ = (CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_weekday"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    barber_member_id: Mapped[int] = mapped_column(ForeignKey("business_members.id", ondelete="CASCADE"), index=True)
    weekday: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    barber = relationship("BusinessMember", back_populates="working_intervals")
