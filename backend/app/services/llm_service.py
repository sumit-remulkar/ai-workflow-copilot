from __future__ import annotations

import json
from typing import Any

from openai import AzureOpenAI, OpenAI

from app.core.config import settings


class LLMService:
    def __init__(self) -> None:
        self.provider = self._resolve_provider()
        self.client = self._build_client()
        self.model = self._resolve_model()

    def _resolve_provider(self) -> str:
        provider = settings.llm_provider.lower().strip()
        if provider in {"openai", "azure", "mock"}:
            return provider
        if settings.azure_openai_api_key and settings.azure_openai_endpoint:
            return "azure"
        if settings.openai_api_key:
            return "openai"
        return "mock"

    def _build_client(self):
        if self.provider == "azure":
            return AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
            )
        if self.provider == "openai":
            kwargs: dict[str, Any] = {"api_key": settings.openai_api_key}
            if settings.openai_base_url:
                kwargs["base_url"] = settings.openai_base_url
            return OpenAI(**kwargs)
        return None

    def _resolve_model(self) -> str:
        if self.provider == "azure":
            return settings.azure_openai_deployment
        if self.provider == "openai":
            return settings.openai_model
        return "mock"

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        fallback: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        fallback = fallback or {}
        if not self.client:
            return fallback

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return self._extract_json_object(content, fallback)

    def generate_text(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.2, fallback: str = "") -> str:
        if not self.client:
            return fallback

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or fallback

    def _extract_json_object(self, content: str, fallback: dict[str, Any]) -> dict[str, Any]:
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(content[start : end + 1])
            except json.JSONDecodeError:
                return fallback
        return fallback
