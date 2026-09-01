"""The only module that knows about PDFs.

Everything else works on :class:`PdfContent`, which is why the parsing and
adapter tests need no PDF files and run in milliseconds.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

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


def extract_folder(folder: Path, keep_going: bool = False) -> Tuple[List[Invoice], List[str]]:
    """Extract every PDF in a folder.

    Returns the invoices that could be read and a list of failure messages.

    ``keep_going=False`` (the default) stops at the first bad document. That
    is the right default for a batch you are about to book: half an import is
    worse than none.

    ``keep_going=True`` processes everything it can and hands back both lists,
    so the good documents still reach the caller and the failures read as a
    to-do list of adapters to write. Losing the good ones alongside the bad
    would defeat the point of the flag.
    """
    invoices: List[Invoice] = []
    failures: List[str] = []

    for pdf in sorted(Path(folder).glob("*.pdf")):
        try:
            invoices.append(extract_invoice(pdf))
        except ExtractionError as exc:
            if not keep_going:
                raise
            failures.append(str(exc))

    return invoices, failures
