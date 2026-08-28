"""Generate three fictional invoice PDFs so the command line demo has input.

The data is obviously made up - no real company, customer or amount appears
anywhere in this repository.

    pip install fpdf2
    python examples/make_sample_invoices.py
    python -m invoice_extractor examples/pdfs demo.xlsx
"""
from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).parent / "pdfs"

INVOICES = [
    {
        "number": "2026-0341", "date": "02.06.2026",
        "customer": "Muster Handels GmbH",
        "items": [("Wartungsvertrag Juni", 1, 249.00),
                  ("Ersatzteil-Set A", 2, 89.50),
                  ("Anfahrtspauschale", 1, 45.00)],
    },
    {
        "number": "2026-0342", "date": "11.06.2026",
        "customer": "Beispiel & Soehne KG",
        "items": [("Montage-Service", 1, 480.00),
                  ("Kleinmaterial", 1, 32.80)],
    },
    {
        "number": "2026-0343", "date": "24.06.2026",
        "customer": "Demo Logistik AG",
        "items": [("Schulung Lagerverwaltung", 1, 350.00),
                  ("Software-Lizenz (Jahr)", 3, 199.00),
                  ("Support-Paket S", 1, 59.00)],
    },
]

VAT_RATE = 0.19


def german(value: float) -> str:
    """1234.5 -> '1.234,50'"""
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build(invoice: dict) -> Path:
    net = sum(quantity * price for _, quantity, price in invoice["items"])
    vat = round(net * VAT_RATE, 2)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "MUSTERFIRMA Technik GmbH", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Beispielweg 1, 12345 Musterstadt - FICTIONAL DEMO INVOICE",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("Helvetica", "", 11)
    for line in (f"Rechnung Nr. {invoice['number']}",
                 f"Rechnungsdatum: {invoice['date']}",
                 f"Kunde: {invoice['customer']}"):
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    widths = (90, 20, 35, 35)
    pdf.set_font("Helvetica", "B", 10)
    for header, width in zip(("Position", "Menge", "Einzelpreis", "Summe"), widths):
        pdf.cell(width, 7, header, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    for description, quantity, price in invoice["items"]:
        for value, width in zip(
            (description, str(quantity), german(price), german(quantity * price)),
            widths,
        ):
            pdf.cell(width, 7, value, border=1)
        pdf.ln()

    pdf.set_font("Helvetica", "B", 10)
    for label, amount in (("Gesamtbetrag netto", net),
                          ("zzgl. 19% MwSt.", vat),
                          ("Rechnungsbetrag", net + vat)):
        pdf.cell(widths[0] + widths[1] + widths[2], 7, label, border=1)
        pdf.cell(widths[3], 7, german(amount), border=1)
        pdf.ln()

    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / f"rechnung_{invoice['number']}.pdf"
    pdf.output(str(target))
    return target


if __name__ == "__main__":
    for entry in INVOICES:
        print("wrote", build(entry))
