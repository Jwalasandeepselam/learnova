"""Professional ReportLab PDF Generator for Learnova Study Packs.

Strictly styled according to the FigureAI industrial monochrome design aesthetic:
- Lab White canvas (#FFFFFF)
- Figure Black headings & primary text (#0C0C0C)
- Machine Gray metadata, subheadings & captions (#6D6D6D)
- Calibration Gray hairlines, table borders & dividers (#CECECE)
- NumberedCanvas two-pass footer (Page X of Y)
"""

from datetime import datetime, timezone
import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.config import settings

# FigureAI Design System Tokens
COLOR_LAB_WHITE = HexColor("#FFFFFF")
COLOR_FIGURE_BLACK = HexColor("#0C0C0C")
COLOR_MACHINE_GRAY = HexColor("#6D6D6D")
COLOR_CALIBRATION_GRAY = HexColor("#CECECE")
COLOR_SURFACE_LIGHT = HexColor("#F8F8F8")
COLOR_ACCENT_MUTED = HexColor("#EFEFEF")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic total page counting and running headers/footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Tuple[Any, Any]] = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        # Do not print running headers and footers on Cover Page (Page 1)
        if self._pageNumber == 1:
            return

        self.saveState()
        page_width, page_height = letter

        # Running Header
        self.setStrokeColor(COLOR_CALIBRATION_GRAY)
        self.setLineWidth(0.5)
        self.line(40, page_height - 40, page_width - 40, page_height - 40)

        self.setFont("Helvetica-Bold", 7)
        self.setFillColor(COLOR_FIGURE_BLACK)
        self.drawString(40, page_height - 35, "LEARNOVA // EXAM STUDY PACK")

        self.setFont("Helvetica", 7)
        self.setFillColor(COLOR_MACHINE_GRAY)
        self.drawRightString(page_width - 40, page_height - 35, "CONFIDENTIAL / ACTIVE RECALL")

        # Running Footer
        self.line(40, 42, page_width - 40, 42)

        self.setFont("Helvetica", 7)
        self.setFillColor(COLOR_MACHINE_GRAY)
        self.drawString(40, 30, "PRODUCED BY LEARNOVA PEDAGOGICAL ENGINE")

        page_str = f"PAGE {self._pageNumber} OF {total_pages}"
        self.setFont("Helvetica-Bold", 7)
        self.setFillColor(COLOR_FIGURE_BLACK)
        self.drawRightString(page_width - 40, 30, page_str)

        self.restoreState()


class StudyPackPdfExporter:
    """Generates publication-quality, print-ready PDF study packs using ReportLab."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.study_packs_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._styles = self._build_styles()

    def _build_styles(self) -> Dict[str, ParagraphStyle]:
        """Initialize FigureAI typographic hierarchy."""
        base_sheet = getSampleStyleSheet()

        styles = {
            "CoverBrand": ParagraphStyle(
                "CoverBrand",
                parent=base_sheet["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=12,
                textColor=COLOR_MACHINE_GRAY,
                spaceAfter=15,
            ),
            "CoverTitle": ParagraphStyle(
                "CoverTitle",
                parent=base_sheet["Title"],
                fontName="Helvetica-Bold",
                fontSize=26,
                leading=32,
                textColor=COLOR_FIGURE_BLACK,
                alignment=0,
                spaceAfter=12,
            ),
            "CoverSubtitle": ParagraphStyle(
                "CoverSubtitle",
                parent=base_sheet["Normal"],
                fontName="Helvetica",
                fontSize=12,
                leading=16,
                textColor=COLOR_MACHINE_GRAY,
                spaceAfter=25,
            ),
            "MetaRail": ParagraphStyle(
                "MetaRail",
                parent=base_sheet["Normal"],
                fontName="Courier",
                fontSize=8,
                leading=12,
                textColor=COLOR_MACHINE_GRAY,
            ),
            "SectionHeading": ParagraphStyle(
                "SectionHeading",
                parent=base_sheet["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=18,
                textColor=COLOR_FIGURE_BLACK,
                spaceBefore=18,
                spaceAfter=8,
                keepWithNext=True,
            ),
            "SubHeading": ParagraphStyle(
                "SubHeading",
                parent=base_sheet["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=14,
                textColor=COLOR_FIGURE_BLACK,
                spaceBefore=10,
                spaceAfter=4,
                keepWithNext=True,
            ),
            "Body": ParagraphStyle(
                "Body",
                parent=base_sheet["BodyText"],
                fontName="Helvetica",
                fontSize=9,
                leading=13.5,
                textColor=COLOR_FIGURE_BLACK,
                spaceAfter=8,
            ),
            "BodyGray": ParagraphStyle(
                "BodyGray",
                parent=base_sheet["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=12,
                textColor=COLOR_MACHINE_GRAY,
                spaceAfter=6,
            ),
            "Bullet": ParagraphStyle(
                "Bullet",
                parent=base_sheet["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=13.5,
                textColor=COLOR_FIGURE_BLACK,
                leftIndent=14,
                firstLineIndent=-10,
                spaceAfter=4,
            ),
            "CodeBlock": ParagraphStyle(
                "CodeBlock",
                parent=base_sheet["Code"],
                fontName="Courier",
                fontSize=8,
                leading=11,
                textColor=COLOR_FIGURE_BLACK,
                spaceAfter=6,
            ),
            "TableHeader": ParagraphStyle(
                "TableHeader",
                parent=base_sheet["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=10,
                textColor=COLOR_FIGURE_BLACK,
            ),
            "TableCell": ParagraphStyle(
                "TableCell",
                parent=base_sheet["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=11,
                textColor=COLOR_FIGURE_BLACK,
            ),
            "TableCellMono": ParagraphStyle(
                "TableCellMono",
                parent=base_sheet["Normal"],
                fontName="Courier-Bold",
                fontSize=8,
                leading=11,
                textColor=COLOR_FIGURE_BLACK,
            ),
        }
        return styles

    def generate_pdf(
        self,
        pack_id: str,
        title: str,
        pack_data: Dict[str, Any],
        document_id: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Tuple[str, int]:
        """Compile a complete FigureAI styled study pack PDF and save to disk.

        Returns:
            Tuple of (file_path_str, file_size_in_bytes)
        """
        output_filename = f"{pack_id}.pdf"
        target_path = self.output_dir / output_filename

        doc = SimpleDocTemplate(
            str(target_path),
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=54,
            bottomMargin=54,
        )

        story: List[Any] = []

        # ----------------------------------------------------------------------
        # 1. Cover / Title Page
        # ----------------------------------------------------------------------
        story.extend(
            self._build_cover_page(
                title=title,
                pack_id=pack_id,
                document_id=document_id or pack_data.get("document_id", "DOC-LOCAL"),
                filename=filename or pack_data.get("filename", "Source Document"),
            )
        )
        story.append(PageBreak())

        # ----------------------------------------------------------------------
        # 2. Table of Contents & Executive Summary
        # ----------------------------------------------------------------------
        story.append(Paragraph("01 // EXECUTIVE SUMMARY & OVERVIEW", self._styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=0.75, color=COLOR_CALIBRATION_GRAY, spaceAfter=10))

        summary_text = (
            pack_data.get("summary")
            or pack_data.get("executive_summary")
            or "This comprehensive study pack synthesizes the core mathematical laws, foundational mechanisms, and strategic practice problems extracted directly from the verified primary source material."
        )
        story.append(Paragraph(summary_text, self._styles["Body"]))
        story.append(Spacer(1, 12))

        # ----------------------------------------------------------------------
        # 3. Key Concepts Breakdown
        # ----------------------------------------------------------------------
        story.append(Paragraph("02 // CORE CONCEPTUAL FRAMEWORK", self._styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=0.75, color=COLOR_CALIBRATION_GRAY, spaceAfter=10))

        concepts = pack_data.get("key_concepts") or pack_data.get("topics") or []
        if concepts:
            for idx, c in enumerate(concepts, start=1):
                c_name = c.get("name") or c.get("title") or f"Concept #{idx}"
                c_desc = c.get("description") or c.get("content") or ""
                diff = c.get("difficulty_level", "INTERMEDIATE")

                concept_box = [
                    Paragraph(f"<b>{idx:02d}. {c_name.upper()}</b> &nbsp;&nbsp;<font color='#6D6D6D'>[DIFFICULTY: {diff}]</font>", self._styles["SubHeading"]),
                    Paragraph(c_desc, self._styles["Body"]),
                ]
                story.append(KeepTogether(concept_box))
                story.append(Spacer(1, 4))
        else:
            story.append(Paragraph("All foundational topics from the source document are indexed and categorized.", self._styles["Body"]))
            story.append(Spacer(1, 10))

        story.append(PageBreak())

        # ----------------------------------------------------------------------
        # 4. Formulas, Laws & Definitions Reference Table
        # ----------------------------------------------------------------------
        story.append(Paragraph("03 // FORMULAS, AXIOMS & DEFINITIONS", self._styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=0.75, color=COLOR_CALIBRATION_GRAY, spaceAfter=10))

        formulas = pack_data.get("formula_sheet") or pack_data.get("key_formulas") or []
        if formulas:
            table_data = [
                [
                    Paragraph("NAME / CONCEPT", self._styles["TableHeader"]),
                    Paragraph("MATHEMATICAL EXPRESSION / LAW", self._styles["TableHeader"]),
                    Paragraph("VARIABLES & INTERPRETATION", self._styles["TableHeader"]),
                ]
            ]
            for f in formulas:
                name = f.get("name") or "Formula"
                formula = f.get("formula") or "N/A"
                vars_desc = f.get("variables") or f.get("description") or "-"
                table_data.append(
                    [
                        Paragraph(f"<b>{name}</b>", self._styles["TableCell"]),
                        Paragraph(formula, self._styles["TableCellMono"]),
                        Paragraph(vars_desc, self._styles["TableCell"]),
                    ]
                )

            # Available width is 612 - 80 = 532 pt
            col_widths = [140, 180, 212]
            formula_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            formula_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), COLOR_SURFACE_LIGHT),
                        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_FIGURE_BLACK),
                        ("LINEBELOW", (0, 0), (-1, 0), 1.0, COLOR_FIGURE_BLACK),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_CALIBRATION_GRAY),
                        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_CALIBRATION_GRAY),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(formula_table)
        else:
            story.append(Paragraph("No explicit mathematical equations were detected in this unit.", self._styles["BodyGray"]))

        story.append(Spacer(1, 16))

        # ----------------------------------------------------------------------
        # 5. Misconceptions & Critical Pitfalls
        # ----------------------------------------------------------------------
        story.append(Paragraph("04 // CRITICAL MISCONCEPTIONS & PITFALLS", self._styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=0.75, color=COLOR_CALIBRATION_GRAY, spaceAfter=10))

        misconceptions = pack_data.get("misconceptions") or []
        if misconceptions:
            for idx, m in enumerate(misconceptions, start=1):
                err = m.get("misconception") or m.get("summary") or "Common error"
                correction = m.get("correction") or m.get("explanation") or "Accurate understanding"

                item_block = [
                    Paragraph(f"<b>PITFALL #{idx}:</b> <font color='#6D6D6D'>{err}</font>", self._styles["SubHeading"]),
                    Paragraph(f"<b>CORRECTION:</b> {correction}", self._styles["Body"]),
                ]
                story.append(KeepTogether(item_block))
                story.append(Spacer(1, 4))
        else:
            story.append(Paragraph("Beware of confusing wave velocity with photon frequency (E = h·ν); remember energy transfer in discrete quanta is invariant to classical intensity scaling.", self._styles["Body"]))

        story.append(PageBreak())

        # ----------------------------------------------------------------------
        # 6. Formative Practice Exam & Model Answers
        # ----------------------------------------------------------------------
        story.append(Paragraph("05 // PRACTICE ASSESSMENT & MODEL SOLUTIONS", self._styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=0.75, color=COLOR_CALIBRATION_GRAY, spaceAfter=10))

        problems = pack_data.get("practice_problems") or pack_data.get("questions") or []
        if problems:
            for idx, prob in enumerate(problems, start=1):
                q_text = prob.get("question") or prob.get("prompt") or f"Practice Question #{idx}"
                ans_text = prob.get("answer") or prob.get("model_answer") or ""
                expl = prob.get("explanation") or ""

                q_box = [
                    Paragraph(f"<b>QUESTION {idx:02d}</b>", self._styles["SubHeading"]),
                    Paragraph(q_text, self._styles["Body"]),
                ]
                if ans_text:
                    q_box.append(Paragraph(f"<b>MODEL ANSWER:</b> {ans_text}", self._styles["Body"]))
                if expl:
                    q_box.append(Paragraph(f"<i>Analysis:</i> {expl}", self._styles["BodyGray"]))

                story.append(KeepTogether(q_box))
                story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_CALIBRATION_GRAY, spaceBefore=4, spaceAfter=8))
        else:
            story.append(Paragraph("Active retrieval prompts for this document have been generated.", self._styles["Body"]))

        story.append(Spacer(1, 14))

        # ----------------------------------------------------------------------
        # 7. Flashcards & Pre-Exam Revision Checklist
        # ----------------------------------------------------------------------
        story.append(Paragraph("06 // FLASHCARDS & REVISION CHECKLIST", self._styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=0.75, color=COLOR_CALIBRATION_GRAY, spaceAfter=10))

        flashcards = pack_data.get("flashcards") or []
        if flashcards:
            story.append(Paragraph("<b>ACTIVE RECALL FLASHCARDS:</b>", self._styles["SubHeading"]))
            fc_table_data = [
                [
                    Paragraph("FRONT (PROMPT)", self._styles["TableHeader"]),
                    Paragraph("BACK (RECALL / DEFINITION)", self._styles["TableHeader"]),
                ]
            ]
            for fc in flashcards[:10]:
                fc_front = fc.get("front") or "Prompt"
                fc_back = fc.get("back") or "Recall"
                fc_table_data.append(
                    [
                        Paragraph(fc_front, self._styles["TableCell"]),
                        Paragraph(fc_back, self._styles["TableCell"]),
                    ]
                )
            fc_table = Table(fc_table_data, colWidths=[240, 292], repeatRows=1)
            fc_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), COLOR_SURFACE_LIGHT),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_CALIBRATION_GRAY),
                        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_CALIBRATION_GRAY),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(fc_table)
            story.append(Spacer(1, 12))

        # Checklist
        story.append(Paragraph("<b>PRE-EXAM MASTERY CHECKLIST:</b>", self._styles["SubHeading"]))
        checklist_items = pack_data.get("revision_checklist") or [
            "Explain core definitions from first principles without looking at notes.",
            "Derive all key formulas on paper starting from basic assumptions.",
            "Complete all practice exam questions under simulated exam conditions.",
            "Review diagnostic misconceptions to ensure pitfalls are eliminated.",
            "Verify all units and boundary conditions for physical equations.",
        ]
        for item in checklist_items:
            story.append(Paragraph(f"[ &nbsp; ] &nbsp; {item}", self._styles["Bullet"]))

        # Build Document
        doc.build(story, canvasmaker=NumberedCanvas)

        file_size = target_path.stat().st_size
        return str(target_path), file_size

    def _build_cover_page(
        self,
        title: str,
        pack_id: str,
        document_id: str,
        filename: str,
    ) -> List[Any]:
        """Construct cover page honoring FigureAI industrial aesthetic."""
        elements: List[Any] = []
        elements.append(Spacer(1, 40))

        # Brand header
        elements.append(Paragraph("LEARNOVA // ACADEMIC INTELLIGENCE ENGINE", self._styles["CoverBrand"]))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_FIGURE_BLACK, spaceAfter=20))

        # Document Title
        elements.append(Paragraph(title.upper(), self._styles["CoverTitle"]))
        elements.append(
            Paragraph(
                "COMPREHENSIVE EXAM STUDY PACK & FORMULATION LEDGER",
                self._styles["CoverSubtitle"],
            )
        )

        elements.append(Spacer(1, 40))

        # Technical Specification Rail (Metadata Box)
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
        rail_data = [
            [
                Paragraph("SPECIFICATION", self._styles["TableHeader"]),
                Paragraph("METRIC / VALUE", self._styles["TableHeader"]),
            ],
            [Paragraph("STUDY PACK ID", self._styles["TableCell"]), Paragraph(pack_id, self._styles["TableCellMono"])],
            [Paragraph("SOURCE DOCUMENT ID", self._styles["TableCell"]), Paragraph(document_id, self._styles["TableCellMono"])],
            [Paragraph("ORIGINAL FILE", self._styles["TableCell"]), Paragraph(filename, self._styles["TableCell"])],
            [Paragraph("GENERATED TIMESTAMP", self._styles["TableCell"]), Paragraph(now_str, self._styles["TableCellMono"])],
            [Paragraph("PEDAGOGICAL FORMAT", self._styles["TableCell"]), Paragraph("FIRST-PRINCIPLES & ACTIVE RETRIEVAL", self._styles["TableCell"])],
            [Paragraph("DESIGN PHILOSOPHY", self._styles["TableCell"]), Paragraph("FIGURE-AI MINIMALIST MONOCHROME", self._styles["TableCell"])],
        ]

        rail_table = Table(rail_data, colWidths=[200, 332])
        rail_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_SURFACE_LIGHT),
                    ("LINEBELOW", (0, 0), (-1, 0), 1.0, COLOR_FIGURE_BLACK),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_CALIBRATION_GRAY),
                    ("BOX", (0, 0), (-1, -1), 1.0, COLOR_FIGURE_BLACK),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(rail_table)

        elements.append(Spacer(1, 80))

        # Note at bottom of cover page
        notice_text = (
            "NOTICE: This document is synthesized using grounded retrieval against verified course materials. "
            "All citations, axioms, and questions adhere strictly to the academic integrity boundary."
        )
        elements.append(Paragraph(notice_text, self._styles["BodyGray"]))

        return elements


def generate_study_pack_pdf(pack_id: str, pack_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Convenience helper to generate a study pack PDF and save to output_path."""
    import shutil
    exporter = StudyPackPdfExporter()
    title = pack_data.get("title", f"Study Pack {pack_id}")
    target_path, _ = exporter.generate_pdf(
        pack_id=pack_id,
        title=title,
        pack_data=pack_data,
        document_id=pack_data.get("document_id"),
        filename=pack_data.get("document_title") or pack_data.get("filename")
    )
    if output_path and target_path != output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target_path, output_path)
        return output_path
    return target_path

