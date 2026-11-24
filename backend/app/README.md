# Backend API

The FastAPI service accepts PDF uploads at `POST /api/pdf/import`, inspects page dimensions/content, renders page previews, and emits low-confidence text/rectangle candidates for review.

Run from repository root with `uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000`.

Current limitations: document metadata and review state are held in process memory; PDFs are stored under `./data`. Restarting the API loses in-memory metadata. Scanned drawing recognition/OCR, two-point calibration, project persistence, CAD geometry transfer, STAAD.Pro automation and structural calculations are not implemented.
