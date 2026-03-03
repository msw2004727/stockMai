from __future__ import annotations

from typing import Any

from .base_http_client import AsyncJsonHttpClient
from .provider_client import ProviderCallError, ProviderResponse, TokenUsage


class OpenAICompatClient(AsyncJsonHttpClient):
    provider = "openai"

    def __init__(self, provider: str, api_key: str, model: str, base_url: str):
        self.provider = provider
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.base_url = base_url.rstrip("/")

    async def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> ProviderResponse:
        if not self.api_key:
            raise ProviderCallError(f"{self.provider} API key is missing.", retryable=False)
        if not self.model:
            raise ProviderCallError(f"{self.provider} model is missing.", retryable=False)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if self.provider == "gpt5":
            text, _, usage = await self._call_and_extract_text(
                endpoint="/responses",
                payload={
                    "model": self.model,
                    "input": prompt,
                    "temperature": 0.2,
                    "max_output_tokens": 500,
                },
                headers=headers,
                timeout_seconds=timeout_seconds,
            )
            if text:
                return ProviderResponse(text=text, usage=usage)

            # Fallback to chat/completions for compatibility if responses body is empty.
            fallback_text, fallback_raw, fallback_usage = await self._call_and_extract_text(
                endpoint="/chat/completions",
                payload={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_completion_tokens": 500,
                },
                headers=headers,
                timeout_seconds=timeout_seconds,
            )
            if fallback_text:
                return ProviderResponse(text=fallback_text, usage=fallback_usage)

            detail = _build_missing_content_detail(fallback_raw)
            raise ProviderCallError(
                f"{self.provider} response missing message content.{detail}",
                retryable=True,
            )

        return await self._generate_chat_completion_with_fallback(
            prompt=prompt,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

    async def _generate_chat_completion_with_fallback(
        self,
        prompt: str,
        headers: dict[str, str],
        timeout_seconds: int,
    ) -> ProviderResponse:
        last_raw_text = ""
        last_error: ProviderCallError | None = None

        model_candidates = _build_model_candidates(provider=self.provider, model=self.model)
        for model in model_candidates:
            payload_candidates = _build_chat_completion_payload_candidates(model, prompt)
            switch_model = False
            for payload in payload_candidates:
                try:
                    text, raw_text, usage = await self._call_and_extract_text(
                        endpoint="/chat/completions",
                        payload=payload,
                        headers=headers,
                        timeout_seconds=timeout_seconds,
                    )
                    last_raw_text = raw_text
                    if text:
                        return ProviderResponse(text=text, usage=usage)
                except ProviderCallError as exc:
                    last_error = exc
                    parsed_error = str(exc)
                    if _is_unsupported_parameter_error(parsed_error):
                        continue
                    if _is_model_not_found_error(parsed_error):
                        switch_model = True
                        break
                    raise
            if switch_model:
                continue

        if last_error and not last_raw_text:
            raise last_error

        detail = _build_missing_content_detail(last_raw_text)
        raise ProviderCallError(
            f"{self.provider} response missing message content.{detail}",
            retryable=True,
        )

    async def _call_and_extract_text(
        self,
        endpoint: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        timeout_seconds: int,
    ) -> tuple[str, str, TokenUsage | None]:
        status_code, data, raw_text = await self.post_json(
            url=f"{self.base_url}{endpoint}",
            payload=payload,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

        if status_code >= 500:
            raise ProviderCallError(
                f"{self.provider} server error: HTTP {status_code}",
                retryable=True,
            )
        if status_code >= 400:
            detail = f" ({raw_text[:200]})" if raw_text else ""
            raise ProviderCallError(
                f"{self.provider} request rejected: HTTP {status_code}{detail}",
                retryable=False,
            )

        return _extract_openai_text(data), raw_text, _extract_openai_usage(data)


class OpenAIClient(OpenAICompatClient):
    def __init__(self, api_key: str, model: str):
        super().__init__(
            provider="gpt5",
            api_key=api_key,
            model=model,
            base_url="https://api.openai.com/v1",
        )


def _extract_openai_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message")
            if isinstance(message, dict):
                text = _extract_content_text(message.get("content"))
                if text:
                    return text
                refusal = message.get("refusal")
                if isinstance(refusal, str) and refusal.strip():
                    return refusal.strip()
                reasoning_content = _extract_content_text(message.get("reasoning_content"))
                if reasoning_content:
                    return reasoning_content
                reasoning = _extract_content_text(message.get("reasoning"))
                if reasoning:
                    return reasoning

            choice_text = first_choice.get("text")
            if isinstance(choice_text, str) and choice_text.strip():
                return choice_text.strip()

    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    response = payload.get("response")
    if isinstance(response, dict):
        nested_output_text = response.get("output_text")
        if isinstance(nested_output_text, str) and nested_output_text.strip():
            return nested_output_text.strip()
        text = _extract_output_text(response.get("output"))
        if text:
            return text

    text = _extract_output_text(payload.get("output"))
    if text:
        return text

    return ""


def _extract_openai_usage(payload: dict[str, Any]) -> TokenUsage | None:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        response = payload.get("response")
        if isinstance(response, dict):
            usage = response.get("usage")
    if not isinstance(usage, dict):
        return None

    input_tokens = _to_int(usage.get("prompt_tokens"))
    if input_tokens is None:
        input_tokens = _to_int(usage.get("input_tokens"))

    output_tokens = _to_int(usage.get("completion_tokens"))
    if output_tokens is None:
        output_tokens = _to_int(usage.get("output_tokens"))

    total_tokens = _to_int(usage.get("total_tokens"))
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens

    if input_tokens is None and output_tokens is None and total_tokens is None:
        return None
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )


def _build_missing_content_detail(raw_text: str) -> str:
    snippet = raw_text.strip()[:220]
    if not snippet:
        return ""
    return f" raw={snippet}"


def _is_unsupported_parameter_error(message: str) -> bool:
    text = str(message or "").lower()
    return (
        "unsupported parameter" in text
        or "is not supported with this model" in text
        or "unknown parameter" in text
    )


def _is_model_not_found_error(message: str) -> bool:
    text = str(message or "").lower()
    return "model not found" in text or "unknown model" in text or "does not exist" in text


def _build_model_candidates(provider: str, model: str) -> list[str]:
    selected = str(model or "").strip()
    if not selected:
        return [selected]

    candidates: list[str] = [selected]
    normalized_provider = str(provider or "").strip().lower()
    normalized_model = selected.lower()

    if normalized_provider == "grok":
        replacement = selected.replace(".", "-")
        if replacement != selected:
            candidates.append(replacement)

        aliases = {
            "grok-4.1-fast": [
                "grok-4-1-fast-non-reasoning",
                "grok-4-1-fast-reasoning",
                "grok-4-fast-non-reasoning",
                "grok-4-fast-reasoning",
                "grok-4",
            ],
            "grok-4-1-fast": [
                "grok-4-1-fast-non-reasoning",
                "grok-4-1-fast-reasoning",
                "grok-4-fast-non-reasoning",
                "grok-4-fast-reasoning",
                "grok-4",
            ],
            "grok-4-fast": [
                "grok-4-fast-non-reasoning",
                "grok-4-fast-reasoning",
                "grok-4",
            ],
        }
        candidates.extend(aliases.get(normalized_model, []))

    if normalized_provider == "deepseek":
        aliases = {
            "deepseek": ["deepseek-chat", "deepseek-reasoner"],
            "deepseek-v3": ["deepseek-chat"],
            "deepseek-r1": ["deepseek-reasoner"],
        }
        candidates.extend(aliases.get(normalized_model, []))

    deduped: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        parsed = str(item or "").strip()
        if not parsed:
            continue
        if parsed in seen:
            continue
        seen.add(parsed)
        deduped.append(parsed)
    return deduped or [selected]


def _build_chat_completion_payload_candidates(model: str, prompt: str) -> list[dict[str, Any]]:
    base_messages = [{"role": "user", "content": prompt}]
    candidates = [
        {"model": model, "messages": base_messages, "temperature": 0.2, "max_tokens": 500},
        {"model": model, "messages": base_messages, "max_tokens": 500},
        {"model": model, "messages": base_messages, "max_completion_tokens": 500},
        {"model": model, "messages": base_messages, "temperature": 0.2, "max_completion_tokens": 500},
    ]

    deduped: list[dict[str, Any]] = []
    signatures: set[tuple[tuple[str, str], ...]] = set()
    for payload in candidates:
        signature = tuple(sorted((key, str(value)) for key, value in payload.items()))
        if signature in signatures:
            continue
        signatures.add(signature)
        deduped.append(payload)
    return deduped


def _extract_output_text(output: Any) -> str:
    if not isinstance(output, list):
        return ""

    parts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue

        text = _extract_content_text(item.get("content"))
        if text:
            parts.append(text)

        direct_text = item.get("text")
        if isinstance(direct_text, str) and direct_text.strip():
            parts.append(direct_text.strip())
        elif isinstance(direct_text, dict):
            nested_value = direct_text.get("value")
            if isinstance(nested_value, str) and nested_value.strip():
                parts.append(nested_value.strip())

    return "\n".join(part for part in parts if part).strip()


def _extract_content_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parsed = item.strip()
            if parsed:
                parts.append(parsed)
            continue

        if not isinstance(item, dict):
            continue

        text = item.get("text")
        if isinstance(text, str):
            parsed = text.strip()
            if parsed:
                parts.append(parsed)
            continue

        if isinstance(text, dict):
            value = text.get("value")
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
                continue

        nested = item.get("content")
        if isinstance(nested, str):
            parsed = nested.strip()
            if parsed:
                parts.append(parsed)
            continue
        if isinstance(nested, list):
            nested_text = _extract_content_text(nested)
            if nested_text:
                parts.append(nested_text)

    return "\n".join(part for part in parts if part).strip()


def _to_int(raw: Any) -> int | None:
    try:
        if raw is None:
            return None
        value = int(raw)
        return value if value >= 0 else None
    except Exception:
        return None
