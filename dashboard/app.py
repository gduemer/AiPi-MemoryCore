"""
dashboard/app.py - Phase 5: FastAPI Dashboard for AiPi-MemoryCore
Metrics API for Chart.js / ECharts / D3 frontend.
"""
import sys
import os
import subprocess
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, UploadFile, File, HTMLResponse
from sqlalchemy import func
from memory_core.models import (
    Conversation,
    Decision,
    OpenLoop,
    Pod,
    Project,
    get_engine,
    get_session,
)

app = FastAPI(title="AiPi-MemoryCore Dashboard", version="0.1.0")
engine = get_engine()

# HTML Template with Modal Interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AiPi-MemoryCore Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0d1117; color: #c9d1d9; }
        .header { background: #161b22; padding: 20px; border-bottom: 1px solid #30363d; }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .header p { color: #8b949e; font-size: 14px; }
        .upload-btn { background: #238636; color: white; border: none; padding: 10px 20px; border-radius: 6px; 
                     cursor: pointer; font-size: 14px; font-weight: 500; margin: 20px; }
        .upload-btn:hover { background: #2ea043; }
        
        /* Modal Styles */
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; 
                overflow: auto; background-color: rgba(0,0,0,0.7); }
        .modal-content { background-color: #161b22; margin: 10% auto; padding: 0; border: 1px solid #30363d; 
                        border-radius: 6px; width: 500px; max-width: 90%; }
        .modal-header { padding: 20px; border-bottom: 1px solid #30363d; }
        .modal-header h2 { font-size: 18px; }
        .modal-body { padding: 20px; }
        .modal-footer { padding: 20px; border-top: 1px solid #30363d; text-align: right; }
        .close { color: #8b949e; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        .close:hover { color: #c9d1d9; }
        
        .file-drop-zone { border: 2px dashed #30363d; border-radius: 6px; padding: 40px; text-align: center; 
                         margin: 20px 0; cursor: pointer; transition: all 0.3s; }
        .file-drop-zone:hover { border-color: #58a6ff; background: #0d1117; }
        .file-drop-zone.dragover { border-color: #58a6ff; background: #0d1117; }
        .file-input { display: none; }
        
        .btn { padding: 10px 20px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; font-weight: 500; }
        .btn-primary { background: #238636; color: white; }
        .btn-primary:hover { background: #2ea043; }
        .btn-secondary { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; }
        .btn-secondary:hover { background: #30363d; }
        
        .status { margin-top: 15px; padding: 10px; border-radius: 6px; display: none; }
        .status.success { background: #238636; }
        .status.error { background: #da3633; }
        
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; padding: 20px; }
        .metric-card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 20px; }
        .metric-card h3 { font-size: 14px; color: #8b949e; margin-bottom: 10px; }
        .metric-card .value { font-size: 32px; font-weight: bold; color: #58a6ff; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 AiPi-MemoryCore Dashboard</h1>
        <p>Conversation ingestion, pod segmentation, and memory analytics</p>
    </div>
    
    <button class="upload-btn" onclick="openModal()">📤 Upload Conversation</button>
    
    <div class="metrics" id="metricsContainer">
        <div class="metric-card">
            <h3>Total Conversations</h3>
            <div class="value" id="totalConvos">-</div>
        </div>
        <div class="metric-card">
            <h3>Open Loops</h3>
            <div class="value" id="openLoops">-</div>
        </div>
        <div class="metric-card">
            <h3>Completion Ratio</h3>
            <div class="value" id="completion">-</div>
        </div>
        <div class="metric-card">
            <h3>Total Pods</h3>
            <div class="value" id="pods">-</div>
        </div>
    </div>
    
    <!-- Modal -->
    <div id="uploadModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <span class="close" onclick="closeModal()">&times;</span>
                <h2>Upload Conversation File</h2>
            </div>
            <div class="modal-body">
                <div class="file-drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
                    <p>📁 Click to browse or drag & drop</p>
                    <p style="color: #8b949e; font-size: 12px; margin-top: 10px;">Accepts JSON conversation files</p>
                </div>
                <input type="file" id="fileInput" class="file-input" accept=".json" onchange="handleFileSelect(event)">
                <div id="fileName" style="margin-top: 10px; color: #8b949e;"></div>
                <div id="status" class="status"></div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn btn-primary" id="uploadBtn" onclick="uploadFile()" disabled>Upload</button>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFile = null;
        
        // Modal functions
        function openModal() {
            document.getElementById('uploadModal').style.display = 'block';
        }
        
        function closeModal() {
            document.getElementById('uploadModal').style.display = 'none';
            selectedFile = null;
            document.getElementById('fileName').textContent = '';
            document.getElementById('uploadBtn').disabled = true;
            document.getElementById('status').style.display = 'none';
        }
        
        // File handling
        function handleFileSelect(event) {
            selectedFile = event.target.files[0];
            if (selectedFile) {
                document.getElementById('fileName').textContent = `Selected: ${selectedFile.name}`;
                document.getElementById('uploadBtn').disabled = false;
            }
        }
        
        // Drag & drop
        const dropZone = document.getElementById('dropZone');
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            selectedFile = e.dataTransfer.files[0];
            if (selectedFile) {
                document.getElementById('fileName').textContent = `Selected: ${selectedFile.name}`;
                document.getElementById('uploadBtn').disabled = false;
            }
        });
        
        // Upload file
        async function uploadFile() {
            if (!selectedFile) return;
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            const uploadBtn = document.getElementById('uploadBtn');
            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Uploading...';
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                const status = document.getElementById('status');
                status.style.display = 'block';
                
                if (result.status === 'success') {
                    status.className = 'status success';
                    status.textContent = '✓ ' + result.message;
                    setTimeout(() => {
                        closeModal();
                        loadMetrics();
                    }, 2000);
                } else {
                    status.className = 'status error';
                    status.textContent = '✗ ' + result.message;
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Upload';
                }
            } catch (error) {
                const status = document.getElementById('status');
                status.style.display = 'block';
                status.className = 'status error';
                status.textContent = '✗ Upload failed: ' + error.message;
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload';
            }
        }
        
        // Load metrics
        async function loadMetrics() {
            try {
                const response = await fetch('/metrics/summary');
                const data = await response.json();
                document.getElementById('totalConvos').textContent = data.total_conversations;
                document.getElementById('openLoops').textContent = data.open_loops_count;
                document.getElementById('completion').textContent = (data.completion_ratio * 100).toFixed(1) + '%';
                document.getElementById('pods').textContent = data.pod_count;
            } catch (error) {
                console.error('Failed to load metrics:', error);
            }
        }
        
        // Load metrics on page load
        loadMetrics();
        setInterval(loadMetrics, 30000); // Refresh every 30 seconds
    </script>
</body>
</html>
"""


@app.get("/")
async def root():
    return HTMLResponse(content=HTML_TEMPLATE)


@app.post("/upload")
async def upload_conversation(file: UploadFile = File(...)):
    """Upload and ingest conversation JSON file."""
    import tempfile

    try:
        # Read file content
        content = await file.read()
        data = json.loads(content)

        # Save to a secure temp file (avoids path traversal from client filename)
        fd, temp_path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data, f)

            # Run ingestion with the same interpreter/venv as this app
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ingest_script = os.path.join(
                project_root, "conversation_ingest", "ingest.py"
            )
            result = subprocess.run(
                [sys.executable, ingest_script, temp_path],
                capture_output=True,
                text=True,
            )
        finally:
            # Always remove the temp file even if ingestion raises
            if os.path.exists(temp_path):
                os.remove(temp_path)

        if result.returncode == 0:
            return {"status": "success", "message": f"Ingested {file.filename}"}
        else:
            return {"status": "error", "message": result.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/metrics/summary")
async def metrics_summary():
    """Gauge data: open loops, decisions, fragmentation index, completion ratio."""
    s = get_session(engine)
    try:
        total_convos = s.query(func.count(Conversation.id)).scalar() or 0
        open_loops = (
            s.query(func.count(OpenLoop.id)).filter(~OpenLoop.is_closed).scalar() or 0
        )
        total_decisions = s.query(func.count(Decision.id)).scalar() or 0
        exec_decisions = (
            s.query(func.count(Decision.id)).filter(Decision.is_executed).scalar() or 0
        )
        active_projects = (
            s.query(func.count(Project.id)).filter(Project.status == "active").scalar()
            or 0
        )
        stale_count = (
            s.query(func.count(Conversation.id)).filter(Conversation.is_stale).scalar()
            or 0
        )
        pod_count = s.query(func.count(Pod.id)).scalar() or 0
        completion = (
            round(exec_decisions / total_decisions, 3) if total_decisions else 0.0
        )
        fragmentation = (
            round(pod_count / active_projects, 2)
            if active_projects
            else float(pod_count)
        )
        return {
            "total_conversations": total_convos,
            "open_loops_count": open_loops,
            "total_decisions": total_decisions,
            "executed_decisions": exec_decisions,
            "completion_ratio": completion,
            "active_projects": active_projects,
            "stale_thread_count": stale_count,
            "pod_count": pod_count,
            "fragmentation_index": fragmentation,
        }
    finally:
        s.close()


@app.get("/metrics/open_loops")
async def get_open_loops(limit: int = 50):
    """Unfinished loop heatmap data."""
    s = get_session(engine)
    try:
        rows = (
            s.query(OpenLoop)
            .filter(~OpenLoop.is_closed)
            .order_by(OpenLoop.days_open.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "text": r.text,
                "days_open": r.days_open,
                "conversation_id": r.conversation_id,
            }
            for r in rows
        ]
    finally:
        s.close()


@app.get("/metrics/tech_stack")
async def tech_stack_frequency():
    """Word cloud source: tech keyword mention frequencies."""
    s = get_session(engine)
    try:
        freq: dict[str, int] = {}
        for (stack,) in s.query(Conversation.tech_stack).all():
            for tech in stack or []:
                freq[tech] = freq.get(tech, 0) + 1
        return sorted(
            [{"tech": k, "count": v} for k, v in freq.items()],
            key=lambda x: x["count"],
            reverse=True,
        )
    finally:
        s.close()


@app.get("/metrics/projects")
async def projects_activity():
    """Per-project activity and completion."""
    s = get_session(engine)
    try:
        return [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "status": p.status,
                "is_strategic": p.is_strategic,
                "completion_ratio": p.completion_ratio,
                "pod_count": len(p.pods),
            }
            for p in s.query(Project).all()
        ]
    finally:
        s.close()


@app.get("/metrics/emotional_volatility")
async def emotional_volatility():
    """Emotion marker frequencies for volatility gauge."""
    s = get_session(engine)
    try:
        freq: dict[str, int] = {}
        for (markers,) in s.query(Conversation.emotional_markers).all():
            for m in markers or []:
                freq[m] = freq.get(m, 0) + 1
        return sorted(
            [{"emotion": k, "count": v} for k, v in freq.items()],
            key=lambda x: x["count"],
            reverse=True,
        )
    finally:
        s.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("dashboard.app:app", host="0.0.0.0", port=8000, reload=True)
