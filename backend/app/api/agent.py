import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from langchain_core.messages import HumanMessage, AIMessage

router = APIRouter(prefix="/api/agent", tags=["Agent"])
logger = logging.getLogger(__name__)

# Thread pool for running the synchronous LangGraph graph
_executor = ThreadPoolExecutor(max_workers=4)

# In-memory session store  — replace with Redis in production
_sessions: dict[str, list] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    extracted_fields: Optional[dict] = None
    tool_calls_made: list = []
    interaction_id: Optional[int] = None


def _run_graph(state: dict) -> dict:
    """Synchronous wrapper – runs inside thread pool so it doesn't block the event loop."""
    from ..agent.graph import compiled_graph
    if compiled_graph is None:
        raise RuntimeError("LangGraph agent is not initialised. Check GROQ_API_KEY.")
    return compiled_graph.invoke(state)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id

    if session_id not in _sessions:
        _sessions[session_id] = []

    _sessions[session_id].append(HumanMessage(content=request.message))

    from ..agent.state import AgentState
    state: AgentState = {
        "messages": list(_sessions[session_id]),
        "session_id": session_id,
        "extracted_fields": {},
        "current_interaction_id": None,
    }

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(_executor, _run_graph, state)
    except RuntimeError as exc:
        return ChatResponse(
            reply=str(exc),
            extracted_fields={},
            tool_calls_made=[],
            interaction_id=None,
        )

    all_messages = result["messages"]
    _sessions[session_id] = all_messages

    # ── Extract reply ──────────────────────────────────────────────────────────
    reply = ""
    for msg in reversed(all_messages):
        if not isinstance(msg, AIMessage):
            continue
        # Skip messages that triggered tool calls — they have no user-visible text
        if msg.tool_calls:
            continue
        # Content may be a plain string or a list of content blocks
        if isinstance(msg.content, str) and msg.content.strip():
            reply = msg.content.strip()
            break
        if isinstance(msg.content, list):
            parts = [b.get("text", "") if isinstance(b, dict) else str(b) for b in msg.content]
            text = " ".join(p for p in parts if p).strip()
            if text:
                reply = text
                break
    if not reply:
        reply = "I've processed your request."

    # ── Extract tool call arguments (for form auto-population) ─────────────────
    extracted_fields: dict = {}
    tool_calls_made: list[str] = []
    interaction_id: Optional[int] = None

    for msg in all_messages:
        # AIMessage with tool_calls → get the arguments the LLM chose
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_name = tc.get("name", "")
                tool_calls_made.append(tool_name)
                if tool_name == "log_interaction":
                    args = {k: v for k, v in tc.get("args", {}).items() if k != "raw_description"}
                    extracted_fields.update(args)

        # ToolMessage → get the results
        if hasattr(msg, "name") and msg.name:
            try:
                data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                if isinstance(data, dict):
                    if msg.name == "log_interaction" and data.get("interaction_id"):
                        interaction_id = data["interaction_id"]
                        extracted_fields["ai_summary"] = data.get("ai_summary", "")
                    if msg.name == "suggest_followups" and data.get("suggestions"):
                        extracted_fields["ai_suggested_followups"] = data["suggestions"]
                    if msg.name == "analyze_sentiment" and data.get("sentiment"):
                        extracted_fields["sentiment"] = data["sentiment"]
            except (json.JSONDecodeError, TypeError):
                pass

    return ChatResponse(
        reply=reply,
        extracted_fields=extracted_fields if extracted_fields else None,
        tool_calls_made=list(dict.fromkeys(tool_calls_made)),  # deduplicated
        interaction_id=interaction_id,
    )


@router.delete("/chat/{session_id}")
async def clear_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"message": f"Session '{session_id}' cleared."}
