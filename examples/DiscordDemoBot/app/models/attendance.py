from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("meeting_id", "person_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meeting_id: Mapped[int] = mapped_column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
