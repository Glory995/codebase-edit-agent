"""
prompts.py

Prompt templates for the Edit Agent.
All prompts live here — never scattered inline across the codebase.
This makes the agent's behaviour easy to audit and tune in one place.
"""


# ---------------------------------------------------------------------------
# System prompt — the agent's permanent identity and rules
# ---------------------------------------------------------------------------

AGENT_SYSTEM_PROMPT = """You are an expert coding assistant and file-editing agent.

Your job is to help users read, understand, and edit code files.

Rules you must always follow:
- Be precise and concise. No filler text, no unnecessary explanation.
- When asked to analyse a file, report only what is relevant to the user's request.
- When asked to plan edits, list each change clearly and separately.
- Never make up file contents. Only work with what you are given.
- If you are unsure about something, say so explicitly.
"""


# ---------------------------------------------------------------------------
# User prompt templates — one function per task type
# ---------------------------------------------------------------------------


def prompt_summarise_file(filename: str, content: str) -> str:
    """Return a prompt asking the agent to summarise a file."""
    return f"""Please summarise the following file.

File: {filename}
---
{content}
---

Provide:
1. What this file does in one sentence.
2. The key functions or classes (just names + one-line description each).
3. Any obvious issues or things worth noting.
"""


def prompt_plan_edit(filename: str, content: str, instruction: str) -> str:
    """Return a prompt asking the agent to plan (not yet apply) an edit."""
    return f"""You are about to edit a file. First, produce a clear plan — do not make any changes yet.

File: {filename}
Instruction: {instruction}
---
{content}
---

List each change you would make, one per line, as:
CHANGE: <what you will do and where>

Do not write any code yet. Plan only.
"""
