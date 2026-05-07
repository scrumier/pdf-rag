import pytest
from rag.core import chunk_text


def test_chunk_text_splits_on_length():
    text = "mot " * 300  # 300 mots
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.split()) <= 110  # tolerance overlap


def test_chunk_text_preserves_content():
    text = "alpha beta gamma delta " * 50
    chunks = chunk_text(text, chunk_size=50, overlap=10)
    joined = " ".join(chunks)
    assert "alpha" in joined
    assert "gamma" in joined


def test_chunk_text_empty():
    assert chunk_text("", chunk_size=100, overlap=20) == []
