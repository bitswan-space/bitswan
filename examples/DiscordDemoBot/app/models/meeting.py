from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meeting_date: Mapped[object] = mapped_column(Date, unique=True, nullable=False)
    status_channel_id: Mapped[str] = mapped_column(String, nullable=False)
    status_message_id: Mapped[str | None] = mapped_column(String, nullable=True)
