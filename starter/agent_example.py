"""Minimal tool-using agent loop over the grid + weather data.

    pip install anthropic
    export ANTHROPIC_API_KEY=...
    python starter/agent_example.py "Why did ERCOT demand peak where it did in August 2024?"

This is deliberately bare-bones (~40 lines) so teams can see the whole loop.
Swap in any provider or framework; the tools in agent_tools.py are plain Python.
"""
from __future__ import annotations

import json
import sys

import anthropic

from agent_tools import TOOL_SCHEMAS, call_tool

MODEL = "claude-sonnet-5-5"  # any tool-capable model works
SYSTEM = (
    "You are a power-grid analyst. Answer using the tools; cite the numbers they return. "
    "Timestamps are UTC unless a field says local. Be explicit about data-quality caveats."
)


def run(question: str, max_steps: int = 8) -> str:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": question}]
    for _ in range(max_steps):
        resp = client.messages.create(model=MODEL, max_tokens=2000, system=SYSTEM,
                                      tools=TOOL_SCHEMAS, messages=messages)
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                try:
                    out = call_tool(block.name, block.input)
                except Exception as e:  # surface errors to the model instead of crashing
                    out = {"error": str(e)}
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": json.dumps(out, default=str)})
        messages.append({"role": "user", "content": results})
    return "Stopped: too many steps."


if __name__ == "__main__":
    print(run(" ".join(sys.argv[1:]) or "Which region had the worst EIA forecast error, and when?"))
