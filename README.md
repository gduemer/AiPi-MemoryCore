# AiPi-MemoryCore

> Conversation ingestion, pod segmentation, memory core, and dashboard for AiPi
> Phase 1 through 5 memory architecture.

---

## Architecture

```
AiPi-MemoryCore/
    conversation_ingest/
        ingest.py              # Phase 1: Signal extraction from exported conversations
        raw_markdown/          # Drop exported .md or .json files here
        extracted_json/        # Auto-generated structured JSON output

    memory_core/
        models.py              # SQLAlchemy ORM: Conversation, Decision, OpenLoop, Pod, Project
        projects.db            # SQLite database (auto-created)

    dashboard/
        app.py                 # Phase 5: FastAPI metrics API
        static/                # Chart.js + D3 word cloud frontend (coming)
```

---

## Five Phases

| Phase | Name | What it does |
|-------|------|--------------|
| 1 | Event Extraction | Parse conversations.json, extract decisions/promises/deadlines/emotions/tech/loops |
| 2 | Pod Segmentation | Cluster extracted signals via sentence-transformers + HDBSCAN |
| 3 | Category Synthesis | Name each pod cluster, cap at 12 categories |
| 4 | Project Alignment | Map pods to existing or new projects |
| 5 | Dashboard | FastAPI + Chart.js gauges and D3 word cloud |

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/gduemer/AiPi-MemoryCore.git
cd AiPi-MemoryCore
pip install -r requirements.txt

# 2. Export your ChatGPT conversations
# Settings > Data controls > Export data
# Unzip and find conversations.json

# 3. Run Phase 1 ingest
python conversation_ingest/ingest.py path/to/conversations.json

# 4. Initialise the database
python memory_core/models.py

# 5. Launch the dashboard
uvicorn dashboard.app:app --reload --port 8000
# Open http://localhost:8000/docs
```

---

## Dashboard Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /metrics/summary` | Gauges: open loops, completion ratio, fragmentation index |
| `GET /metrics/open_loops` | Heatmap: unresolved loops sorted by days open |
| `GET /metrics/tech_stack` | Word cloud data: tech keyword frequencies |
| `GET /metrics/projects` | Per-project activity and completion ratios |
| `GET /metrics/emotional_volatility` | Emotion marker frequencies across all conversations |

---

## Key Metrics

- **Open Loops Count** - conversations with unresolved items
- **Completion Ratio** - `executed_decisions / total_decisions`
- **Fragmentation Index** - `pod_count / active_projects`
- **Stale Thread Count** - conversations not referenced in 90+ days
- **Emotional Volatility** - frequency of fear/stuck/frustrated markers

---

## 90-Day Downgrade Rule

Any idea not referenced within 90 days is downgraded to `archived` unless
the parent project is tagged `is_strategic = True`. This prevents cognitive hoarding.

---

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, SQLite
- **AI/Embeddings**: sentence-transformers, HDBSCAN, scikit-learn
- **Frontend**: Chart.js, ECharts, D3 (word cloud)
- **Dev**: uvicorn, pydantic, python-dotenv

---

## Part of AiPi

This is the memory substrate for the AiPi agent system.
AiPi Core ingests this module to maintain cross-session context.

```
AiPi Core
  └── Memory Module (AiPi-MemoryCore)
       ├── Conversation Ingest
       ├── Pod Segmentation
       ├── Project Alignment
       └── Dashboard API
```

---

*Start with 50 conversations. Extract decisions. Count open loops. Display one gauge.
You will learn more from imperfection than overdesign.*
