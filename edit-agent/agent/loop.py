"""
agent/loop.py

The core agent loop: think → act → observe → repeat.

The model is called repeatedly until it stops requesting tools
and produces a final plain text response.
"""

import json
from client import complete
from prompts import AGENT_SYSTEM_PROMPT
from tools.filesystem import read_file, list_dir, write_file


# Maps tool names (strings from the model) to actual Python functions
TOOL_REGISTRY = {
    "read_file": read_file,
    "list_dir": list_dir,
    "write_file": write_file,
}

MAX_ITERATIONS = 10  # safety cap — prevents infinite loops


def parse_tool_request(response: str) -> dict | None:
    """
    Check if the model's response is a JSON tool request.
    Returns the parsed dict if it is, or None if it's plain text.
    """
    stripped = response.strip()

    # Must start with { to even attempt JSON parsing
    if not stripped.startswith("{"):
        return None

    try:
        data = json.loads(stripped)
        if "tool" in data and "args" in data:
            return data
    except json.JSONDecodeError:
        pass

    return None


def run_tool(tool_request: dict) -> str:
    """
    Execute the tool the model requested.
    Returns the result as a string to feed back to the model.
    """
    tool_name = tool_request["tool"]
    args = tool_request["args"]

    if tool_name not in TOOL_REGISTRY:
        return f"Error: unknown tool '{tool_name}'. Available tools: {list(TOOL_REGISTRY.keys())}"

    tool_fn = TOOL_REGISTRY[tool_name]

    try:
        result = tool_fn(**args)
        return str(result)
    except TypeError as e:
        return f"Error calling tool '{tool_name}': {e}"


def run_agent(user_instruction: str) -> str:
    """
    Run the agent loop for a given user instruction.

    Keeps calling the model until it produces a final plain text answer
    or the iteration limit is reached.

    Args:
        user_instruction: The task the user wants the agent to perform.

    Returns:
        The agent's final plain text response.
    """
    print(f"\n[agent] Starting task: {user_instruction}")

    # Conversation history — grows as the loop progresses
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_instruction},
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"[agent] Iteration {iteration}")

        # Ask the model what to do next
        response = _call_model(messages)
        print(f"[agent] Model response: {response}")

        # Check if the model is requesting a tool
        tool_request = parse_tool_request(response)

        if tool_request is None:
            # No tool request — this is the final answer
            print("[agent] Task complete.")
            return response

        # Run the tool and get the result
        tool_name = tool_request["tool"]
        print(f"[agent] Running tool: {tool_name} with args: {tool_request['args']}")
        tool_result = run_tool(tool_request)
        print(f"[agent] Tool result: {tool_result}")

        # Add the model's tool request and the tool result to the conversation
        # so the model has full context on the next iteration
        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user", "content": f"Tool result: {tool_result}"})

    return "Error: agent reached maximum iterations without completing the task."


def _call_model(messages: list) -> str:
    """
    Call the model with the full conversation history.
    Private helper — only used inside this module.
    """
    from dotenv import load_dotenv
    import os

    load_dotenv()

    import requests

    model = os.getenv("DEFAULT_MODEL", "llama3.2")
    url = f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/chat"

    payload = {
        "model": model,
        "stream": False,
        "messages": messages,
    }

    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()["message"]["content"]
