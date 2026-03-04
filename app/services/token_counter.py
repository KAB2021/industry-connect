"""Token counting utilities using tiktoken."""

import functools

import tiktoken


@functools.lru_cache(maxsize=8)
def _get_encoding(model: str) -> tiktoken.Encoding:
    return tiktoken.encoding_for_model(model)


def count_tokens(text: str, model: str) -> int:
    """Return the number of tokens in *text* for the given *model*."""
    return len(_get_encoding(model).encode(text))
