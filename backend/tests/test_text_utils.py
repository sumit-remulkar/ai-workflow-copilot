from app.utils.text import chunk_text

def test_chunk_text() -> None:
    text = "a " * 2500
    chunks = chunk_text(text, chunk_size=1000, overlap=100)
    assert len(chunks) >= 2
