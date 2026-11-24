from __future__ import annotations
import hashlib, os, uuid
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from .pdf_importer import inspect_pdf, extract_candidates
from .schemas import CalibrationRequest, ApprovalRequest

MAX_UPLOAD_BYTES = 30 * 1024 * 1024
DATA_DIR = Path(os.getenv("STRUCTURAL_AUTOMATION_DATA", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
documents: dict[str, dict] = {}

app = FastAPI(title="Structural Automation API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173","http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health():
    return {"status":"ok", "service":"structural-automation", "engineering_analysis":"not_implemented"}

@app.post("/api/pdf/import")
async def import_pdf(file: UploadFile = File(...)):
    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(400, "Upload a PDF file.")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "PDF exceeds the 30 MB upload limit.")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(400, "The uploaded file does not have a valid PDF signature.")
    try:
        inspection = inspect_pdf(data)
        candidates = extract_candidates(data)
    except Exception as exc:
        raise HTTPException(422, f"Unable to inspect PDF: {exc}") from exc
    doc_id = str(uuid.uuid4())
    digest = hashlib.sha256(data).hexdigest()
    safe_name = Path(file.filename).name[:120]
    (DATA_DIR / f"{doc_id}.pdf").write_bytes(data)
    documents[doc_id] = {"filename":safe_name, "sha256":digest, "candidates":candidates, "approved_geometry":[]}
    return {"document_id":doc_id, "filename":safe_name, "sha256":digest, "inspection":inspection, "candidates":candidates,
            "notice":"All detections are unverified candidates. No project geometry was changed."}

@app.post("/api/pdf/{document_id}/calibrate")
def calibrate(document_id: str, request: CalibrationRequest):
    if document_id not in documents:
        raise HTTPException(404, "PDF document not found.")
    if request.page_number > 100:
        raise HTTPException(400, "Invalid page number.")
    points_per_unit = request.pixel_distance / request.real_distance
    result = {"page_number":request.page_number,"pixel_distance":request.pixel_distance,
              "real_distance":request.real_distance,"unit":request.unit,
              "points_per_unit":round(points_per_unit,8),
              "warning":"Calibration is stored as a user-supplied reference. Confirm the selected endpoints and page before using dimensions."}
    documents[document_id].setdefault("calibrations",[]).append(result)
    return result

@app.post("/api/pdf/{document_id}/review")
def review(document_id: str, request: ApprovalRequest):
    record = documents.get(document_id)
    if record is None:
        raise HTTPException(404, "PDF document not found.")
    by_id = {c["candidate_id"]: c for c in record["candidates"]}
    approved = []
    for decision in request.decisions:
        candidate = by_id.get(decision.candidate_id)
        if candidate is None:
            raise HTTPException(400, f"Unknown candidate: {decision.candidate_id}")
        candidate["status"] = decision.decision
        candidate["review_notes"] = decision.notes
        if decision.decision == "approved":
            approved.append(candidate.copy())
    record["approved_geometry"] = approved
    return {"document_id":document_id,"approved_count":len(approved),"approved_candidates":approved,
            "notice":"Approval records review status only; candidates are not yet mapped into a structural analysis model."}

@app.get("/api/pdf/{document_id}")
def get_document(document_id: str):
    record = documents.get(document_id)
    if record is None:
        raise HTTPException(404, "PDF document not found.")
    return {"document_id":document_id, **record}

@app.get("/")
def root():
    return {"message":"Structural Automation API","docs":"/docs"}
