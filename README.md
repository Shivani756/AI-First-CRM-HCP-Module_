# AI-First CRM – HCP Module: Log Interaction Screen

A full-stack pharmaceutical CRM application for field representatives to log their interactions with Healthcare Professionals (HCPs). Supports both a **structured form** and a **conversational AI chat** interface powered by LangGraph + Groq.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Redux Toolkit, Vite, Google Inter |
| Backend | Python 3.11+, FastAPI |
| AI Agent | LangGraph, LangChain |
| LLM | Groq – `gemma2-9b-it` (primary), `llama-3.3-70b-versatile` (follow-ups) |
| Database | PostgreSQL (async via asyncpg + SQLAlchemy 2.0) |

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan
│   │   ├── config.py            # Pydantic settings (reads .env)
│   │   ├── database.py          # Async + sync SQLAlchemy engines
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── hcp.py
│   │   │   ├── interaction.py
│   │   │   └── material.py
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── api/
│   │   │   ├── hcps.py          # HCP + materials endpoints
│   │   │   ├── interactions.py  # CRUD for interactions
│   │   │   └── agent.py         # LangGraph chat endpoint
│   │   └── agent/
│   │       ├── state.py         # AgentState TypedDict
│   │       ├── tools.py         # 5 LangGraph tools
│   │       └── graph.py         # StateGraph definition
│   ├── seed.py                  # Seed DB with sample HCPs + materials
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── store/               # Redux slices (interaction, agent, hcp)
    │   ├── components/
    │   │   ├── LogInteractionForm/
    │   │   └── AIAssistantChat/
    │   └── services/api.js      # Axios API client
    ├── index.html
    ├── package.json
    └── vite.config.js           # Dev proxy → backend:8000
```

---

## LangGraph Agent & Tools

The LangGraph `StateGraph` runs with `gemma2-9b-it` via the Groq API. The agent receives the chat message, decides which tool to call, executes it synchronously in a thread pool, and returns a structured response that auto-populates the form.

| # | Tool | Description |
|---|------|-------------|
| 1 | `log_interaction` | Extracts entities (HCP, date, topics, sentiment) from free text using the LLM, generates an AI summary, and inserts the record into PostgreSQL. |
| 2 | `edit_interaction` | Parses the user's edit intent and updates only the specified fields of an existing interaction by ID. |
| 3 | `get_hcp_profile` | Fetches HCP details (specialty, organisation, contact) and their 5 most recent interactions from the DB. |
| 4 | `suggest_followups` | Calls `llama-3.3-70b-versatile` with interaction context to generate 3 prioritised, pharma-specific follow-up actions. |
| 5 | `analyze_sentiment` | Classifies HCP sentiment (Positive / Neutral / Negative) from interaction notes, returning confidence level and reasoning. |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL running locally (default port 5432)
- A free [Groq API key](https://console.groq.com)

---

### 1. Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set:
#   DATABASE_URL=postgresql+asyncpg://USER:PASS@localhost:5432/crm_hcp
#   SYNC_DATABASE_URL=postgresql+psycopg2://USER:PASS@localhost:5432/crm_hcp
#   GROQ_API_KEY=your_key_here

# Create the database (psql)
psql -U postgres -c "CREATE DATABASE crm_hcp;"

# Seed sample data (creates tables automatically on first run)
python seed.py

# Start the API server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

### 2. Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (proxies /api → http://localhost:8000)
npm run dev
```

App available at: http://localhost:5173

---

## Key Features

- **Dual-mode logging**: Fill the structured form manually, or describe the interaction in natural language in the AI chat — the form auto-populates from extracted fields.
- **AI Summary**: `log_interaction` tool uses the LLM to generate a concise 2-3 sentence summary of the interaction.
- **AI Follow-up Suggestions**: The agent proactively calls `suggest_followups` after logging; suggestions appear in the form and can be accepted with one click.
- **Sentiment Analysis**: The AI infers HCP sentiment and sets the radio button automatically.
- **Quick prompts**: One-click prompts in the chat panel for common tasks.
- **Session persistence**: Chat history maintained in memory per session ID.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/hcps?q=` | Search HCPs by name |
| GET | `/api/hcps/{id}` | Get single HCP |
| GET | `/api/materials?q=` | Search materials |
| POST | `/api/interactions` | Create interaction |
| GET | `/api/interactions` | List all interactions |
| GET | `/api/interactions/{id}` | Get single interaction |
| PUT | `/api/interactions/{id}` | Update interaction |
| POST | `/api/agent/chat` | Send message to AI agent |
| DELETE | `/api/agent/chat/{session_id}` | Clear session history |

---

## Environment Variables

### Backend (`backend/.env`)
```
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/crm_hcp
SYNC_DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/crm_hcp
GROQ_API_KEY=gsk_...
```

### Frontend (`frontend/.env`) — optional
```
VITE_API_URL=http://localhost:8000
```
> The Vite dev proxy handles `/api` requests automatically, so this is only needed for production builds.
