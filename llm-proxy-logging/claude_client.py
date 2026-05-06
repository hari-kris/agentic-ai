"""
claude_client.py — Claude API wrapper with Requesty.ai proxy support.

When REQUESTY_API_KEY is set in .env, every call is routed through
https://router.requesty.ai and logged to the Requesty dashboard.
Falls back to direct Anthropic API when the key is absent.
"""

import os
import time
import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
REQUESTY_API_KEY  = os.getenv("REQUESTY_API_KEY")

# True when calls are proxied through Requesty
REQUESTY_ACTIVE = bool(REQUESTY_API_KEY)


def _make_client() -> anthropic.Anthropic:
    if REQUESTY_ACTIVE:
        return anthropic.Anthropic(
            api_key=REQUESTY_API_KEY,
            base_url="https://router.requesty.ai/anthropic",
        )
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def chat(
    system: str,
    user: str,
    max_tokens: int = 1024,
    temperature: float = 1.0,
) -> tuple[str, dict]:
    """Single Claude API call. Returns (text, usage_dict).

    usage_dict keys: input_tokens, output_tokens, latency_ms
    """
    client = _make_client()
    t0 = time.perf_counter()
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text, {
        "input_tokens":  response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency_ms":    int((time.perf_counter() - t0) * 1000),
    }


def chat_with_tools(
    system: str,
    messages: list[dict],
    tools: list[dict],
    max_tokens: int = 1024,
) -> tuple[list, dict]:
    """Claude API call with tool use support. Returns (content_blocks, usage_dict).

    content_blocks — list of dicts, each with a "type" field:
      {"type": "text",     "text": "..."}
      {"type": "tool_use", "id": "...", "name": "...", "input": {...}}

    usage_dict keys: input_tokens, output_tokens, latency_ms
    """
    client = _make_client()
    t0 = time.perf_counter()
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        tools=tools,
        messages=messages,
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)

    blocks = []
    for block in response.content:
        if block.type == "text":
            blocks.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            blocks.append({
                "type":  "tool_use",
                "id":    block.id,
                "name":  block.name,
                "input": block.input,
            })

    return blocks, {
        "input_tokens":  response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency_ms":    latency_ms,
    }
