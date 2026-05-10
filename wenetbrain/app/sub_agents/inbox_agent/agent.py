"""InboxAgent — manages HITL approval queue."""

from google.adk.agents import Agent

from app.tools import (
    approve_inbox_item,
    create_inbox_item,
    get_inbox_items,
    reject_inbox_item,
)

_instruction = """
You are InboxAgent — WenetBrain's human-in-the-loop coordinator.

Your job:
1. Create inbox items via `create_inbox_item`.
2. List pending items via `get_inbox_items`.
3. Approve or reject items via `approve_inbox_item` and `reject_inbox_item`.

When approving, the item becomes visible in the knowledge bank.
When rejecting, it is discarded.
"""

inbox_agent = Agent(
    name="inbox_agent",
    model="gemini-2.5-flash",
    description="Manages HITL approval queue for meeting notes and tasks.",
    instruction=_instruction,
    tools=[create_inbox_item, get_inbox_items, approve_inbox_item, reject_inbox_item],
)
