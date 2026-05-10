"""RoutingAgent — decides which knowledge banks a meeting chunk should go to."""


from google.adk.agents import Agent


def route_to_banks(
    meeting_type: str,
    participants: list[str],
    company_id: str = "webwave",
) -> dict:
    """Determine destination banks for a meeting based on its type.

    Args:
        meeting_type: One of team, cross, oneonone, allhands.
        participants: List of participant identifiers.
        company_id: Company identifier.

    Returns:
        JSON with list of {bank_id, status} destinations.
    """
    destinations = []
    mt = meeting_type.lower()

    if mt == "team":
        destinations.append({"bank_id": f"team_product_{company_id}", "status": "pending_approval"})
        for p in participants:
            destinations.append({"bank_id": f"private_{p}", "status": "approved"})
    elif mt == "cross":
        destinations.append({"bank_id": f"company_{company_id}", "status": "pending_approval"})
        # simplified: assume all participants belong to team_product for PoC
        destinations.append({"bank_id": f"team_product_{company_id}", "status": "pending_approval"})
        for p in participants:
            destinations.append({"bank_id": f"private_{p}", "status": "approved"})
    elif mt == "oneonone":
        for p in participants:
            destinations.append({"bank_id": f"private_{p}", "status": "approved"})
    elif mt == "allhands":
        destinations.append({"bank_id": "group", "status": "pending_approval"})
        destinations.append({"bank_id": f"company_{company_id}", "status": "pending_approval"})
        for p in participants:
            destinations.append({"bank_id": f"private_{p}", "status": "approved"})

    return {"destinations": destinations}


_instruction = """
You are RoutingAgent — WenetBrain's knowledge router.

Your job:
1. Receive meeting_type and participants.
2. Call `route_to_banks` to get the list of destination banks.
3. Return the routing decision as JSON.
"""

routing_agent = Agent(
    name="routing_agent",
    model="gemini-2.5-flash",
    description="Routes meeting notes to the correct knowledge banks.",
    instruction=_instruction,
    tools=[route_to_banks],
)
