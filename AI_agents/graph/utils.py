"""
Utility functions for LangGraph state management.
"""


def escape_braces(text: str) -> str:
    """
    Escape curly braces in text to prevent f-string format errors.

    When error messages or dynamic content contain {} braces and are
    inserted into f-strings, Python interprets them as format specifiers.
    This function escapes them to prevent that.

    Args:
        text: String that may contain braces

    Returns:
        String with braces escaped ({{ and }})
    """
    if not isinstance(text, str):
        text = str(text)
    return text.replace("{", "{{").replace("}", "}}")
