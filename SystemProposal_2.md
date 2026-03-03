Here’s a revised `SystemProposal_2.md` with the missing API/CLI/interface details, aimed at “good clean efficient effective” implementation.

```markdown
# SystemProposal_2: AiPi-MemoryCore as a Pluggable Memory “Thumb Drive”

## 1. Vision

AiPi-MemoryCore becomes a **pluggable, project-agnostic memory service** that behaves like a USB thumb drive: you plug it into any system (dev shop, municipal stack, game backend, personal infra) to get structured memory and RAG over conversations, issues, logs, and events.[page:29]

The core ideas:

- One **canonical memory schema** (decisions, loops, pods, projects, etc.).[page:29]
- A small, stable **API + CLI contract** for ingest, query, and metrics.
- A simple **adapter interface** so any data source can be normalized into the same memory substrate.

---

## 2. Core Responsibilities

AiPi-MemoryCore is responsible for:

- **Ingesting heterogeneous event streams**  
  - Conversations, tickets, issues, logs, commits, telemetry, etc.[page:29]

- **Normalizing into a canonical memory schema**  
  - `SourceEvent` (raw normalized event)  
  - `Conversation`  
  - `Decision`  
  - `OpenLoop`  
  - `Pod`  
  - `Project`  
  - `EmotionMarker`[page:29]

- **Segmenting and organizing memory**  
  - Clustering into pods and mapping to projects using embeddings + HDBSCAN (as in existing phases).[page:29]

- **Exposing memory for RAG and agents**  
  - Semantic query over the memory graph with filters and “next action” hints.

- **Surfacing development telemetry**  
  - Metrics: open loops, completion ratio, fragmentation index, stale threads, emotional volatility, 90-day downgrade rule.[page:29]

---

## 3. Deployment Form Factors

### 3.1 Standalone Service

Primary mode: Dockerized HTTP service.

- Run:

  ```bash
  docker run -p 8001:8001 aipi/memorycore
  ```

- Provides:
  - `/ingest` endpoints to push data.
  - `/query` endpoint for RAG queries.
  - `/metrics` endpoints for telemetry.

### 3.2 Embedded Library

Secondary mode: import as a Python package.

- Install (future):

  ```bash
  pip install aipi-memorycore
  ```

- Usage:

  ```python
  from aipi_memorycore import MemoryClient

  client = MemoryClient(base_url="http://localhost:8001")
  client.ingest_events([...])
  results = client.query_rag(query="Where am I stuck?", filters={"types": ["open_loop"]})
  ```

---

## 4. Canonical Ingest Model

### 4.1 `IngestEvent` (Pydantic)

All adapters must output the same structure:

```python
# memory_core/schemas.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class IngestEvent(BaseModel):
    source: str                # "chatgpt", "github", "slack", "municipal", "game", ...
    event_type: str            # "conversation", "message", "issue", "log", "commit", ...
    timestamp: datetime
    actors: List[str] = []     # usernames, agent IDs
    raw_text: str              # main text content
    payload: Dict[str, Any] = {}   # source-specific extra data

    project_hint: Optional[str] = None
    pod_hint: Optional[str] = None
```

### 4.2 DB Alignment

Extend or confirm `memory_core/models.py`:

- Add `SourceEvent` table if not present:

  - `id`, `source`, `event_type`, `timestamp`, `actors`, `raw_text`, `payload_json`, `project_hint`, `pod_hint`.[page:29]

- Keep existing higher-level entities:

  - `Conversation`, `Decision`, `OpenLoop`, `Pod`, `Project`, `EmotionMarker`.[page:29]

`IngestEvent` → `SourceEvent` → extraction/segmentation → `Decision`, `OpenLoop`, `Pod`, `Project`, etc.

---

## 5. Adapter Interface

### 5.1 Adapter Contract

Each adapter is a module under `adapters/` that implements:

```python
# adapters/base.py

from typing import Iterable
from memory_core.schemas import IngestEvent

class BaseAdapter:
    source_name: str

    def load(self, **kwargs) -> Iterable[IngestEvent]:
        """Yield IngestEvent objects from the underlying data."""
        raise NotImplementedError
```

Example: ChatGPT adapter refactor:

```python
# adapters/chatgpt_export.py

from typing import Iterable
from pathlib import Path
import json
from datetime import datetime
from memory_core.schemas import IngestEvent
from .base import BaseAdapter

class ChatGPTExportAdapter(BaseAdapter):
    source_name = "chatgpt"

    def __init__(self, path: str):
        self.path = Path(path)

    def load(self, **kwargs) -> Iterable[IngestEvent]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        # TODO: Align with existing conversation_ingest logic
        for conv in data["conversations"]:
            for msg in conv["mapping"].values():
                if not msg.get("message"):
                    continue
                content = msg["message"]["content"]["parts"]
                yield IngestEvent(
                    source=self.source_name,
                    event_type="message",
                    timestamp=datetime.fromtimestamp(msg["create_time"]),
                    actors=[msg["message"]["author"]["role"]],
                    raw_text=content,
                    payload={"conversation_id": conv["id"]}
                )
```

Adapters can reuse or call into existing `conversation_ingest` logic as needed.[page:29]

---

## 6. CLI Contract (`run_pipeline.py`)

`run_pipeline.py` orchestrates: adapter → DB → segmentation → metrics.

### 6.1 Expected CLI

```bash
# ChatGPT export
python run_pipeline.py --source chatgpt --path data/conversations.json

# GitHub issues (future)
python run_pipeline.py --source github --repo gduemer/AiPi-MemoryCore

# Other sources
python run_pipeline.py --source slack --workspace my-ws --channel ai-pi
```

### 6.2 High-Level Flow

Pseudo-code:

```python
# run_pipeline.py

import argparse
from adapters.chatgpt_export import ChatGPTExportAdapter
# from adapters.github_issues import GitHubIssuesAdapter, etc.
from memory_core.pipeline import process_events

ADAPTERS = {
    "chatgpt": ChatGPTExportAdapter,
    # "github": GitHubIssuesAdapter,
    # ...
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--path")
    parser.add_argument("--repo")
    args = parser.parse_args()

    adapter_cls = ADAPTERS[args.source]
    adapter = adapter_cls(**vars(args))  # simple kwargs pass-through

    events = adapter.load()
    process_events(events)  # writes to DB, runs extraction + segmentation + metrics

if __name__ == "__main__":
    main()
```

`process_events` lives in `memory_core/pipeline.py` and coordinates DB writes and existing extraction/segmentation phases.[page:29]

---

## 7. HTTP API Contract

Implement as FastAPI app, e.g. `api/app.py` (or extend existing `dashboard/app.py`).[page:29]

### 7.1 Endpoints Overview

| Endpoint               | Method | Purpose                             |
|------------------------|--------|-------------------------------------|
| `/ingest/events`       | POST   | Push normalized `IngestEvent` list  |
| `/ingest/raw/{source}` | POST   | Push raw data for a named adapter   |
| `/query/rag`           | POST   | Semantic query over memory          |
| `/metrics/summary`     | GET    | High-level metrics summary          |
| `/metrics/open_loops`  | GET    | Open loop metrics/detail            |
| `/metrics/projects`    | GET    | Project-level metrics               |

### 7.2 Example Schemas

```python
# api/schemas.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from memory_core.schemas import IngestEvent

class RAGQuery(BaseModel):
    query: str
    filters: Dict[str, Any] = {}   # e.g., {"types": ["decision","open_loop"], "project_id": "..."}
    k: int = 10

class RAGItem(BaseModel):
    id: str
    item_type: str      # "decision", "open_loop", "conversation", "pod", "project"
    score: float
    snippet: str
    project_id: Optional[str]
    pod_id: Optional[str]
    suggested_action: Optional[str] = None

class RAGResponse(BaseModel):
    items: List[RAGItem]
```

### 7.3 Example FastAPI Skeleton

```python
# api/app.py

from fastapi import FastAPI, UploadFile, File
from typing import List
from memory_core.schemas import IngestEvent
from .schemas import RAGQuery, RAGResponse
from memory_core import pipeline, rag, metrics

app = FastAPI(title="AiPi-MemoryCore API")

@app.post("/ingest/events")
async def ingest_events(events: List[IngestEvent]):
    pipeline.process_events(events)
    return {"status": "ok", "count": len(events)}

@app.post("/ingest/raw/{source}")
async def ingest_raw(source: str, file: UploadFile = File(...)):
    content = await file.read()
    events = pipeline.load_from_raw(source=source, raw_bytes=content)
    pipeline.process_events(events)
    return {"status": "ok", "count": len(events)}

@app.post("/query/rag", response_model=RAGResponse)
async def query_rag(body: RAGQuery):
    items = rag.query(body.query, body.filters, body.k)
    return RAGResponse(items=items)

@app.get("/metrics/summary")
async def metrics_summary():
    return metrics.get_summary()

# ... other /metrics endpoints reusing existing metrics logic
```

`rag.query` uses embeddings + DB to retrieve and score items (conversations, decisions, open loops, pods, projects).[page:29]

---

## 8. RAG Behavior: Action-Oriented Memory

### 8.1 Query Semantics

`POST /query/rag`:

- Input:

  ```json
  {
    "query": "What promises did I make about AiPi-MemoryCore CI?",
    "filters": { "types": ["decision","open_loop"] },
    "k": 10
  }
  ```

- Output: top-K items across decisions, open loops, conversations, pods, projects, each with:

  - `snippet`
  - `item_type`
  - `project_id` / `pod_id`
  - `suggested_action` (e.g., “Open a CI issue to implement X”).  

### 8.2 Suggested Actions

`suggested_action` is generated using simple rules or a small model:

- If item is an open loop with no linked issue → suggest creating a task/issue.
- If item is a decision without an “executed” flag → suggest verifying completion and updating status.
- If item is a pod with high fragmentation and low completion → suggest consolidation or pruning.

This makes MemoryCore useful to autonomous agents and dashboards as a **“what should we do next?” engine**, not just a recall layer.

---

## 9. Metrics as First-Class Integration Points

Metrics already defined in the repository are treated as public surfaces for other systems:[page:29]

- `Open Loops Count`  
- `Completion Ratio`  
- `Fragmentation Index`  
- `Stale Thread Count`  
- `Emotional Volatility`  
- `90-Day Downgrade Rule`[page:29]

Agents and orchestrators can:

- Poll `/metrics/summary` to prioritize automation work.  
- Use metrics thresholds to trigger alerts or workflows (e.g., high emotional volatility → suggest focus/refactor time).

---

## 10. Relationship to AiPi and Other Systems

AiPi-MemoryCore is positioned as:

- **The memory substrate for AiPi**  
  - AiPi core orchestrator uses MemoryCore for durable context, RAG, and progress signals.[page:29]

- **A reusable module for other environments**  
  - Autonomous dev shop: plug into CI/CD and planning.  
  - Municipal workflows: ingest tickets, approvals, decisions.  
  - Game AI: ingest player events, balancing notes, design discussions.

Any system that can talk HTTP or Python can “mount” this memory thumb drive and benefit from the same schema, metrics, and RAG behavior.

---
```
