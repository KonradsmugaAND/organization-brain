"""ClickUpAgent — exports tasks to ClickUp."""

from google.adk.agents import Agent

from app.tools import create_clickup_task, export_inbox_to_clickup

_instruction = """
You are ClickUpAgent — WenetBrain's task exporter.

Your job:
1. Receive task details (name, assignee, due_date, description).
2. Call `create_clickup_task` to push the task to ClickUp.
3. Or call `export_inbox_to_clickup` to export an existing inbox item.

Return the ClickUp task ID or mock confirmation.
"""

clickup_agent = Agent(
    name="clickup_agent",
    model="gemini-2.5-flash",
    description="Exports action items to ClickUp.",
    instruction=_instruction,
    tools=[create_clickup_task, export_inbox_to_clickup],
)
