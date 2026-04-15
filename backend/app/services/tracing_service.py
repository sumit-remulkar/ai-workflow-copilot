from __future__ import annotations

from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from typing import Any, Iterator

from langfuse import get_client

from app.core.config import settings


@dataclass
class _NullObservation:
    def update(self, **_: Any) -> None:
        return None


class TracingService:
    def __init__(self) -> None:
        self.enabled = bool(settings.langfuse_secret_key and settings.langfuse_public_key)
        self.client = get_client() if self.enabled else None

    @contextmanager
    def span(
        self,
        name: str,
        *,
        as_type: str = "span",
        input: Any | None = None,
        output: Any | None = None,
        metadata: dict[str, Any] | None = None,
        model: str | None = None,
    ) -> Iterator[Any]:
        if not self.client:
            yield _NullObservation()
            return

        with self.client.start_as_current_observation(as_type=as_type, name=name, model=model) as observation:
            if input is not None or metadata is not None or output is not None:
                update_kwargs: dict[str, Any] = {}
                if input is not None:
                    update_kwargs["input"] = input
                if output is not None:
                    update_kwargs["output"] = output
                if metadata is not None:
                    update_kwargs["metadata"] = metadata
                observation.update(**update_kwargs)
            yield observation

    def flush(self) -> None:
        if self.client:
            self.client.flush()
