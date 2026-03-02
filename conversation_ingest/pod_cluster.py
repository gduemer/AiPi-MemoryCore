"""
conversation_ingest/pod_cluster.py
Phase 2: Pod Segmentation via sentence-transformers + HDBSCAN
"""

import json
import uuid
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import hdbscan

EXTRACTED_DIR = Path("conversation_ingest/extracted_json")
EMBED_DIR = Path("conversation_ingest/embeddings")
EMBED_DIR.mkdir(parents=True, exist_ok=True)
MODEL_NAME = "all-MiniLM-L6-v2"


def load_all_extracted() -> list[dict]:
    records = []
    for f in EXTRACTED_DIR.glob("*_extracted.json"):
        with open(f, "r", encoding="utf-8") as fp:
            records.extend(json.load(fp))
    print(f"[cluster] Loaded {len(records)} conversations")
    return records


def build_text_for_embedding(record: dict) -> str:
    parts = (
        record.get("projects_named", [])
        + record.get("tech_stack", [])
        + record.get("emotional_markers", [])
        + record.get("decisions", [])[:5]
        + record.get("open_loops", [])[:5]
    )
    return " ".join(parts) or "unknown"


def generate_embeddings(records: list[dict]) -> np.ndarray:
    model = SentenceTransformer(MODEL_NAME)
    texts = [build_text_for_embedding(r) for r in records]
    print(f"[cluster] Embedding {len(texts)} conversations...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    np.save(EMBED_DIR / "embeddings.npy", embeddings)
    print("[cluster] Embeddings saved.")
    return embeddings


def cluster_embeddings(embeddings: np.ndarray, records: list[dict]) -> list[dict]:
    clusterer = hdbscan.HDBSCAN(min_cluster_size=3, min_samples=2, metric="euclidean")
    labels = clusterer.fit_predict(embeddings)
    n_pods = len(set(labels) - {-1})
    print(f"[cluster] {n_pods} pods | {list(labels).count(-1)} noise points")

    pods: dict[int, dict] = {}
    for label, record in zip(labels, records):
        if label == -1:
            continue
        if label not in pods:
            pods[label] = {
                "pod_id": str(uuid.uuid4()),
                "cids": [],
                "tech": set(),
                "projects": set(),
                "emotions": set(),
            }
        pods[label]["cids"].append(record["conversation_id"])
        pods[label]["tech"].update(record.get("tech_stack", []))
        pods[label]["projects"].update(record.get("projects_named", []))
        pods[label]["emotions"].update(record.get("emotional_markers", []))

    result = [
        {
            "pod_id": p["pod_id"],
            "conversation_ids": p["cids"],
            "core_technologies": list(p["tech"]),
            "projects": list(p["projects"]),
            "emotional_driver": ", ".join(list(p["emotions"])[:3]),
            "size": len(p["cids"]),
        }
        for p in pods.values()
    ]

    with open(EMBED_DIR / "pods.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"[cluster] pods.json written ({len(result)} pods)")
    return result


def run_clustering():
    records = load_all_extracted()
    if not records:
        print("[cluster] No extracted data. Run ingest.py first.")
        return
    embeddings = generate_embeddings(records)
    pods = cluster_embeddings(embeddings, records)
    print(f"[cluster] Done. {len(pods)} pods ready for Phase 3 labelling.")
    return pods


if __name__ == "__main__":
    run_clustering()
