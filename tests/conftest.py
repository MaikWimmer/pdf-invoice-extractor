"""Fixtures.

No PDF is opened anywhere in this test suite. The adapters work on
:class:`PdfContent`, so a test builds the page content by hand. That keeps
the suite fast, makes broken layouts trivial to simulate, and means a
contributor can run the tests without any sample documents.
"""
import pytest

from invoice_extractor import PdfContent
from samples import HEADER, TABLE


@pytest.fixture
def invoice_content():
    """A well-formed invoice in the layout the shipped adapter handles."""
    return PdfContent(text=HEADER, tables=[TABLE],
                      source_name="rechnung_2026-0341.pdf")


@pytest.fixture
def content_factory():
    """Build a variant: drop a line from the header, change a table row.

    Used to simulate the layout changes that break adapters in practice.
    """
    def build(text=HEADER, table=None, name="test.pdf"):
        return PdfContent(text=text,
                          tables=[table if table is not None else TABLE],
                          source_name=name)
    return build
