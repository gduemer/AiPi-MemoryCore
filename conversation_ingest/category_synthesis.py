"""conversation_ingest/category_synthesis.py
Phase 3: Category Synthesis via clustering + simple rule-based labeling
Names each pod cluster with a category label (cap at 12 categories max).
"""
import json
from pathlib import Path
from collections import Counter

EMBED_DIR = Path("conversation_ingest/embeddings")
PODS_FILE = EMBED_DIR / "pods.json"
LABELED_FILE = EMBED_DIR / "pods_labeled.json"

# Predefined category mapping (max 12 categories)
CATEGORY_RULES = {
    "AI & ML Development": ["ollama", "embedding", "hdbscan", "llamacpp", "lm studio"],
    "Backend Development": ["fastapi", "sqlalchemy", "postgres", "sqlite", ".net", "c#"],
    "Frontend Development": ["chart.js", "d3", "echarts"],
    "DevOps & Infrastructure": ["docker", "github actions", "wsl"],
    "Data & Analytics": ["sqlite", "postgres", "sqlalchemy"],
    "Game Development": ["ugli"],
    "Automation & CI/CD": ["github", "github actions", "powershell"],
    "AiPi Project": ["aipi"],
    "SWIS Project": ["swis"],
    "FOST Project": ["fost"],
    "HumanCore Project": ["humancore"],
    "OpenClaw Project": ["openclaw"],
}


def assign_category(pod: dict) -> str:
    """Assign category based on tech stack and projects."""
    tech = [t.lower() for t in pod.get("core_technologies", [])]
    projects = [p.lower() for p in pod.get("projects", [])]
    combined = tech + projects

    scores = Counter()
    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword in combined:
                scores[category] += 1

    if scores:
        return scores.most_common(1)[0][0]
    else:
        # Default to a generic category
        if "fastapi" in tech or "sqlalchemy" in tech:
            return "Backend Development"
        elif tech:
            return "General Development"
        else:
            return "Uncategorized"


def synthesize_categories():
    """Load pods.json, assign categories, save pods_labeled.json."""
    if not PODS_FILE.exists():
        print("[category] No pods.json found. Run pod_cluster.py first.")
        return

    with open(PODS_FILE, "r", encoding="utf-8") as fp:
        pods = json.load(fp)

    print(f"[category] Loaded {len(pods)} pods from {PODS_FILE}")

    for pod in pods:
        pod["category"] = assign_category(pod)

    # Count categories (cap at 12)
    category_counts = Counter(p["category"] for p in pods)
    print(f"[category] Category distribution:")
    for cat, count in category_counts.most_common(12):
        print(f"  {cat}: {count} pods")

    with open(LABELED_FILE, "w", encoding="utf-8") as fp:
        json.dump(pods, fp, indent=2)

    print(f"[category] Saved {len(pods)} labeled pods to {LABELED_FILE}")
    return pods


if __name__ == "__main__":
    synthesize_categories()
