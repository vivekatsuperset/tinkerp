import json
import re
from typing import Any


def sanitize_json_string(json_str: str | dict | list) -> dict[str, Any] | list[dict[str, Any]]:
    """Sanitize a JSON string that might contain problematic control characters."""
    if isinstance(json_str, (dict, list)):
        return json_str

    if json_str.startswith("```json"):
        json_str = json_str.replace("```json", "", 1)
    if json_str.endswith("```"):
        json_str = json_str.replace("```", "", 1)

    # Remove backslashes used for line continuation
    # json_str = json_str.replace(" \\n", " ")  # Fix misplaced backslashes before newlines
    # json_str = json_str.replace("\\n", " ")   # Remove any unnecessary newlines in the SQL query
    json_str = json_str.replace("\\", "")  # Remove stray backslashes

    # Remove any unintended control characters (just in case)
    json_str = re.sub(r"[\x00-\x1F]+", " ", json_str)  # Remove invalid control characters

    # Remove any potential BOM and normalize newlines
    json_str = json_str.strip().replace('\r\n', '\n')
    try:
        # First try to parse it as is
        return json.loads(json_str)
    except json.JSONDecodeError:
        # If that fails, try to normalize the string
        # This handles cases where the string might have been pretty-printed or contains special characters
        try:
            # Parse it as a Python literal (safer than eval)
            import ast
            parsed = ast.literal_eval(json_str)
            if isinstance(parsed, (dict, list)):
                return parsed
        except:
            pass
        # If all else fails, try to clean up the string
        try:
            # Remove any leading/trailing whitespace from lines
            lines = [line.strip() for line in json_str.split('\n')]
            cleaned = '\n'.join(line for line in lines if line)
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse JSON string: {e}")
