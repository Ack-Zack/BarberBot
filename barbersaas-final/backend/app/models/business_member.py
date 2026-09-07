from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class BusinessMember(Base):
    __tablename__ = "business_members"
    __table_args__ = (UniqueConstraint("business_id", "user_id", name="uq_business_member"), CheckConstraint("role IN ('owner', 'barber', 'client')", name="ck_business_member_role"))
    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(32))
    display_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    business = relationship("Business", back_populates="members")
    user = relationship("User", back_populates="memberships")
    working_intervals = relationship("WorkingInterval", back_populates="barber")
    schedule_blocks = relationship("ScheduleBlock", back_populates="barber")
    appointments = relationship("Appointment", back_populates="barber")
