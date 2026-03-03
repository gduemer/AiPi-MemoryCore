Here’s a `SystemProposal_2.md` you can drop into the repo root.

***

```markdown
# SystemProposal_2: AiPi-MemoryCore as a Pluggable Memory “Thumb Drive”

## 1. Vision

AiPi-MemoryCore evolves from a single-purpose ChatGPT export analyzer into a **pluggable, project-agnostic memory service** that behaves like a USB thumb drive for AI systems: you “plug it into” any project to gain rich, structured memory and RAG capabilities across conversations, issues, logs, and events.[page:28]

Instead of being tied to a single app, AiPi-MemoryCore becomes the **memory substrate** for many different environments: autonomous dev shops, municipal workflows, game backends, and personal infra.[page:28]

---

## 2. Core Responsibilities

AiPi-MemoryCore is responsible for:

- **Ingesting heterogeneous event streams**  
  Conversations, tickets, issues, logs, commits, and telemetry from different systems and tools.[page:28]

- **Normalizing into a canonical memory schema**  
  Everything becomes structured around a small set of universal objects:  
  - `SourceEvent` (raw normalized event)  
  - `Conversation`  
  - `Decision`  
  - `OpenLoop`  
  - `Pod`  
  - `Project`  
  - `EmotionMarker`[page:28]

- **Segmenting and organizing memory**  
  Clustering signals into pods and mapping them to projects and categories using embeddings + HDBSCAN.[page:28]

- **Exposing memory for RAG and agents**  
  Providing retrieval APIs that return not just text, but **contextualized memory items** (decisions, loops, projects) so agents can act, not just answer questions.[page:28]

- **Surfacing development telemetry**  
  Metrics such as open loops, completion ratio, fragmentation index, stale threads, and emotional volatility become first-class signals for self-improving systems.[page:28]

---

## 3. “USB Thumb Drive” Form Factor

### 3.1 Deployment Modes

1. **Standalone Service (recommended)**  
   - Packaged as a Docker image (`aipi/memorycore`).  
   - Run as:  
     ```bash
     docker run -p 8001:8001 aipi/memorycore
     ```  
   - Exposes HTTP APIs for ingest, query, and metrics.

2. **Embedded Library**  
   - Install via `pip` (future):  
     ```bash
     pip install aipi-memorycore
     ```  
   - Import and use `MemoryClient` and ingest/query functions directly inside a Python project.

### 3.2 Integration Contract (High-Level)

Clients interact with three main surfaces:

- **Ingest APIs**  
  - `POST /ingest/raw/{source}` – send raw data for a specific source type (ChatGPT export, GitHub issues, etc.); calls the corresponding adapter.  
  - `POST /ingest/events` – send already-normalized `IngestEvent` objects.

- **RAG / Memory Query APIs**  
  - `POST /query/rag` – semantic search over conversations, decisions, open loops, pods, and projects, with filters and “what to do next” hints.

- **Metrics APIs**  
  - `GET /metrics/*` – summary, open loops, tech stack, projects, emotional volatility (existing dashboard metrics).[page:28]

---

## 4. Architecture Alignment with Current Repo

### 4.1 Existing Structure

Current key components already map well to the pluggable vision:[page:28]

- `conversation_ingest/ingest.py`  
  - Phase 1: event extraction from ChatGPT `conversations.json`.  
  - Extracts decisions, promises, deadlines, emotions, tech signals, loops.

- `memory_core/models.py`  
  - SQLAlchemy ORM models: `Conversation`, `Decision`, `OpenLoop`, `Pod`, `Project`.  
  - SQLite database: `projects.db`.[page:28]

- `run_pipeline.py`  
  - Orchestrates ingestion and processing phases.

- `dashboard/app.py`  
  - Phase 5: FastAPI metrics API, serving dashboard endpoints and docs.[page:28]

- Metrics and rules:  
  - `Open Loops Count`, `Completion Ratio`, `Fragmentation Index`, `Stale Thread Count`, `Emotional Volatility`, and the **90-Day Downgrade Rule**.[page:28]

### 4.2 Proposed New Layers

To become a thumb drive, we add:

1. **Canonical Ingest Model**

   A Pydantic `IngestEvent` model in `memory_core/`:

   - `source` (e.g., `chatgpt`, `github`, `slack`, `municipal`, `game`).  
   - `event_type` (e.g., `conversation`, `issue`, `log`, `commit`).  
   - `timestamp`  
   - `actors` (usernames, agent IDs, roles)  
   - `raw_text` / `payload`  
   - Optional: `project_hint`, `pod_hint`  

   All adapters convert their raw inputs to `IngestEvent` instances, then pipeline them into the DB and segmentation phases.

2. **Adapter Layer (`adapters/`)**

   - Per-source adapters:  
     - `adapters/chatgpt_export.py`  
     - `adapters/github_issues.py`  
     - `adapters/slack.py`  
     - `adapters/municipal_tickets.py`  
     - `adapters/game_logs.py`  

   Each adapter:

   - Takes source-specific configurations/paths.  
   - Emits `IngestEvent` objects.  
   - Reuses the same downstream core: models, segmentation, metrics.

3. **Unified API / Service Layer (`api/`)**

   A FastAPI app (`memory_core.api` or `api/app.py`) that provides:

   - Ingest endpoints (`/ingest/raw/{source}`, `/ingest/events`).  
   - RAG query endpoint (`/query/rag`).  
   - Metrics endpoints (may reuse or wrap `dashboard.app`).[page:28]

---

## 5. “Development-Forward” Memory Behavior

AiPi-MemoryCore is **not** just a document RAG; it is a **development telemetry brain**.

### 5.1 Event Semantics

For each event, the system attempts to extract:

- **Decisions** – committed choices, with optional `executed` flags and timestamps.[page:28]  
- **Open Loops** – promises, TODOs, “we should…” items not yet resolved.[page:28]  
- **Emotional Markers** – frustration, excitement, confusion signals.[page:28]  
- **Tech Stack Changes** – mentions of tools, libraries, infra.[page:28]  
- **Project / Pod Affinity** – what project or pod this event likely touches.[page:28]

### 5.2 Metrics as Action Signals

Existing metrics are explicitly treated as **inputs to other agents**:

- `Open Loops Count` – guides triage agents to close the most critical loops.[page:28]  
- `Completion Ratio` – measures execution vs. planning.  
- `Fragmentation Index` – flags when attention is spread too thin across too many pods.[page:28]  
- `Stale Thread Count` – identifies abandoned conversations.  
- `Emotional Volatility` – tracks stress, confusion, or stuckness over time.[page:28]  
- **90-Day Downgrade Rule** – prevents cognitive hoarding by auto-archiving inactive ideas unless strategic.[page:28]

Agentic systems and dashboards consume these metrics to prioritize work, refactors, and human attention.

### 5.3 RAG for Actions, Not Just Answers

`POST /query/rag` returns entries enriched with:

- Memory type (`decision`, `open_loop`, `conversation`, `pod`, `project`).  
- Links/IDs to related entities (e.g., which loop a message belongs to, which project a pod supports).  
- Suggested next actions (e.g., “This loop references feature X; consider opening an issue or task to complete it.”).

This enables downstream systems (PM agents, dev agents, municipal agents, game AI) to treat MemoryCore as a **“what should we do next?” context engine**, not just a recall engine.

---

## 6. Implementation Roadmap

### Phase A: Canonical Schema & Adapter Setup

1. **Extend `memory_core/models.py`**  
   - Add `SourceEvent` table (if not present) and align ORM models with the canonical schema (including `source` and `event_type`).[page:28]

2. **Define `IngestEvent` model**  
   - Create a shared Pydantic class in `memory_core/` for all adapters.

3. **Refactor `conversation_ingest/ingest.py` into first adapter**  
   - Make ChatGPT ingest output `IngestEvent` objects instead of writing directly to DB.  
   - Pipe `IngestEvent` → models → existing segmentation and metrics.[page:28]

4. **Add `run_pipeline.py` entry mode**

   Example CLI:

   ```bash
   python run_pipeline.py --source chatgpt --path path/to/conversations.json
   python run_pipeline.py --source gh_issues --repo gduemer/AiPi-MemoryCore
   ```

### Phase B: API & Packaging

1. **API Layer**

   - Implement FastAPI endpoints on top of `memory_core`:

     - `POST /ingest/events`  
     - `POST /ingest/raw/{source}`  
     - `POST /query/rag`  
     - Proxy or wrap existing `/metrics/*` endpoints.[page:28]

2. **Docker Packaging**

   - Add a `Dockerfile` to run the API:

     ```bash
     uvicorn memory_core.api:app --host 0.0.0.0 --port 8001
     ```

   - Publish an image to a registry (e.g., `aipi/memorycore`).

3. **Python Packaging**

   - Add `pyproject.toml` and package metadata.  
   - Provide a small `MemoryClient` class for Python projects to ingest/query programmatically.

### Phase C: Multi-Source Ingest & Example Integrations

1. **Second Adapter**

   - Implement at least one non-ChatGPT adapter (e.g., GitHub issues/PRs) to validate the adapter pattern.

2. **Example Integrations**

   - Add examples under `examples/` that show how to plug MemoryCore into:  
     - AiPi Core.  
     - An autonomous dev shop pipeline.  
     - A game AI or municipal-style workflow.

---

## 7. Usage as a Pluggable Module

### 7.1 Standalone Service Usage

1. Run the container:

   ```bash
   docker run -p 8001:8001 aipi/memorycore
   ```

2. Ingest data:

   ```bash
   curl -X POST http://localhost:8001/ingest/raw/chatgpt \
        -F "file=@conversations.json"
   ```

3. Query memory:

   ```bash
   curl -X POST http://localhost:8001/query/rag \
        -H "Content-Type: application/json" \
        -d '{
          "query": "What promises did I make about AiPi-MemoryCore CI?",
          "filters": { "types": ["decision","open_loop"] }
        }'
   ```

4. Pull metrics:

   ```bash
   curl http://localhost:8001/metrics/summary
   ```

### 7.2 Embedded Library Usage (Future)

```python
from aipi_memorycore import MemoryClient

client = MemoryClient(base_url="http://localhost:8001")

client.ingest_events([...])  # list of IngestEvent dicts
results = client.query_rag(
    query="Where am I stuck on infra work?",
    filters={"types": ["open_loop"]}
)
```

---

## 8. Relationship to AiPi

AiPi-MemoryCore remains **the memory substrate for AiPi**, but with a stronger separation of concerns:[page:28]

- AiPi Core: orchestrator, agents, tools, and higher-level policies.  
- AiPi-MemoryCore: universal memory store and telemetry brain across projects, domains, and tools.

AiPi Core “plugs in” to this thumb drive to gain:

- Durable cross-session context.  
- Structured progress and risk signals.  
- Actionable RAG over all its conversations, decisions, and work artifacts.[page:28]
```

If you want, I can next draft a companion `run_pipeline.py` comment block or `api/app.py` skeleton that matches this proposal so you can wire it up quickly.
