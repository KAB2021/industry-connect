"""Background poller service.

Fetches records from POLL_SOURCE_URL on a configurable interval and persists
them as OperationalRecord rows with source='poll'.
"""
import asyncio
import logging
from typing import Any

import httpx
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.operational_record import OperationalRecord

logger = logging.getLogger(__name__)


async def poll_once(session_factory: sessionmaker, client: httpx.AsyncClient) -> int:
    """Fetch records from POLL_SOURCE_URL and persist them.

    Returns the count of OperationalRecord rows created.
    Raises httpx.HTTPStatusError on non-2xx responses.
    Raises json.JSONDecodeError (or httpx.DecodingError) on malformed JSON.
    Raises KeyError when required fields are missing from a response item.
    """
    response = await client.get(settings.POLL_SOURCE_URL)
    response.raise_for_status()
    data = response.json()  # Expected: list of {timestamp, entity_id, metric_name, metric_value}

    count = 0
    session = session_factory()
    try:
        for item in data:
            record = OperationalRecord(
                source="poll",
                timestamp=item["timestamp"],
                entity_id=item["entity_id"],
                metric_name=item["metric_name"],
                metric_value=float(item["metric_value"]),
                analysed=False,
            )
            session.add(record)
            count += 1
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return count


async def run_poller(session_factory: sessionmaker, poll_settings: Any = None) -> None:
    """Run the polling loop indefinitely until cancelled.

    When POLL_SOURCE_URL is not configured the function returns immediately.
    HTTP errors, timeouts, and JSON decode errors are logged and the loop
    continues after the configured interval.
    """
    s = poll_settings or settings
    if not s.POLL_SOURCE_URL:
        logger.info("POLL_SOURCE_URL not set, skipping poller")
        return

    async with httpx.AsyncClient() as client:
        while True:
            try:
                count = await poll_once(session_factory, client)
                logger.info("Polled %d records", count)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Poller cycle failed")
            await asyncio.sleep(s.POLL_INTERVAL_SECONDS)
