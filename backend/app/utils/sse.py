from typing import Any, Dict
import json


def create_sse_event(data: Any, event_type: str = "message") -> str:
    """
    Create a Server-Sent Event string with the given data and event type.
    """
    event_str = f"event: {event_type}\n"
    event_str += f"data: {json.dumps(data)}\n\n"
    return event_str
