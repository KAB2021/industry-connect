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
    record_ids: Mapped[list[str]] = mapped_column(sa.JSON, nullable=False)
    summary: Mapped[str] = mapped_column(sa.Text, nullable=False)
    anomalies: Mapped[list[dict[str, Any]]] = mapped_column(sa.JSON, nullable=False)
    prompt: Mapped[str] = mapped_column(sa.Text, nullable=False)
    response_raw: Mapped[str] = mapped_column(sa.Text, nullable=False)
    prompt_tokens: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
