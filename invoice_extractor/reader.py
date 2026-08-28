"""The only module that knows about PDFs.

Everything else works on :class:`PdfContent`, which is why the parsing and
adapter tests need no PDF files and run in milliseconds.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, List

from .errors import ExtractionError
from .model import Invoice, PdfContent
from .adapters import parse_invoice


def read_pdf(path: Path) -> PdfContent:
    """Read text and tables from the first page of a PDF."""
    import pdfplumber  # imported here so the rest of the package stays light

    path = Path(path)
    try:
        with pdfplumber.open(path) as pdf:
            if not pdf.pages:
                raise ExtractionError(f"{path.name}: PDF has no pages")
            page = pdf.pages[0]
            return PdfContent(
                text=page.extract_text() or "",
                tables=page.extract_tables() or [],
                source_name=path.name,
            )
    except ExtractionError:
        raise
    except Exception as exc:  # pdfplumber raises a variety of types
        raise ExtractionError(f"{path.name}: could not be read - {exc}") from exc


def extract_invoice(path: Path) -> Invoice:
    """Read one PDF and turn it into an :class:`Invoice`."""
    return parse_invoice(read_pdf(path))


def extract_folder(folder: Path, keep_going: bool = False) -> Iterator[Invoice]:
    """Extract every PDF in a folder.

    ``keep_going=False`` (the default) stops at the first bad document. That
    is the right default for a batch you are going to book: half an import is
    worse than none. Pass ``True`` when triaging a new set of files, and read
    the errors as a to-do list of adapters to write.
    """
    failures: List[str] = []
    for pdf in sorted(Path(folder).glob("*.pdf")):
        try:
            yield extract_invoice(pdf)
        except ExtractionError as exc:
            if not keep_going:
                raise
            failures.append(str(exc))

    if failures:
        raise ExtractionError(
            f"{len(failures)} document(s) could not be processed:\n  "
            + "\n  ".join(failures)
        )
