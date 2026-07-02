"""
main.py

Entry point for the Edit Agent.

Usage:
    python main.py
"""

import os
import requests
from dotenv import load_dotenv

from tools.parser import extract_tool_request
from tools.filesystem import read_file, list_dir, write_file
from agent.planner import plan_and_format
from tools.sandbox import ensure_sandbox_exists
from prompts import AGENT_SYSTEM_PROMPT
from agent.exceptions import (
    ModelConnectionError,
    ModelTimeoutError,
    ToolExecutionError,
    MaxIterationsExceeded,
)

load_dotenv()
ensure_sandbox_exists()

TOOL_REGISTRY = {
    "read_file": read_file,
    "list_dir": list_dir,
    "write_file": write_file,
}

MAX_ITERATIONS = 10
MAX_RETRIES = 2  # how many times to retry a failed model call


def run_tool(tool_request: dict) -> str:
    """
    Execute the tool the model requested and return the result.

    Never raises — all errors are caught and returned as a string
    so the model can see what went wrong and adjust its next request.
    """
    # Validate the request has the shape we expect
    if "tool" not in tool_request or "args" not in tool_request:
        return "Error: malformed tool request. Expected 'tool' and 'args' keys."

    tool_name = tool_request["tool"]
    args = tool_request["args"]

    if not isinstance(args, dict):
        return f"Error: 'args' must be a dictionary, got {type(args).__name__}."

    if tool_name not in TOOL_REGISTRY:
        available = ", ".join(TOOL_REGISTRY.keys())
        return f"Error: unknown tool '{tool_name}'. Available tools: {available}"

    tool_fn = TOOL_REGISTRY[tool_name]

    try:
        result = tool_fn(**args)
        return str(result)

    except TypeError as e:
        # Usually means wrong/missing arguments were passed
        return f"Error: incorrect arguments for '{tool_name}': {e}"

    except FileNotFoundError as e:
        return f"Error: {e}"

    except PermissionError as e:
        return f"Error: {e}"

    except Exception as e:
        # Catch-all — we never want an unexpected error to crash the loop
        return f"Error: unexpected failure in '{tool_name}': {e}"


def call_model(messages: list, retries: int = MAX_RETRIES) -> str:
    """
    Call the model with the full conversation history.

    Retries automatically on timeout or connection failure.
    Raises a clear AgentError if all retries are exhausted.

    Args:
        messages: The full conversation history to send.
        retries:  How many attempts remain.

    Returns:
        The model's response text.

    Raises:
        ModelConnectionError: If Ollama cannot be reached after all retries.
        ModelTimeoutError: If the model times out after all retries.
    """
    url = f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/chat"
    model = os.getenv("DEFAULT_MODEL", "llama3.2")

    try:
        response = requests.post(
            url,
            json={"model": model, "stream": False, "messages": messages},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    except requests.exceptions.ConnectionError:
        if retries > 0:
            print(f"  [retry] Connection failed, retrying... ({retries} attempts left)")
            return call_model(messages, retries=retries - 1)
        raise ModelConnectionError(
            "Could not connect to Ollama. Is it running? Try: ollama serve"
        )

    except requests.exceptions.ReadTimeout:
        if retries > 0:
            print(f"  [retry] Model timed out, retrying... ({retries} attempts left)")
            return call_model(messages, retries=retries - 1)
        raise ModelTimeoutError(
            "The model took too long to respond. Try a smaller model or shorter input."
        )

    except requests.exceptions.HTTPError as e:
        raise ModelConnectionError(f"Ollama returned an error: {e}")


def run_agent_turn(history: list) -> str:
    """
    Run one full agent turn — may involve multiple tool calls —
    starting from the current conversation history.

    Args:
        history: The conversation so far. Gets appended to in place.

    Returns:
        The agent's final plain text response for this turn.

    Raises:
        MaxIterationsExceeded: If the loop never reaches a final answer.
    """
    for iteration in range(1, MAX_ITERATIONS + 1):
        try:
            raw_response = call_model(history)
        except (ModelConnectionError, ModelTimeoutError) as e:
            # Don't crash — return a clear message instead
            return f"[Error] {e}"

        tool_request = extract_tool_request(raw_response)

        if tool_request is None:
            history.append({"role": "assistant", "content": raw_response})
            return raw_response

        tool_name = tool_request.get("tool", "unknown")
        print(f"  → using {tool_name}...")
        tool_result = run_tool(tool_request)

        history.append({"role": "assistant", "content": raw_response})
        history.append({"role": "user", "content": f"Tool result:\n{tool_result}"})

    raise MaxIterationsExceeded(
        f"Agent could not complete the task in {MAX_ITERATIONS} steps."
    )


def main():
    print("=" * 55)
    print("  EDIT AGENT — Agentic AI Project")
    print("=" * 55)
    print()
    print("Available tools: read_file, list_dir, write_file")
    print("Type 'quit' to exit.")
    print()

    history = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break

        history.append({"role": "user", "content": user_input})

        # For complex tasks, create a plan first and inject it
        # into the conversation so the agent follows it
        try:
            plan = plan_and_format(user_input)
            if plan:
                print()
                print("  [planner] Plan created — starting execution...")
                print()
                history.append({"role": "assistant", "content": plan})
        except Exception as e:
            print(f"  [planner] Planning skipped: {e}")

        try:
            result = run_agent_turn(history)
            print()
            print("Agent:", result)
            print()

        except MaxIterationsExceeded as e:
            print()
            print(f"Agent: I wasn't able to finish this task. {e}")
            print()
            # Remove the failed turn from history so it doesn't poison future turns
            history.append(
                {
                    "role": "assistant",
                    "content": "I was unable to complete the previous task.",
                }
            )


if __name__ == "__main__":
    main()
