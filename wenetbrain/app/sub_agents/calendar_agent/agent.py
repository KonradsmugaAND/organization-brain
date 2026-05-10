"""CalendarAgent — syncs with Microsoft 365 Calendar."""

from google.adk.agents import Agent

from app.tools import get_calendar_events


def suggest_meeting_type(attendees: list[str]) -> str:
    """Suggest meeting type based on attendee list.

    Args:
        attendees: List of attendee names/emails.

    Returns:
        Suggested meeting type: team, cross, oneonone, allhands.
    """
    if len(attendees) <= 2:
        return "oneonone"
    if len(attendees) > 10:
        return "allhands"
    return "cross"


_instruction = """
You are CalendarAgent — WenetBrain's calendar assistant.

Your job:
1. Fetch upcoming events via `get_calendar_events`.
2. Suggest meeting type via `suggest_meeting_type`.
3. Return the event list with suggestions.
"""

calendar_agent = Agent(
    name="calendar_agent",
    model="gemini-2.5-flash",
    description="Fetches calendar events and suggests meeting types.",
    instruction=_instruction,
    tools=[get_calendar_events, suggest_meeting_type],
)
