"""Adapter selection and extraction.

Two questions matter here. Does a document that *is* recognised come out
completely and correctly? And does a document that is *not* recognised fail
loudly instead of producing a half-filled row?
"""
import datetime as dt

import pytest

from invoice_extractor import (
    MissingFieldError,
    PdfContent,
    UnknownLayoutError,
    parse_invoice,
)
from invoice_extractor.adapters import MusterfirmaAdapter
from samples import HEADER, TABLE


class TestHappyPath:
    def test_header_fields(self, invoice_content):
        invoice = parse_invoice(invoice_content)
        assert invoice.number == "2026-0341"
        assert invoice.date == dt.date(2026, 6, 2)
        assert invoice.customer == "Muster Handels GmbH"
        assert invoice.source_file == "rechnung_2026-0341.pdf"

    def test_totals(self, invoice_content):
        invoice = parse_invoice(invoice_content)
        assert invoice.net == pytest.approx(473.00)
        assert invoice.vat == pytest.approx(89.87)
        assert invoice.gross == pytest.approx(562.87)

    def test_line_items(self, invoice_content):
        invoice = parse_invoice(invoice_content)
        assert len(invoice.items) == 3
        first = invoice.items[0]
        assert first.description == "Wartungsvertrag Juni"
        assert first.quantity == 1
        assert first.unit_price == pytest.approx(249.00)

    def test_line_items_add_up_to_the_net_total(self, invoice_content):
        """A cross-check the document itself makes possible.

        If this ever fails, either a line was missed or a total was read
        from the wrong cell - both worth knowing before the data is booked.
        """
        invoice = parse_invoice(invoice_content)
        assert invoice.items_total() == pytest.approx(invoice.net)

    def test_totals_are_not_mistaken_for_line_items(self, invoice_content):
        """The summary rows sit in the same table as the items."""
        invoice = parse_invoice(invoice_content)
        descriptions = [item.description for item in invoice.items]
        assert not any(d.startswith(("Gesamtbetrag", "zzgl", "Rechnungsbetrag"))
                       for d in descriptions)


class TestUnknownLayout:
    def test_unrecognised_document_raises(self):
        content = PdfContent(text="ACME Corp\nInvoice 42\n", tables=[],
                             source_name="acme.pdf")
        with pytest.raises(UnknownLayoutError) as caught:
            parse_invoice(content)
        assert "acme.pdf" in str(caught.value)

    def test_the_error_lists_the_layouts_that_are_known(self):
        """So the reader knows which adapter is missing, not just that one is."""
        with pytest.raises(UnknownLayoutError) as caught:
            parse_invoice(PdfContent(text="unknown", source_name="x.pdf"))
        assert "musterfirma" in str(caught.value)

    def test_empty_document_does_not_match_anything(self):
        with pytest.raises(UnknownLayoutError):
            parse_invoice(PdfContent(text="", tables=[], source_name="blank.pdf"))


class TestLayoutChanged:
    """A matched document with a missing field is an adapter defect.

    These are the failures that matter most in production: the supplier
    tweaked their template, the marker still matches, and a naive parser
    keeps going with a hole in the data.
    """

    def test_missing_invoice_number(self, content_factory):
        text = HEADER.replace("Rechnung Nr. 2026-0341\n", "")
        with pytest.raises(MissingFieldError) as caught:
            parse_invoice(content_factory(text=text))
        assert "invoice number" in str(caught.value)

    def test_missing_date(self, content_factory):
        text = HEADER.replace("Rechnungsdatum: 02.06.2026\n", "")
        with pytest.raises(MissingFieldError):
            parse_invoice(content_factory(text=text))

    def test_missing_gross_total(self, content_factory):
        table = [row for row in TABLE if not row[0].startswith("Rechnungsbetrag")]
        with pytest.raises(MissingFieldError) as caught:
            parse_invoice(content_factory(table=table))
        assert "gross total" in str(caught.value)
        assert "2026-0341" in str(caught.value)   # says which invoice

    def test_an_invoice_with_no_line_items_is_still_valid(self, content_factory):
        """Some invoices really are a single lump sum. Totals are required,
        line items are not - the distinction has to be deliberate."""
        table = [row for row in TABLE
                 if row[0].startswith(("Position", "Gesamtbetrag", "zzgl",
                                       "Rechnungsbetrag"))]
        invoice = parse_invoice(content_factory(table=table))
        assert invoice.items == []
        assert invoice.gross == pytest.approx(562.87)


class TestAdapterSelection:
    def test_matching_is_case_insensitive(self):
        adapter = MusterfirmaAdapter()
        assert adapter.matches(PdfContent(text="musterfirma technik gmbh"))

    def test_first_matching_adapter_wins(self):
        """Order in ADAPTERS is the tie-breaker, and it is explicit."""
        calls = []

        class Recording(MusterfirmaAdapter):
            def __init__(self, label):
                self.label = label

            def matches(self, content):
                calls.append(self.label)
                return True

            def parse(self, content):
                return f"parsed by {self.label}"

        result = parse_invoice(PdfContent(text="anything"),
                               adapters=(Recording("a"), Recording("b")))
        assert result == "parsed by a"
        assert calls == ["a"]
