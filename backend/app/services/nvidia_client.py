"""Thin NVIDIA chat-completions client (streaming, via requests).

Never raises and never logs the API key, headers or message contents. Returns
None whenever the call cannot produce text, so callers can fall back to
deterministic templates.
"""

from __future__ import annotations

import json

import requests

from app.core.config import get_settings


def ask_nvidia(system_prompt: str, user_prompt: str) -> str | None:
    return chat_completion(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )


def chat_completion(messages: list[dict]) -> str | None:
    settings = get_settings()
    if not settings.nvidia_api_key:
        return None

    api_url = settings.nvidia_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.nvidia_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.nvidia_model,
        "messages": messages,
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": settings.nvidia_max_tokens,
        "stream": True,
        "chat_template_kwargs": {"enable_thinking": settings.nvidia_enable_thinking},
    }

    try:
        parts: list[str] = []
        with requests.post(
            api_url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=(15, settings.nvidia_timeout_seconds),
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices", [])
                if not choices:
                    continue
                content = choices[0].get("delta", {}).get("content")
                if content:
                    parts.append(content)
        text = "".join(parts).strip()
        return text or None
    except requests.exceptions.RequestException:
        return None
    except Exception:
        return None
