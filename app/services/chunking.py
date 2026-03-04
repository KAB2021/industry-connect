"""Map-reduce chunking utilities for splitting large record batches."""

import json
from typing import Any

from app.services.token_counter import count_tokens

# Fraction of the threshold to target per chunk (80%)
_FILL_RATIO = 0.8
# Number of records to overlap between consecutive chunks
_OVERLAP = 2


def chunk_records(
    records: list[Any],
    token_threshold: int,
    model: str,
) -> list[list[Any]]:
    """Split *records* into chunks whose serialised token count stays under
    *token_threshold* * ``_FILL_RATIO``.

    Consecutive chunks share ``_OVERLAP`` records at their boundaries so that
    context is not lost between map steps.

    Parameters
    ----------
    records:
        The list of objects to chunk. Each item must be JSON-serialisable.
    token_threshold:
        Maximum token budget per chunk (only *_FILL_RATIO* fraction is used).
    model:
        OpenAI model name used to select the tokeniser.

    Returns
    -------
    list[list]:
        A list of chunks. If all records fit in a single chunk, a list with
        one element is returned.
    """
    if not records:
        return []

    target_tokens = int(token_threshold * _FILL_RATIO)

    # Fast path: everything fits in one chunk
    full_text = json.dumps(records)
    if count_tokens(full_text, model) <= target_tokens:
        return [records]

    chunks: list[list[Any]] = []
    current_chunk: list[Any] = []
    current_tokens: int = 0

    for record in records:
        record_text = json.dumps(record)
        record_tokens = count_tokens(record_text, model)

        if current_chunk and current_tokens + record_tokens > target_tokens:
            # Seal the current chunk
            chunks.append(current_chunk)
            # Start the next chunk with the overlap tail of the previous one
            overlap = current_chunk[-_OVERLAP:] if len(current_chunk) >= _OVERLAP else current_chunk[:]
            current_chunk = overlap + [record]
            current_tokens = count_tokens(json.dumps(current_chunk), model)
        else:
            current_chunk.append(record)
            current_tokens += record_tokens

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
