"""One adapter per document layout.

There is deliberately no generic "find the total somewhere on the page"
fallback. A generic parser works on the documents you tested it with and
quietly returns the wrong number on the one you did not. Each supplier gets
an adapter that knows where its fields are; an unrecognised layout raises
:class:`UnknownLayoutError`.

Adding a supplier means writing a class with ``matches`` and ``parse`` and
appending it to :data:`ADAPTERS`.
"""
from __future__ import annotations

import re
from typing import List, Optional, Sequence

from .errors import MissingFieldError, UnknownLayoutError
from .model import Invoice, LineItem, PdfContent
from .parsing import parse_amount, parse_date


class InvoiceAdapter:
    """Interface every adapter implements."""

    name = "abstract"

    def matches(self, content: PdfContent) -> bool:  # pragma: no cover
        raise NotImplementedError

    def parse(self, content: PdfContent) -> Invoice:  # pragma: no cover
        raise NotImplementedError


def _require(match: Optional[re.Match], field: str, source: str, layout: str) -> str:
    """Fail with the document named.

    An error that says which adapter complained is useless when you are
    looking at four hundred files. It has to say which document.
    """
    if match is None:
        raise MissingFieldError(
            f"{source}: no {field} found - the {layout} layout probably changed"
        )
    return match.group(1).strip()


class MusterfirmaAdapter(InvoiceAdapter):
    """German service invoices: header block plus one line-item table.

    Amounts are German (``1.234,56``), dates are ``dd.mm.yyyy``. Both are
    stated here rather than guessed per document, because a single supplier
    does not change convention between invoices - and if it does, that is a
    new layout and deserves a new adapter.
    """

    name = "musterfirma"
    marker = "MUSTERFIRMA"

    number_re = re.compile(r"Rechnung Nr\.\s*(\S+)")
    date_re = re.compile(r"Rechnungsdatum:\s*(\S+)")
    customer_re = re.compile(r"Kunde:\s*(.+)")

    def matches(self, content: PdfContent) -> bool:
        return self.marker.lower() in content.text.lower()

    def parse(self, content: PdfContent) -> Invoice:
        text = content.text
        source = content.source_name or "document"
        number = _require(self.number_re.search(text), "invoice number", source, self.name)
        date_text = _require(self.date_re.search(text), "invoice date", source, self.name)
        customer = _require(self.customer_re.search(text), "customer", source, self.name)

        items: List[LineItem] = []
        net = vat = gross = None

        for table in content.tables:
            for row in table:
                cells = [(c or "").strip() for c in row]
                if not cells or not cells[0] or cells[0] == "Position":
                    continue

                head = cells[0]
                if head.startswith("Gesamtbetrag"):
                    net = parse_amount(cells[-1])
                elif head.startswith("zzgl"):
                    vat = parse_amount(cells[-1])
                elif head.startswith("Rechnungsbetrag"):
                    gross = parse_amount(cells[-1])
                elif len(cells) >= 4 and cells[1]:
                    items.append(LineItem(
                        description=head,
                        quantity=int(cells[1]),
                        unit_price=parse_amount(cells[2]),
                        total=parse_amount(cells[3]),
                    ))

        for value, label in ((net, "net total"), (vat, "VAT"), (gross, "gross total")):
            if value is None:
                raise MissingFieldError(
                    f"{source}: no {label} found in invoice {number}"
                )

        return Invoice(
            source_file=content.source_name,
            number=number,
            date=parse_date(date_text),
            customer=customer,
            net=net,
            vat=vat,
            gross=gross,
            items=items,
        )


#: Adapters are tried in order; the first match wins.
ADAPTERS: Sequence[InvoiceAdapter] = (MusterfirmaAdapter(),)


def parse_invoice(content: PdfContent, adapters: Sequence[InvoiceAdapter] = ADAPTERS) -> Invoice:
    """Pick the adapter for this document and run it.

    Raises :class:`UnknownLayoutError` when nothing matches, rather than
    handing the document to a best-effort parser.
    """
    for adapter in adapters:
        if adapter.matches(content):
            return adapter.parse(content)

    known = ", ".join(a.name for a in adapters) or "none registered"
    raise UnknownLayoutError(
        f"{content.source_name or 'document'}: no adapter matched "
        f"(known layouts: {known})"
    )
