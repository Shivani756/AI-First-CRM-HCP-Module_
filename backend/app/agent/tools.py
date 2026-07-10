"""
LangGraph tools for the HCP CRM AI agent.
Each tool runs synchronously inside a thread pool (called via run_in_executor from FastAPI).
Async DB operations are handled via asyncio.new_event_loop() inside each thread so that
psycopg2 / a sync driver is not required.
"""
import asyncio
import json
from typing import Optional
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from sqlalchemy import select
from ..database import AsyncSessionLocal
from ..models.interaction import Interaction
from ..models.hcp import HCP
from ..config import settings


def _run_async(coro):
    """Execute an async coroutine synchronously.
    Safe to call from threads spawned by run_in_executor because each thread
    gets its own event loop.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _get_llm(model: str = "llama-3.1-8b-instant"):
    return ChatGroq(
        model=model,
        groq_api_key=settings.groq_api_key,
        temperature=0.3,
        max_tokens=512,
    )


# ─────────────────────────────────────────────
# Tool 1 – Log Interaction
# ─────────────────────────────────────────────
@tool
def log_interaction(
    hcp_name: str,
    interaction_type: str = "Meeting",
    date: str = "",
    time: str = "",
    attendees: str = "",
    topics_discussed: str = "",
    sentiment: str = "Neutral",
    outcomes: str = "",
    follow_up_actions: str = "",
    raw_description: str = "",
) -> str:
    """
    Log a new HCP (Healthcare Professional) interaction to the CRM database.
    Use this tool whenever the user wants to record or save a new interaction.
    The LLM will generate an AI summary from the topics and raw description.
    Returns JSON with interaction_id, hcp_name, ai_summary, and a success message.
    """
    ai_summary = ""

    # Use LLM to generate summary if content is available
    if settings.groq_api_key and (topics_discussed or raw_description):
        content = raw_description or topics_discussed
        try:
            llm = _get_llm()
            prompt = (
                "Summarize this HCP pharmaceutical interaction in 2-3 concise sentences. "
                "Highlight key medical topics, product discussions, and outcomes.\n\n"
                f"Interaction notes: {content}\n\nSummary:"
            )
            ai_summary = llm.invoke(prompt).content.strip()
        except Exception:
            ai_summary = (topics_discussed or raw_description)[:200]
    else:
        ai_summary = (topics_discussed or raw_description)[:200]

    async def _save():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(HCP).where(HCP.name.ilike(f"%{hcp_name}%")))
            hcp = result.scalar_one_or_none()
            hcp_id = hcp.id if hcp else None

            interaction = Interaction(
                hcp_id=hcp_id,
                hcp_name=hcp_name,
                interaction_type=interaction_type,
                date=date,
                time=time,
                attendees=attendees,
                topics_discussed=topics_discussed,
                materials_shared=[],
                samples_distributed=[],
                sentiment=sentiment,
                outcomes=outcomes,
                follow_up_actions=follow_up_actions,
                ai_summary=ai_summary,
                ai_suggested_followups=[],
            )
            db.add(interaction)
            await db.commit()
            await db.refresh(interaction)
            return interaction

    try:
        interaction = _run_async(_save())
        return json.dumps({
            "success": True,
            "interaction_id": interaction.id,
            "hcp_name": interaction.hcp_name,
            "ai_summary": interaction.ai_summary,
            "message": f"Interaction with {hcp_name} logged successfully (ID: {interaction.id}).",
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# ─────────────────────────────────────────────
# Tool 2 – Edit Interaction
# ─────────────────────────────────────────────
@tool
def edit_interaction(
    interaction_id: int,
    hcp_name: Optional[str] = None,
    interaction_type: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    attendees: Optional[str] = None,
    topics_discussed: Optional[str] = None,
    sentiment: Optional[str] = None,
    outcomes: Optional[str] = None,
    follow_up_actions: Optional[str] = None,
) -> str:
    """
    Edit or update an existing logged HCP interaction by its numeric ID.
    Use this tool when the user wants to modify or correct a previously saved interaction.
    Only supply the fields that need to change; omit fields that should remain unchanged.
    Returns JSON with the updated field names and a success message.
    """
    async def _update():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Interaction).where(Interaction.id == interaction_id))
            interaction = result.scalar_one_or_none()
            if not interaction:
                return None

            updated_fields = []
            field_map = {
                "hcp_name": hcp_name,
                "interaction_type": interaction_type,
                "date": date,
                "time": time,
                "attendees": attendees,
                "topics_discussed": topics_discussed,
                "sentiment": sentiment,
                "outcomes": outcomes,
                "follow_up_actions": follow_up_actions,
            }
            for field, value in field_map.items():
                if value is not None:
                    setattr(interaction, field, value)
                    updated_fields.append(field)

            await db.commit()
            await db.refresh(interaction)
            return updated_fields

    try:
        updated = _run_async(_update())
        if updated is None:
            return json.dumps({"success": False, "error": f"No interaction found with ID {interaction_id}."})
        return json.dumps({
            "success": True,
            "interaction_id": interaction_id,
            "updated_fields": updated,
            "message": f"Interaction {interaction_id} updated. Changed: {', '.join(updated)}.",
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# ─────────────────────────────────────────────
# Tool 3 – Get HCP Profile
# ─────────────────────────────────────────────
@tool
def get_hcp_profile(hcp_name: str) -> str:
    """
    Retrieve an HCP's profile details and their 5 most recent interaction records.
    Use this tool when the user asks about a specific doctor, their background,
    contact details, specialty, or previous engagement history.
    Returns JSON with HCP profile and recent interactions list.
    """
    async def _fetch():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(HCP).where(HCP.name.ilike(f"%{hcp_name}%")))
            hcp = result.scalar_one_or_none()
            if not hcp:
                return None

            r2 = await db.execute(
                select(Interaction)
                .where(Interaction.hcp_id == hcp.id)
                .order_by(Interaction.created_at.desc())
                .limit(5)
            )
            recent = r2.scalars().all()
            return hcp, recent

    try:
        data = _run_async(_fetch())
        if data is None:
            return json.dumps({"success": False, "message": f"No HCP found matching '{hcp_name}'."})
        hcp, recent = data
        interactions_data = [
            {
                "id": i.id,
                "date": i.date,
                "type": i.interaction_type,
                "topics": i.topics_discussed,
                "sentiment": i.sentiment,
                "outcomes": i.outcomes,
            }
            for i in recent
        ]
        return json.dumps({
            "success": True,
            "hcp": {
                "id": hcp.id,
                "name": hcp.name,
                "specialty": hcp.specialty,
                "organization": hcp.organization,
                "email": hcp.email,
                "phone": hcp.phone,
            },
            "recent_interactions": interactions_data,
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# ─────────────────────────────────────────────
# Tool 4 – Suggest Follow-ups
# ─────────────────────────────────────────────
@tool
def suggest_followups(
    hcp_name: str = "",
    topics_discussed: str = "",
    outcomes: str = "",
    sentiment: str = "Neutral",
    interaction_id: Optional[int] = None,
) -> str:
    """
    Generate 3 prioritized AI-powered follow-up action suggestions for a pharmaceutical field rep.
    Use this tool when the user asks for next steps, follow-up recommendations, or action items
    after an HCP interaction. Tailors suggestions based on interaction context and HCP sentiment.
    Returns JSON with a list of 3 specific follow-up suggestions.
    """
    # Load from DB if interaction_id provided
    if interaction_id:
        async def _load():
            async with AsyncSessionLocal() as db:
                r = await db.execute(select(Interaction).where(Interaction.id == interaction_id))
                return r.scalar_one_or_none()
        try:
            i = _run_async(_load())
            if i:
                hcp_name = hcp_name or i.hcp_name or ""
                topics_discussed = topics_discussed or i.topics_discussed or ""
                outcomes = outcomes or i.outcomes or ""
                sentiment = sentiment or i.sentiment or "Neutral"
        except Exception:
            pass

    if not settings.groq_api_key:
        return json.dumps({
            "success": True,
            "suggestions": [
                f"Schedule a follow-up meeting with {hcp_name} within 2 weeks.",
                "Send relevant clinical data or product publications.",
                "Add to advisory board invite list if sentiment is positive.",
            ],
        })

    context = "\n".join(filter(None, [
        f"HCP: {hcp_name}" if hcp_name else "",
        f"Topics discussed: {topics_discussed}" if topics_discussed else "",
        f"Outcomes: {outcomes}" if outcomes else "",
        f"HCP Sentiment: {sentiment}",
    ]))

    try:
        llm = _get_llm("llama-3.3-70b-versatile")
        prompt = (
            "You are a pharmaceutical field representative assistant. "
            "Based on this HCP interaction, provide exactly 3 specific, actionable follow-up suggestions "
            "for the sales rep. Be concise and practical. Number each suggestion.\n\n"
            f"Interaction Context:\n{context}\n\n"
            "3 Prioritized Follow-up Actions:"
        )
        response = llm.invoke(prompt).content.strip()
        lines = [l.strip() for l in response.split("\n") if l.strip() and any(c.isalpha() for c in l)]
        suggestions = [l.lstrip("0123456789.-) ").strip() for l in lines if l.lstrip("0123456789.-) ").strip()][:3]
        if not suggestions:
            suggestions = [response[:200]]
        return json.dumps({"success": True, "suggestions": suggestions})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# ─────────────────────────────────────────────
# Tool 5 – Analyze Sentiment
# ─────────────────────────────────────────────
@tool
def analyze_sentiment(
    text: str = "",
    interaction_id: Optional[int] = None,
) -> str:
    """
    Analyze and classify an HCP's observed sentiment (Positive, Neutral, or Negative)
    from interaction notes, conversation text, or topics discussed.
    Use this tool when the user wants to understand the HCP's attitude toward the rep or product.
    Returns JSON with sentiment classification, confidence level, and reasoning.
    """
    if not text and interaction_id:
        async def _load_text():
            async with AsyncSessionLocal() as db:
                r = await db.execute(select(Interaction).where(Interaction.id == interaction_id))
                i = r.scalar_one_or_none()
                if i:
                    return " ".join(filter(None, [i.topics_discussed, i.outcomes]))
                return ""
        try:
            text = _run_async(_load_text())
        except Exception:
            text = ""

    if not text:
        return json.dumps({"success": False, "error": "No text provided for sentiment analysis."})

    if not settings.groq_api_key:
        return json.dumps({
            "success": True,
            "sentiment": "Neutral",
            "confidence": "Low",
            "reasoning": "API key not configured; defaulting to Neutral.",
        })

    try:
        llm = _get_llm()
        prompt = (
            "Analyze the HCP's (Healthcare Professional's) sentiment toward the pharmaceutical "
            "representative based on the following interaction notes. Classify as Positive, Neutral, or Negative.\n\n"
            f"Interaction notes: {text}\n\n"
            "Respond in EXACTLY this format:\n"
            "Sentiment: [Positive/Neutral/Negative]\n"
            "Confidence: [High/Medium/Low]\n"
            "Reasoning: [1-2 sentence explanation]"
        )
        response = llm.invoke(prompt).content.strip()

        sentiment = "Neutral"
        confidence = "Medium"
        reasoning = response

        for line in response.split("\n"):
            lower = line.lower()
            if lower.startswith("sentiment:"):
                val = line.split(":", 1)[1].strip().lower()
                if "positive" in val:
                    sentiment = "Positive"
                elif "negative" in val:
                    sentiment = "Negative"
                else:
                    sentiment = "Neutral"
            elif lower.startswith("confidence:"):
                confidence = line.split(":", 1)[1].strip()
            elif lower.startswith("reasoning:"):
                reasoning = line.split(":", 1)[1].strip()

        return json.dumps({
            "success": True,
            "sentiment": sentiment,
            "confidence": confidence,
            "reasoning": reasoning,
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


ALL_TOOLS = [log_interaction, edit_interaction, get_hcp_profile, suggest_followups, analyze_sentiment]
