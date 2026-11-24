from __future__ import annotations
import base64, hashlib, re
from typing import Any
import fitz

MAX_PAGES = 100
RENDER_DPI = 110

def _b64_png(page: fitz.Page) -> str:
    pix = page.get_pixmap(matrix=fitz.Matrix(RENDER_DPI / 72, RENDER_DPI / 72), alpha=False)
    return base64.b64encode(pix.tobytes("png")).decode("ascii")

def inspect_pdf(data: bytes) -> dict[str, Any]:
    doc = fitz.open(stream=data, filetype="pdf")
    if doc.is_encrypted:
        raise ValueError("Password-protected PDFs are not supported yet.")
    if len(doc) == 0:
        raise ValueError("The PDF contains no pages.")
    if len(doc) > MAX_PAGES:
        raise ValueError(f"PDF has {len(doc)} pages; limit is {MAX_PAGES}.")
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        drawings = page.get_drawings()
        images = page.get_images(full=True)
        rect = page.rect
        # Heuristic only: page is classified as scanned when it has substantial image area
        # and little extractable text/vector geometry.
        image_area = 0.0
        for img in images:
            try:
                info = doc.extract_image(img[0])
                # Image presence is evidence, not proof of a scan.
                image_area = max(image_area, 1.0 if info.get("width", 0) * info.get("height", 0) > 500_000 else 0.0)
            except Exception:
                pass
        kind = "likely_scanned" if image_area and len(text.strip()) < 40 and len(drawings) < 10 else "likely_vector_or_mixed"
        pages.append({
            "page_number": i + 1,
            "width_points": round(rect.width, 2),
            "height_points": round(rect.height, 2),
            "rotation": page.rotation,
            "orientation": "landscape" if rect.width > rect.height else "portrait",
            "content_type": kind,
            "text_characters": len(text),
            "drawing_objects": len(drawings),
            "embedded_images": len(images),
            "preview_png_base64": _b64_png(page),
        })
    return {"page_count": len(doc), "pages": pages}

def extract_candidates(data: bytes) -> list[dict[str, Any]]:
    doc = fitz.open(stream=data, filetype="pdf")
    candidates: list[dict[str, Any]] = []
    for page_index, page in enumerate(doc):
        page_no = page_index + 1
        # Candidate grid labels from text spans. These are annotations, not confirmed grids.
        for word in page.get_text("words"):
            label = str(word[4]).strip()
            if re.fullmatch(r"[A-Z]{1,2}|[0-9]{1,3}", label):
                x0, y0, x1, y1 = word[:4]
                candidates.append({
                    "candidate_id": hashlib.sha1(f"{page_no}:label:{label}:{x0:.1f}:{y0:.1f}".encode()).hexdigest()[:12],
                    "element_type": "grid_label_candidate", "page_number": page_no,
                    "label": label, "bbox_points": [round(x0,2), round(y0,2), round(x1,2), round(y1,2)],
                    "confidence": 0.25, "status": "needs_review",
                    "source": "PDF text extraction",
                    "warning": "Text token resembles a grid label; verify against the drawing."
                })
        # Closed rectangular vector paths are possible column symbols; no semantic inference.
        for drawing in page.get_drawings():
            rect = drawing.get("rect")
            items = drawing.get("items", [])
            if rect is None or not items:
                continue
            w, h = abs(rect.width), abs(rect.height)
            if w < 3 or h < 3 or w > 120 or h > 120:
                continue
            if abs(w-h) > max(w,h) * 0.45:
                continue
            # Keep only simple rectangle-like paths; mark as low-confidence symbol candidates.
            if len(items) <= 6:
                x, y = rect.x0, rect.y0
                candidates.append({
                    "candidate_id": hashlib.sha1(f"{page_no}:rect:{x:.2f}:{y:.2f}:{w:.2f}:{h:.2f}".encode()).hexdigest()[:12],
                    "element_type": "rectangular_symbol_candidate", "page_number": page_no,
                    "center_points": [round((rect.x0+rect.x1)/2,2), round((rect.y0+rect.y1)/2,2)],
                    "size_points": [round(w,2), round(h,2)],
                    "bbox_points": [round(rect.x0,2),round(rect.y0,2),round(rect.x1,2),round(rect.y1,2)],
                    "confidence": 0.2, "status": "needs_review",
                    "source": "PDF vector path",
                    "warning": "May be a column, symbol, or annotation; not classified automatically."
                })
    return candidates
