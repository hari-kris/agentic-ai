import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"


def chat(system: str, user: str, max_tokens: int = 1024, temperature: float = 1.0) -> tuple[str, dict]:
    """Single Claude API call. Returns (text, usage_dict)."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return response.content[0].text, usage


def chat_with_tools(
    system: str,
    messages: list[dict],
    tools: list[dict],
    max_tokens: int = 1024,
) -> tuple[list, dict]:
    """Claude API call with tool use support.

    Returns (content_blocks, usage_dict).
    content_blocks is a list of dicts — each block has a "type" field:
      - {"type": "text", "text": "..."} for text output
      - {"type": "tool_use", "id": "...", "name": "...", "input": {...}} for tool calls
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        tools=tools,
        messages=messages,
    )
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    blocks = []
    for block in response.content:
        if block.type == "text":
            blocks.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            blocks.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
    return blocks, usage
