from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    processed_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
