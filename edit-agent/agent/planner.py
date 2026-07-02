"""
agent/planner.py

Produces a step-by-step plan before the agent starts acting.

For simple tasks (single file, single action) planning is skipped.
For complex tasks (multiple files, multiple changes) a plan is
produced first so the agent works in a predictable, ordered way.
"""

from client import complete
from prompts import AGENT_SYSTEM_PROMPT, prompt_create_plan
from tools.filesystem import list_dir


# Tasks longer than this word count get a plan first
# Short tasks like "read client.py" don't need planning overhead
PLANNING_THRESHOLD_WORDS = 8


def needs_planning(instruction: str) -> bool:
    """
    Decide whether this instruction is complex enough to warrant a plan.

    Simple heuristic: if the instruction is longer than a threshold
    or contains keywords that suggest multi-step work, plan first.

    Args:
        instruction: The user's raw instruction.

    Returns:
        True if a plan should be created first, False for simple tasks.
    """
    word_count = len(instruction.split())
    if word_count > PLANNING_THRESHOLD_WORDS:
        return True

    # Keywords that suggest multi-step or multi-file work
    complex_keywords = [
        "all",
        "every",
        "each",
        "multiple",
        "fix",
        "refactor",
        "improve",
        "update",
        "and then",
        "after that",
        "also",
    ]

    instruction_lower = instruction.lower()
    return any(keyword in instruction_lower for keyword in complex_keywords)


def create_plan(instruction: str) -> str:
    """
    Ask the model to produce a step-by-step plan for the given instruction.

    Passes the current workspace listing so the model knows what files exist
    before planning which ones to touch.

    Args:
        instruction: The user's instruction to plan for.

    Returns:
        The model's plan as a plain text string.
    """
    # Give the planner a view of what's in the workspace
    # so it can reference specific files by name in its plan
    try:
        file_listing = list_dir(".")
    except Exception:
        file_listing = "Could not list workspace contents."

    planning_prompt = prompt_create_plan(instruction, file_listing)

    print("  [planner] Creating plan...")
    plan = complete(
        system_prompt=AGENT_SYSTEM_PROMPT,
        user_prompt=planning_prompt,
    )
    return plan


def plan_and_format(instruction: str) -> str | None:
    """
    Check if planning is needed and return a plan if so.

    This is the main entry point called by the agent loop.

    Args:
        instruction: The user's instruction.

    Returns:
        A formatted plan string to inject into the conversation,
        or None if the task is simple enough to skip planning.
    """
    if not needs_planning(instruction):
        return None

    plan = create_plan(instruction)

    # Format the plan clearly so it shows up well in the conversation
    return f"""I have created a plan for this task:

{plan}

I will now execute this plan step by step.
"""
