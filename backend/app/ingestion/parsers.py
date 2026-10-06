"""Multi-format document parser for Learnova ingestion pipeline.

Supports PDF (via pdfplumber and pypdf), DOCX (via python-docx),
PPTX (via python-pptx), and TXT/Markdown documents.
Preserves page/slide numbers, extracts sections, and unifies output into ParsedDocument.
"""

from dataclasses import dataclass, field
import io
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union
import unicodedata


@dataclass
class DocumentSection:
    """Logical section or heading extracted from document content."""

    title: str
    level: int = 1
    start_page: int = 1
    content: str = ""


@dataclass
class DocumentPage:
    """Content and metadata for a specific physical page or presentation slide."""

    page_number: int  # 1-indexed
    text: str
    section_title: Optional[str] = None
    slide_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """Unified normalized document structure produced across all supported formats."""

    filename: str
    file_type: str
    total_pages: int
    sections: List[DocumentSection] = field(default_factory=list)
    pages: List[DocumentPage] = field(default_factory=list)
    raw_text: str = ""
    word_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentParser:
    """Unified document parser handling PDF, DOCX, PPTX, and TXT/Markdown formats."""

    HEADING_REGEX = re.compile(
        r"^(?:(?:\d+\.)+\d*\s+[A-Z][\w\s\-:]{2,80}|(?:Chapter|Section|Module|Unit|Lecture|Part)\s+\d+[\s\:\-].*|[A-Z][A-Z0-9\s\-:]{3,60})$",
        re.MULTILINE,
    )

    MD_HEADING_REGEX = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    @classmethod
    def parse_file(
        cls,
        file_source: Union[str, Path, bytes, io.BytesIO],
        original_filename: str = "document.pdf",
    ) -> ParsedDocument:
        """Parse file from path or bytes into a unified ParsedDocument."""
        suffix = Path(original_filename).suffix.lower()

        if isinstance(file_source, (str, Path)):
            path = Path(file_source)
            if not path.exists():
                raise FileNotFoundError(f"Source file not found at: {file_source}")
            with open(path, "rb") as f:
                data = f.read()
        elif isinstance(file_source, bytes):
            data = file_source
        elif isinstance(file_source, io.BytesIO):
            data = file_source.getvalue()
        else:
            raise ValueError(f"Unsupported file source type: {type(file_source)}")

        if suffix == ".pdf":
            return cls._parse_pdf(data, original_filename)
        elif suffix in (".docx", ".doc"):
            return cls._parse_docx(data, original_filename)
        elif suffix in (".pptx", ".ppt"):
            return cls._parse_pptx(data, original_filename)
        elif suffix in (".txt", ".md", ".markdown", ".rst"):
            return cls._parse_text(data, original_filename)
        else:
            # Fallback based on content sniffing or treat as plain text
            if data.startswith(b"%PDF"):
                return cls._parse_pdf(data, original_filename)
            elif data.startswith(b"PK\x03\x04"):
                # Could be docx or pptx zip container
                try:
                    return cls._parse_docx(data, original_filename)
                except Exception:
                    return cls._parse_pptx(data, original_filename)
            return cls._parse_text(data, original_filename)

    # --------------------------------------------------------------------------
    # PDF Parsing
    # --------------------------------------------------------------------------

    @classmethod
    def _parse_pdf(cls, data: bytes, filename: str) -> ParsedDocument:
        """Extract text and structure from PDF using pdfplumber with pypdf fallback."""
        pages: List[DocumentPage] = []
        full_text_parts: List[str] = []
        sections: List[DocumentSection] = []
        current_section: Optional[str] = None

        extracted_with_plumber = False
        try:
            import pdfplumber

            with pdfplumber.open(io.BytesIO(data)) as pdf:
                for idx, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text(layout=False) or ""
                    clean_text = cls._clean_text(page_text)

                    # Detect section heading on page
                    detected_title = cls._detect_page_heading(clean_text)
                    if detected_title:
                        current_section = detected_title
                        sections.append(
                            DocumentSection(
                                title=detected_title,
                                level=1,
                                start_page=idx,
                            )
                        )

                    pages.append(
                        DocumentPage(
                            page_number=idx,
                            text=clean_text,
                            section_title=current_section,
                            metadata={"page_width": page.width, "page_height": page.height},
                        )
                    )
                    if clean_text:
                        full_text_parts.append(clean_text)
                extracted_with_plumber = True
        except Exception:
            extracted_with_plumber = False

        if not extracted_with_plumber or not pages:
            pages = []
            full_text_parts = []
            sections = []
            current_section = None
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(data))
            for idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                clean_text = cls._clean_text(page_text)

                detected_title = cls._detect_page_heading(clean_text)
                if detected_title:
                    current_section = detected_title
                    sections.append(
                        DocumentSection(
                            title=detected_title,
                            level=1,
                            start_page=idx,
                        )
                    )

                pages.append(
                    DocumentPage(
                        page_number=idx,
                        text=clean_text,
                        section_title=current_section,
                    )
                )
                if clean_text:
                    full_text_parts.append(clean_text)

        raw_text = "\n\n".join(full_text_parts)
        word_count = len(raw_text.split())

        return ParsedDocument(
            filename=filename,
            file_type="application/pdf",
            total_pages=len(pages),
            sections=sections,
            pages=pages,
            raw_text=raw_text,
            word_count=word_count,
            metadata={"parser": "pdfplumber/pypdf"},
        )

    # --------------------------------------------------------------------------
    # DOCX Parsing
    # --------------------------------------------------------------------------

    @classmethod
    def _parse_docx(cls, data: bytes, filename: str) -> ParsedDocument:
        """Extract text and hierarchical headings from DOCX."""
        import docx

        doc = docx.Document(io.BytesIO(data))
        sections: List[DocumentSection] = []
        pages: List[DocumentPage] = []
        page_texts: List[str] = []
        current_page_idx = 1
        current_section = "Introduction"

        # Approximate 500 words per page for DOCX
        words_on_current_page = 0
        current_page_paragraphs: List[str] = []

        for p in doc.paragraphs:
            text = cls._clean_text(p.text)
            if not text:
                continue

            style_name = p.style.name if p.style else ""
            is_heading = (
                style_name.startswith("Heading")
                or style_name in ("Title", "Subtitle")
                or cls.HEADING_REGEX.match(text)
            )

            if is_heading:
                current_section = text
                level = 1
                if "2" in style_name:
                    level = 2
                elif "3" in style_name:
                    level = 3
                sections.append(
                    DocumentSection(
                        title=text,
                        level=level,
                        start_page=current_page_idx,
                    )
                )

            current_page_paragraphs.append(text)
            words_on_current_page += len(text.split())

            # Simulate page division every ~450 words or explicit section breaks
            if words_on_current_page >= 450:
                p_text = "\n\n".join(current_page_paragraphs)
                pages.append(
                    DocumentPage(
                        page_number=current_page_idx,
                        text=p_text,
                        section_title=current_section,
                    )
                )
                page_texts.append(p_text)
                current_page_idx += 1
                current_page_paragraphs = []
                words_on_current_page = 0

        # Flush remaining content
        if current_page_paragraphs:
            p_text = "\n\n".join(current_page_paragraphs)
            pages.append(
                DocumentPage(
                    page_number=current_page_idx,
                    text=p_text,
                    section_title=current_section,
                )
            )
            page_texts.append(p_text)

        # Fallback if empty
        if not pages:
            pages.append(
                DocumentPage(
                    page_number=1,
                    text="",
                    section_title="Empty Document",
                )
            )

        raw_text = "\n\n".join(page_texts)
        return ParsedDocument(
            filename=filename,
            file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            total_pages=len(pages),
            sections=sections,
            pages=pages,
            raw_text=raw_text,
            word_count=len(raw_text.split()),
            metadata={"parser": "python-docx"},
        )

    # --------------------------------------------------------------------------
    # PPTX Parsing
    # --------------------------------------------------------------------------

    @classmethod
    def _parse_pptx(cls, data: bytes, filename: str) -> ParsedDocument:
        """Extract text per slide from PowerPoint presentations."""
        import pptx

        prs = pptx.Presentation(io.BytesIO(data))
        pages: List[DocumentPage] = []
        sections: List[DocumentSection] = []
        full_text_parts: List[str] = []

        for idx, slide in enumerate(prs.slides, start=1):
            slide_title = None
            slide_texts: List[str] = []

            # Check for slide title shape
            if slide.shapes.title and slide.shapes.title.has_text_frame:
                title_text = slide.shapes.title.text_frame.text.strip()
                if title_text:
                    slide_title = title_text

            for shape in slide.shapes:
                if shape != slide.shapes.title and shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        p_text = paragraph.text.strip()
                        if p_text:
                            slide_texts.append(p_text)

            # Slide notes if present
            notes_text = ""
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes_text = slide.notes_slide.notes_text_frame.text.strip()

            combined_parts = []
            if slide_title:
                combined_parts.append(f"## {slide_title}")
                sections.append(
                    DocumentSection(
                        title=slide_title,
                        level=1,
                        start_page=idx,
                    )
                )
            if slide_texts:
                combined_parts.append("\n".join(slide_texts))
            if notes_text:
                combined_parts.append(f"[Speaker Notes: {notes_text}]")

            clean_slide_text = cls._clean_text("\n\n".join(combined_parts))
            pages.append(
                DocumentPage(
                    page_number=idx,
                    slide_number=idx,
                    text=clean_slide_text,
                    section_title=slide_title,
                    metadata={"has_notes": bool(notes_text)},
                )
            )
            if clean_slide_text:
                full_text_parts.append(clean_slide_text)

        if not pages:
            pages.append(DocumentPage(page_number=1, slide_number=1, text=""))

        raw_text = "\n\n".join(full_text_parts)
        return ParsedDocument(
            filename=filename,
            file_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            total_pages=len(pages),
            sections=sections,
            pages=pages,
            raw_text=raw_text,
            word_count=len(raw_text.split()),
            metadata={"parser": "python-pptx"},
        )

    # --------------------------------------------------------------------------
    # TXT / Markdown Parsing
    # --------------------------------------------------------------------------

    @classmethod
    def _parse_text(cls, data: bytes, filename: str) -> ParsedDocument:
        """Extract text and markdown headers from TXT and MD files."""
        text = ""
        for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                text = data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        text = cls._clean_text(text)
        sections: List[DocumentSection] = []

        # Find Markdown headers
        for match in cls.MD_HEADING_REGEX.finditer(text):
            hashes, title = match.groups()
            sections.append(
                DocumentSection(
                    title=title.strip(),
                    level=len(hashes),
                    start_page=1,
                )
            )

        # Approximate pages (~500 words per page)
        words = text.split()
        total_words = len(words)
        page_word_limit = 500
        pages: List[DocumentPage] = []

        if total_words <= page_word_limit:
            pages.append(
                DocumentPage(
                    page_number=1,
                    text=text,
                    section_title=sections[0].title if sections else "Main Content",
                )
            )
        else:
            current_page_idx = 1
            for i in range(0, total_words, page_word_limit):
                chunk_words = words[i : i + page_word_limit]
                page_text = " ".join(chunk_words)
                pages.append(
                    DocumentPage(
                        page_number=current_page_idx,
                        text=page_text,
                        section_title=sections[0].title if sections else "Main Content",
                    )
                )
                current_page_idx += 1

        return ParsedDocument(
            filename=filename,
            file_type="text/markdown" if filename.endswith((".md", ".markdown")) else "text/plain",
            total_pages=len(pages),
            sections=sections,
            pages=pages,
            raw_text=text,
            word_count=total_words,
            metadata={"parser": "text/markdown"},
        )

    # --------------------------------------------------------------------------
    # Helper Utilities
    # --------------------------------------------------------------------------

    @classmethod
    def _clean_text(cls, text: str) -> str:
        """Normalize whitespace, unicode codepoints, and remove control characters."""
        if not text:
            return ""
        # Normalize unicode
        text = unicodedata.normalize("NFKC", text)
        # Remove null bytes and non-printable control chars
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Normalize carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse multiple empty lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @classmethod
    def _detect_page_heading(cls, text: str) -> Optional[str]:
        """Detect potential heading or title in page header lines."""
        if not text:
            return None
        lines = [line.strip() for line in text.split("\n") if line.strip()][:5]
        for line in lines:
            if cls.HEADING_REGEX.match(line):
                return line
        return None
