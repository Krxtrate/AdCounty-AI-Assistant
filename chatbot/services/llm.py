"""
services/llm.py
────────────────
Automatic failover LLM router.

Tries Hugging Face Inference API first (fast, ~3-5s, free tier).
On failure (rate limit, timeout, server error), falls back to local
Ollama (medium-slow, ~30-50s, local), and flags the response so the frontend can show a notice.

Automatically retries HF every 24 hours in case the rate limit reset.

app.py imports ONLY from here — never from hf.py or ollama.py directly.
"""

import asyncio
import time

import httpx

from chatbot.services import hf
from chatbot.services import ollama as ollama_backend

_hf_available = True
_fallback_since: float | None = None
HF_RETRY_INTERVAL_SECONDS = 24 * 60 * 60  # retry HF once a day


def prewarm_ollama() -> None:
    """Pre-warm both backends so neither pays a cold-start penalty
    whenever it's actually used."""
    hf.prewarm_ollama()
    ollama_backend.prewarm_ollama()


def _maybe_auto_reset() -> None:
    """If we've been on fallback long enough, give HF another shot."""
    global _hf_available, _fallback_since
    if not _hf_available and _fallback_since is not None:
        elapsed = time.time() - _fallback_since
        if elapsed >= HF_RETRY_INTERVAL_SECONDS:
            print("24h elapsed on fallback — retrying HF Inference API.")
            _hf_available = True
            _fallback_since = None


async def call_ollama(payload: dict, timeout: float = 120.0) -> dict:
    """
    Try HF first. On failure, fall back to local Ollama (which must be
    running on this server) and tag the response so app.py can surface
    a notice to the frontend. Auto-retries HF after 24h on fallback.
    """
    global _hf_available, _fallback_since

    _maybe_auto_reset()

    if _hf_available:
        try:
            result = await hf.call_ollama(payload, timeout=timeout)
            result["_backend"] = "hf"
            return result
        except (httpx.TimeoutException, httpx.RequestError, RuntimeError) as e:
            print(f"HF API failed, falling back to local Ollama: {e}")
            _hf_available = False
            _fallback_since = time.time()
        except Exception as e:
            print(f"HF API unexpected error, falling back to local Ollama: {e}")
            _hf_available = False
            _fallback_since = time.time()

    # ── Fallback path — local Ollama on this server ──────────────────
    try:
        result = await ollama_backend.call_ollama(payload, timeout=timeout)
        result["_backend"] = "ollama"
        return result
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        # Ollama itself isn't reachable — likely not installed/running
        # (expected for public repo clones without a local model)
        print(f"Ollama fallback also unavailable: {e}")
        raise RuntimeError(
            "Both Hugging Face Inference API and local Ollama are "
            "unavailable. If running this outside the AdCounty server, "
            "make sure Ollama is installed and running, or wait for the "
            "HF rate limit to reset."
        )


def compute_ctx(ollama_messages: list, desired_predict: int) -> tuple[int, int]:
    if _hf_available:
        return hf.compute_ctx(ollama_messages, desired_predict)
    return ollama_backend.compute_ctx(ollama_messages, desired_predict)


def log_timing_summary(*args, **kwargs) -> None:
    if _hf_available:
        hf.log_timing_summary(*args, **kwargs)
    else:
        ollama_backend.log_timing_summary(*args, **kwargs)


def get_model_name() -> str:
    return hf.get_model_name() if _hf_available else ollama_backend.get_model_name()


def is_using_fallback() -> bool:
    return not _hf_available