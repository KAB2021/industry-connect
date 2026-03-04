import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    record_ids: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    summary: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    anomalies: Mapped[Any | None] = mapped_column(sa.JSON, nullable=True)
    prompt: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    response_raw: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
