from __future__ import annotations

import math
import hashlib
from openai import OpenAI

from app.core.config import settings

class EmbeddingService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def embed_text(self, text: str) -> list[float]:
        if self.client:
            response = self.client.embeddings.create(
                model=settings.openai_embedding_model,
                input=text,
            )
            return list(response.data[0].embedding)

        return self._fallback_embedding(text, settings.embedding_dimension)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

    def _fallback_embedding(self, text: str, dim: int) -> list[float]:
        '''Deterministic fallback embedding so the starter app works without an API key.'''
        vec = [0.0] * dim
        tokens = text.lower().split()
        if not tokens:
            return vec

        for token in tokens:
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            vec[idx] += 1.0

        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
