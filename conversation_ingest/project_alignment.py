"""conversation_ingest/project_alignment.py
Phase 4: Project Alignment - map pods to existing or new projects
Creates Project records and associates Pods with them.
"""
import json
import sys
import os
import uuid
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory_core.models import (
    Pod,
    Project,
    get_engine,
    get_session,
    init_db,
)

EMBED_DIR = Path("conversation_ingest/embeddings")
LABELED_FILE = EMBED_DIR / "pods_labeled.json"

# Known projects mapping
PROJECT_MAPPING = {
    "AiPi Project": {"name": "AiPi", "is_strategic": True},
    "SWIS Project": {"name": "SWIS", "is_strategic": True},
    "FOST Project": {"name": "FOST", "is_strategic": False},
    "OpenClaw Project": {"name": "OpenClaw", "is_strategic": False},
    "HumanCore Project": {"name": "HumanCore", "is_strategic": False},
    "Game Development": {"name": "UGLI-GameAI", "is_strategic": False},
}


def ensure_project(session, category: str, is_strategic: bool = False) -> Project:
    """Get or create a project for the given category."""
    # Check if we have a known mapping
    if category in PROJECT_MAPPING:
        project_name = PROJECT_MAPPING[category]["name"]
        is_strategic = PROJECT_MAPPING[category]["is_strategic"]
    else:
        project_name = category

    # Try to find existing project
    project = session.query(Project).filter_by(name=project_name).first()
    if project:
        return project

    # Create new project
    project = Project(
        id=str(uuid.uuid4()),
        name=project_name,
        category=category,
        status="active",
        is_strategic=is_strategic,
        last_active=datetime.utcnow(),
    )
    session.add(project)
    session.commit()
    print(f"[align] Created project: {project_name} (strategic={is_strategic})")
    return project


def align_pods_to_projects():
    """Load labeled pods, create projects, and associate pods with projects."""
    if not LABELED_FILE.exists():
        print("[align] No pods_labeled.json found. Run category_synthesis.py first.")
        return

    with open(LABELED_FILE, "r", encoding="utf-8") as fp:
        pods_data = json.load(fp)

    print(f"[align] Loaded {len(pods_data)} labeled pods")

    # Initialize database
    engine = init_db()
    session = get_session(engine)

    try:
        pods_created = 0
        projects_created = set()

        for pod_data in pods_data:
            category = pod_data.get("category", "Uncategorized")

            # Ensure project exists
            project = ensure_project(session, category)
            projects_created.add(project.name)

            # Check if pod already exists
            existing_pod = session.query(Pod).filter_by(id=pod_data["pod_id"]).first()
            if existing_pod:
                # Update existing pod
                existing_pod.label = category
                existing_pod.project_id = project.id
                existing_pod.core_technologies = pod_data.get(
                    "core_technologies", []
                )
                existing_pod.emotional_driver = pod_data.get("emotional_driver")
            else:
                # Create new pod
                pod = Pod(
                    id=pod_data["pod_id"],
                    label=category,
                    core_technologies=pod_data.get("core_technologies", []),
                    emotional_driver=pod_data.get("emotional_driver"),
                    project_id=project.id,
                )
                session.add(pod)
                pods_created += 1

        session.commit()
        print(f"[align] Created/updated {pods_created} pods")
        print(f"[align] Projects involved: {', '.join(sorted(projects_created))}")

        # Print summary
        total_projects = session.query(Project).count()
        total_pods = session.query(Pod).count()
        print(f"[align] Database now has {total_projects} projects and {total_pods} pods")

    finally:
        session.close()


if __name__ == "__main__":
    align_pods_to_projects()
