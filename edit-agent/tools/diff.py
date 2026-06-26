"""
tools/diff.py

Generates human-readable diffs between original and proposed file content.

Used by the agent before applying any edit — the user sees exactly
what will change before it happens. Nothing is written until approved.
"""

import difflib


def generate_diff(original: str, proposed: str, filename: str = "file") -> str:
    """
    Compare original and proposed content and return a readable diff.

    Each changed line is shown as:
        - removed line    (what was there before)
        + added line      (what will replace it)
      unchanged line      (context — lines around the change)

    Args:
        original: The current content of the file.
        proposed: The new content the agent wants to write.
        filename: The filename to show in the diff header.

    Returns:
        A formatted string showing all differences.
        Returns a message if the content is identical.
    """

    # splitlines(keepends=True) splits a string into a list of lines
    # keepends=True means it keeps the newline character at the end of each line
    # This is what difflib needs to work correctly
    # Example: "hello\nworld\n" → ["hello\n", "world\n"]
    original_lines = original.splitlines(keepends=True)
    proposed_lines = proposed.splitlines(keepends=True)

    # unified_diff compares two lists of lines and generates the diff
    # n=3 means show 3 lines of context around each change (standard convention)
    # fromfile/tofile are the labels shown in the diff header
    diff = list(
        difflib.unified_diff(
            original_lines,
            proposed_lines,
            fromfile=f"{filename} (original)",
            tofile=f"{filename} (proposed)",
            n=3,
        )
    )

    # If diff is empty, the two versions are identical
    if not diff:
        return f"No changes detected in '{filename}'."

    # Join all the diff lines into one readable string
    # Each line already has its +/- prefix from unified_diff
    return "".join(diff)


def has_changes(original: str, proposed: str) -> bool:
    """
    Quick check — are the two versions different at all?

    Args:
        original: The current file content.
        proposed: The proposed new content.

    Returns:
        True if there are differences, False if they are identical.
    """
    return original.strip() != proposed.strip()
