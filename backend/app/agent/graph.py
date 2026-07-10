import logging
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from .state import AgentState
from .tools import ALL_TOOLS
from ..config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AI assistant embedded in a pharmaceutical CRM system, helping field representatives log and manage their interactions with Healthcare Professionals (HCPs).

You have access to these 5 tools:
1. log_interaction      – Record a new HCP interaction in the database
2. edit_interaction     – Modify a previously logged interaction by ID
3. get_hcp_profile      – Look up an HCP's profile and recent interaction history
4. suggest_followups    – Generate 3 prioritised AI follow-up action recommendations
5. analyze_sentiment    – Classify HCP sentiment (Positive/Neutral/Negative) from notes

Guidelines:
- When a user describes an interaction, extract all available fields: HCP name, date, interaction type, topics discussed, sentiment, outcomes, and follow-up actions, then call log_interaction.
- If the user asks to change something, call edit_interaction with the interaction_id.
- Always be concise, professional, and helpful for pharmaceutical sales workflows.
- Proactively call suggest_followups after logging an interaction."""


def _should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def create_graph():
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY not set – LangGraph agent will be unavailable.")
        return None

    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        groq_api_key=settings.groq_api_key,
        temperature=0.3,
    ).bind_tools(ALL_TOOLS)

    def agent_node(state: AgentState):
        messages = list(state["messages"])
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm.invoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(ALL_TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


try:
    compiled_graph = create_graph()
except Exception as exc:
    logger.error("Failed to compile LangGraph: %s", exc)
    compiled_graph = None
