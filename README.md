# Structural Automation

AI-assisted structural engineering office application.

## Current status

This repository is being initialized. The first implementation milestone is the PDF plan intake and engineer-review workflow.

## Development setup

Requirements:
- Python 3.10+
- Node.js 20+
- Windows is recommended for later STAAD.Pro / OpenSTAAD integration.

### Backend

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

Open http://localhost:5173. For a tablet on the same trusted Wi-Fi, use the Windows PC's LAN IP and port 5173.

## Engineering safety

PDF extraction is assistive only. Detected geometry is unverified until reviewed and explicitly approved by an engineer. The application does not infer design loads, certify dimensions, or produce structural analysis results from drawings. Do not use unverified extraction output for construction or professional design.

## Roadmap

1. PDF upload, page inspection, preview, scale calibration, candidate geometry and approval.
2. Structural geometry editor and project integration.
3. STAAD.Pro model generation and validation.
4. Loads, OpenSTAAD analysis retrieval, design checks and deliverables.

Each engineering feature must document code editions, assumptions, units, limitations and verification status.
