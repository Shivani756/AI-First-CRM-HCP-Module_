from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    session_id: str
    extracted_fields: dict
    current_interaction_id: Optional[int]
