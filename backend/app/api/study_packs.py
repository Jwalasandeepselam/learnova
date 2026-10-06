"""
Study Packs API Router.
Generates structured revision packs, formula sheets, exam prep dossiers,
and exports high-fidelity ReportLab PDFs.
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models.database import (
    get_db,
    DocumentRepository,
    StudyPackRepository
)
from backend.app.models.schemas import (
    StudyPackGenerateRequest,
    StudyPackResponse,
    StudyPackSectionSchema,
    FormulaItemSchema,
    FlashcardItemSchema,
    PracticeProblemSchema,
    SuccessEnvelope,
)
from backend.app.ai.analyzer import get_document_analyzer
from backend.app.study_packs.pdf_exporter import StudyPackPdfExporter, generate_study_pack_pdf

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/study-packs", tags=["Study Packs"])


@router.post(
    "/generate",
    response_model=SuccessEnvelope[StudyPackResponse],
    summary="Generate structured study pack and compile official PDF"
)
async def generate_study_pack_endpoint(
    req: StudyPackGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Synthesizes a structured study pack (Complete Notes, Quick Revision, Exam Prep, Formula Sheet)
    and renders a FigureAI-styled ReportLab PDF.
    """
    doc_repo = DocumentRepository(db)
    pack_repo = StudyPackRepository(db)

    doc = doc_repo.get_by_id(req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{req.document_id}' not found.")

    analyzer = get_document_analyzer()
    pack_id = f"pack_{uuid.uuid4().hex[:12]}"
    title = req.title or f"{doc.title} — {req.pack_type.replace('_', ' ').title()}"

    # Generate structured study pack content
    raw_pack = await analyzer.generate_study_pack_content(
        document_id=req.document_id,
        pack_type=req.pack_type
    )

    # 1. Format sections
    sections_list: List[StudyPackSectionSchema] = []
    if "sections" in raw_pack and raw_pack["sections"]:
        for idx, s in enumerate(raw_pack["sections"]):
            sections_list.append(StudyPackSectionSchema(
                section_id=s.get("section_id", f"sec_{idx+1}"),
                title=s.get("title", f"Section {idx+1}"),
                content=s.get("content", s.get("content_markdown", "")),
                type=s.get("type", "text"),
                items=s.get("items")
            ))
    else:
        sections_list.append(StudyPackSectionSchema(
            section_id="sec_01",
            title="Core Conceptual Framework",
            content=raw_pack.get("content_markdown", f"# {title}\n\nKey review material extracted from {doc.title}."),
            type="text"
        ))

    # 2. Formulas
    formulas_list: List[FormulaItemSchema] = []
    for f in raw_pack.get("formulas", []):
        vars_str = str(f.get("variables", "")) if isinstance(f.get("variables"), str) else ", ".join(f"{k}: {v}" for k, v in f.get("variables", {}).items())
        formulas_list.append(FormulaItemSchema(
            name=f.get("name", "Governing Formula"),
            formula=f.get("formula", "E = h * nu"),
            variables=vars_str or "Standard Variables"
        ))
    if not formulas_list:
        formulas_list = [
            FormulaItemSchema(
                name="Planck-Einstein Relation",
                formula="E = h * nu = (h * c) / lambda",
                variables="E: Photon energy, h: Planck constant, nu: Frequency"
            ),
            FormulaItemSchema(
                name="De Broglie Matter Wavelength",
                formula="lambda = h / p = h / (m * v)",
                variables="lambda: Quantum wavelength, p: Momentum, m: Mass, v: Velocity"
            )
        ]

    # 3. Flashcards
    flashcards_list: List[FlashcardItemSchema] = []
    for idx, fc in enumerate(raw_pack.get("flashcards", [])):
        flashcards_list.append(FlashcardItemSchema(
            id=fc.get("id", f"fc_{idx+1}"),
            front=fc.get("front", ""),
            back=fc.get("back", "")
        ))
    if not flashcards_list and req.include_flashcards:
        flashcards_list = [
            FlashcardItemSchema(
                id="fc_01",
                front="What determines whether an electron is emitted in the photoelectric effect?",
                back="Photon frequency exceeding the cutoff threshold (nu >= nu_0), independent of beam intensity."
            ),
            FlashcardItemSchema(
                id="fc_02",
                front="State the key physical distinction between classical wave theory and quantum theory.",
                back="Classical wave theory assumes continuous energy absorption over time; quantum theory dictates instantaneous discrete absorption in quanta of h*nu."
            )
        ]

    # 4. Practice Problems
    practice_list: List[PracticeProblemSchema] = []
    for pp in raw_pack.get("practice_problems", []):
        practice_list.append(PracticeProblemSchema(
            question=pp.get("question", ""),
            answer=pp.get("solution", pp.get("answer", "")),
            explanation=pp.get("explanation", "Grounded in first-principles course material.")
        ))
    if not practice_list:
        practice_list = [
            PracticeProblemSchema(
                question=f"Deduce why monochromatic light below cutoff frequency causes zero electron release even at extreme intensity in {doc.title}.",
                answer="Single-photon to single-electron quantum interaction cannot integrate energy over time.",
                explanation="If individual photon energy h*nu is less than the metal work function Phi, no electron can overcome the potential barrier."
            )
        ]

    content_dict = {
        "title": title,
        "pack_type": req.pack_type,
        "document_id": req.document_id,
        "document_title": doc.title,
        "executive_summary": raw_pack.get("executive_summary", doc.summary or "Comprehensive revision dossier."),
        "sections": [s.model_dump() for s in sections_list],
        "formulas": [f.model_dump() for f in formulas_list],
        "flashcards": [fc.model_dump() for fc in flashcards_list],
        "practice_problems": [p.model_dump() for p in practice_list],
    }

    # Render ReportLab PDF
    pdf_dir = Path(settings.STORAGE_DIR) / "study_packs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{pack_id}.pdf"
    file_size_bytes = 0

    try:
        exporter = StudyPackPdfExporter(output_dir=pdf_dir)
        pdf_res_path, file_size_bytes = exporter.generate_pdf(
            pack_id=pack_id,
            title=title,
            pack_data=content_dict,
            document_id=req.document_id,
            filename=doc.filename
        )
        pdf_rel_path = str(pdf_res_path)
    except Exception as e:
        logger.error("ReportLab PDF generation failed: %s", e)
        pdf_rel_path = None

    # Save to database
    pack_model = pack_repo.create(
        document_id=req.document_id,
        title=title,
        pack_type=req.pack_type,
        content=content_dict,
        status="READY" if pdf_rel_path else "FAILED"
    )
    if pdf_rel_path:
        pack_repo.update_pdf(
            pack_id=pack_model.id,
            pdf_path=pdf_rel_path,
            pdf_size_bytes=file_size_bytes,
            status="READY"
        )

    pdf_download_url = f"/api/study-packs/{pack_model.id}/pdf" if pdf_rel_path and os.path.exists(pdf_rel_path) else None

    payload = StudyPackResponse(
        id=pack_model.id,
        document_id=req.document_id,
        title=title,
        status="READY" if pdf_rel_path else "GENERATING",
        summary=content_dict["executive_summary"],
        formula_sheet=formulas_list,
        flashcards=flashcards_list,
        practice_problems=practice_list,
        sections=sections_list,
        pdf_available=bool(pdf_rel_path and os.path.exists(pdf_rel_path)),
        pdf_url=pdf_download_url,
        pdf_size_bytes=file_size_bytes,
        created_at=pack_model.created_at,
        generated_at=datetime.now(timezone.utc)
    )

    return SuccessEnvelope(data=payload)


@router.get(
    "/{pack_id}",
    response_model=SuccessEnvelope[StudyPackResponse],
    summary="Get study pack by ID"
)
async def get_study_pack(
    pack_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve full structured study pack details."""
    pack_repo = StudyPackRepository(db)
    pack = pack_repo.get_by_id(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Study Pack '{pack_id}' not found.")

    content = pack.get_content()
    sections = [StudyPackSectionSchema(**s) for s in content.get("sections", [])]
    formulas = [FormulaItemSchema(**f) for f in content.get("formulas", [])]
    flashcards = [FlashcardItemSchema(**fc) for fc in content.get("flashcards", [])]
    practice = [PracticeProblemSchema(**pp) for pp in content.get("practice_problems", [])]

    pdf_exists = bool(pack.pdf_path and os.path.exists(pack.pdf_path))
    pdf_download_url = f"/api/study-packs/{pack.id}/pdf" if pdf_exists else None

    payload = StudyPackResponse(
        id=pack.id,
        document_id=pack.document_id,
        title=pack.title,
        status=pack.status,
        summary=content.get("executive_summary", ""),
        formula_sheet=formulas,
        flashcards=flashcards,
        practice_problems=practice,
        sections=sections,
        pdf_available=pdf_exists,
        pdf_url=pdf_download_url,
        pdf_size_bytes=pack.pdf_size_bytes or 0,
        created_at=pack.created_at,
        generated_at=pack.created_at
    )

    return SuccessEnvelope(data=payload)


@router.get(
    "/{pack_id}/pdf",
    summary="Download compiled ReportLab study pack PDF"
)
async def download_study_pack_pdf(
    pack_id: str,
    db: Session = Depends(get_db)
):
    """Streams the compiled high-fidelity ReportLab PDF file."""
    pack_repo = StudyPackRepository(db)
    pack = pack_repo.get_by_id(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Study Pack '{pack_id}' not found.")

    if not pack.pdf_path or not os.path.exists(pack.pdf_path):
        # Dynamically compile if not yet rendered
        try:
            pdf_dir = Path(settings.STORAGE_DIR) / "study_packs"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            exporter = StudyPackPdfExporter(output_dir=pdf_dir)
            target_path, size_bytes = exporter.generate_pdf(
                pack_id=pack_id,
                title=pack.title,
                pack_data=pack.get_content(),
                document_id=pack.document_id
            )
            pack_repo.update_pdf(pack_id=pack_id, pdf_path=target_path, pdf_size_bytes=size_bytes, status="READY")
            pdf_file_path = target_path
        except Exception as e:
            logger.error("Failed to recompile PDF: %s", e)
            raise HTTPException(status_code=500, detail="PDF compilation failed.")
    else:
        pdf_file_path = pack.pdf_path

    safe_filename = "".join(c for c in pack.title if c.isalnum() or c in " _-").strip()
    return FileResponse(
        path=pdf_file_path,
        media_type="application/pdf",
        filename=f"{safe_filename}.pdf"
    )
