"""Token counting utilities using tiktoken."""

import tiktoken


def count_tokens(text: str, model: str) -> int:
    """Return the number of tokens in *text* for the given *model*."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))
