from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal

class CalibrationRequest(BaseModel):
    page_number: int = Field(ge=1)
    pixel_distance: float = Field(gt=0)
    real_distance: float = Field(gt=0)
    unit: Literal["mm", "cm", "m", "in", "ft"]

class CandidateDecision(BaseModel):
    candidate_id: str
    decision: Literal["approved", "rejected", "needs_review"]
    notes: str = ""

class ApprovalRequest(BaseModel):
    decisions: list[CandidateDecision]
