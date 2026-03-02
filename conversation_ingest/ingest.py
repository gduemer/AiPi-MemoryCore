"""
Phase 1: Conversation Ingest
Parses exported ChatGPT/Claude/Perplexity conversation JSON.
Extracts: decisions, promises, deadlines, projects, emotions, tech, open loops.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Any

OUT_DIR = Path("conversation_ingest/extracted_json")
OUT_DIR.mkdir(parents=True, exist_ok=True)

DECISION_MARKERS  = ["i will", "we decided", "going with", "decided to"]
PROMISE_MARKERS   = ["i promise", "i'll make sure", "will have it done", "will deliver"]
DEADLINE_MARKERS  = ["by friday", "by monday", "end of week", "tomorrow", "next week", "deadline"]
EMOTION_MARKERS   = ["fear", "excited", "frustrated", "stuck", "overwhelmed", "anxious", "proud", "worried"]
LOOP_MARKERS      = ["need to", "haven't yet", "still need", "todo", "not done", "pending", "unfinished"]
TECH_KEYWORDS     = [
    "fastapi", "sqlite", "postgres", "docker", "python", "c#", ".net",
    "chart.js", "d3", "echarts", "llamacpp", "ollama", "lm studio",
    "embedding", "hdbscan", "sqlalchemy", "swis", "ugli", "aipi",
    "github", "github actions", "powershell", "wsl", "vscode"
]
KNOWN_PROJECTS = ["swis", "ugli", "fost", "aipi", "humancore", "openclaw"]


def extract_signal(text: str, conversation_id: str, timestamp: str) -> dict[str, Any]:
    lower = text.lower()
    lines = text.split("\n")
    return {
        "conversation_id":  conversation_id,
        "timestamp":        timestamp,
        "decisions":             [line.strip() for line in lines if any(m in line.lower() for m in DECISION_MARKERS)][:20],        "promises":         [l.strip() for l in lines if any(m in l.lower() for m in PROMISE_MARKERS)][:20],
        "promises":             [line.strip() for line in lines if any(m in line.lower() for m in PROMISE_MARKERS)][:20],        "projects_named":   list({p.upper() for p in KNOWN_PROJECTS if p in lower}),
                "deadlines":            [line.strip() for line in lines if any(m in line.lower() for m in DEADLINE_MARKERS)][:10],
        "projects_named":        list({p.upper() for p in KNOWN_PROJECTS if p in lower}),
        "emotional_markers": [m for m in EMOTION_MARKERS if m in lower],
        "tech_stack":       list({t for t in TECH_KEYWORDS if t in lower}),
        "open_loops":           [line.strip() for line in lines if any(m in line.lower() for m in LOOP_MARKERS)][:30],        "raw_char_count":   len(text),
    }


def ingest_chatgpt_export(export_path: Path) -> list[dict]:
    with open(export_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = []
    for convo in data:
        cid = convo.get("id", str(uuid.uuid4()))
        ts  = convo.get("create_time", "")
        if ts:
            ts = datetime.utcfromtimestamp(float(ts)).isoformat()
        messages   = convo.get("mapping", {})
        text_parts = []
        for _, msg_data in messages.items():
            msg = msg_data.get("message")
            if msg and msg.get("content"):
                for part in msg["content"].get("parts", []):
                    if isinstance(part, str):
                        text_parts.append(part)
        full_text = "\n".join(text_parts)
        results.append(extract_signal(full_text, cid, ts))
    return results


def run_ingest(export_path: str):
    path     = Path(export_path)
    results  = ingest_chatgpt_export(path)
    out_file = OUT_DIR / f"{path.stem}_extracted.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[ingest] {len(results)} conversations extracted -> {out_file}")
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <conversations.json>")
        sys.exit(1)
    run_ingest(sys.argv[1])
