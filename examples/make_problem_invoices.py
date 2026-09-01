"""Generate two deliberately broken invoices, so the failure paths can be run.

These are the two failure modes that actually occur in practice:

1. An unknown supplier - no adapter exists for the layout.
2. A known supplier whose template changed - the marker still matches, but a
   required field is gone.

The second is the dangerous one. A parser without a required-field check keeps
going and produces a row with a hole in it that nobody notices.

    pip install fpdf2
    python examples/make_problem_invoices.py
    python -m invoice_extractor examples/pdfs out.xlsx --keep-going
"""
from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).parent / "pdfs"
VAT_RATE = 0.19


def german(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build(filename: str, company: str, header_lines, items) -> Path:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, company, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "FICTIONAL DEMO INVOICE", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("Helvetica", "", 11)
    for line in header_lines:
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    widths = (90, 20, 35, 35)
    pdf.set_font("Helvetica", "B", 10)
    for header, width in zip(("Position", "Menge", "Einzelpreis", "Summe"), widths):
        pdf.cell(width, 7, header, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    net = 0.0
    for description, quantity, price in items:
        net += quantity * price
        for value, width in zip(
            (description, str(quantity), german(price), german(quantity * price)),
            widths,
        ):
            pdf.cell(width, 7, value, border=1)
        pdf.ln()

    vat = round(net * VAT_RATE, 2)
    pdf.set_font("Helvetica", "B", 10)
    for label, amount in (("Gesamtbetrag netto", net),
                          ("zzgl. 19% MwSt.", vat),
                          ("Rechnungsbetrag", net + vat)):
        pdf.cell(widths[0] + widths[1] + widths[2], 7, label, border=1)
        pdf.cell(widths[3], 7, german(amount), border=1)
        pdf.ln()

    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / filename
    pdf.output(str(target))
    return target


if __name__ == "__main__":
    # 1. Unknown supplier - no adapter matches, so the document is reported
    #    rather than approximated.
    print("wrote", build(
        "unknown_supplier_ACME.pdf",
        "ACME Supplies Ltd.",
        ["Invoice No. 2026-77", "Date: 15.06.2026", "Customer: Nordwind AG"],
        [("Consulting hours", 4, 120.00)],
    ))

    # 2. Known layout, but the invoice number is missing. The marker still
    #    matches, so only a required-field check catches this one.
    print("wrote", build(
        "changed_template_no_number.pdf",
        "MUSTERFIRMA Technik GmbH",
        ["Rechnungsdatum: 28.06.2026", "Kunde: Luecken GmbH"],
        [("Reparatur Foerderband", 1, 310.00)],
    ))
