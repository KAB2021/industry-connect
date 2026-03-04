import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OperationalRecord(Base):
    __tablename__ = "operational_records"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    source: Mapped[str] = mapped_column(sa.String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    entity_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    metric_name: Mapped[str] = mapped_column(sa.String, nullable=False)
    metric_value: Mapped[float] = mapped_column(sa.Float, nullable=False)
    analysed: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.text("false")
    )
    ingested_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
