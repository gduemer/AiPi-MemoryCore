#!/usr/bin/env python3
"""run_pipeline.py
Orchestrates all 5 phases of AiPi-MemoryCore:
  Phase 1: Event Extraction (ingest.py)
  Phase 2: Pod Segmentation (pod_cluster.py)
  Phase 3: Category Synthesis (category_synthesis.py)
  Phase 4: Project Alignment (project_alignment.py)
  Phase 5: Dashboard (dashboard/app.py)

Usage:
  python run_pipeline.py <path/to/conversations.json>
"""
import sys
import subprocess
from pathlib import Path


def run_phase(phase_name: str, script_path: str, *args):
    """Execute a single phase script."""
    print(f"\n{'='*60}")
    print(f"  PHASE: {phase_name}")
    print(f"{'='*60}")
    
    cmd = [sys.executable, script_path, *args]
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"\n❌ {phase_name} failed with exit code {result.returncode}")
        sys.exit(1)
    else:
        print(f"\n✅ {phase_name} completed successfully")


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_pipeline.py <path/to/conversations.json>")
        print("\nThis script runs all 5 phases:")
        print("  1. Event Extraction")
        print("  2. Pod Segmentation")
        print("  3. Category Synthesis")
        print("  4. Project Alignment")
        print("  5. Dashboard (started separately)")
        sys.exit(1)

    conversations_file = sys.argv[1]
    if not Path(conversations_file).exists():
        print(f"❌ File not found: {conversations_file}")
        sys.exit(1)

    print("\n" + "="*60)
    print("  AiPi-MemoryCore Full Pipeline")
    print("="*60)
    print(f"Input: {conversations_file}\n")

    # Phase 1: Event Extraction
    run_phase(
        "Phase 1: Event Extraction",
        "conversation_ingest/ingest.py",
        conversations_file
    )

    # Phase 2: Pod Segmentation  
    run_phase(
        "Phase 2: Pod Segmentation",
        "conversation_ingest/pod_cluster.py"
    )

    # Phase 3: Category Synthesis
    run_phase(
        "Phase 3: Category Synthesis",
        "conversation_ingest/category_synthesis.py"
    )

    # Phase 4: Project Alignment
    run_phase(
        "Phase 4: Project Alignment",
        "conversation_ingest/project_alignment.py"
    )

    # Phase 5 info
    print(f"\n{'='*60}")
    print("  PHASE 5: Dashboard")
    print(f"{'='*60}")
    print("\nTo launch the dashboard, run:")
    print("  python launch_dashboard.py")
    print("  OR")
    print("  uvicorn dashboard.app:app --reload --port 8000")
    print("\nThen open: http://localhost:8000")
    print("\n✅ Pipeline complete! All data ingested and ready.\n")


if __name__ == "__main__":
    main()
