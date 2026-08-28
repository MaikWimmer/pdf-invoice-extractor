# pdf-invoice-extractor

Turns a folder of invoice PDFs into a structured Excel workbook — and refuses
to guess when a document is ambiguous.

```
$ python -m invoice_extractor examples/pdfs demo.xlsx
3 invoices, 8 line items -> demo.xlsx
total gross: 2,370.24
```

Two sheets come out: one row per invoice for accounting, one row per line item
for anyone who has to ask what was actually bought, joined by invoice number.

---

## The idea

Extracting invoices is easy to do badly. A parser that searches the page for
something total-shaped works on the twenty documents you tested it with and
returns a wrong number on the twenty-first. Nobody notices, because a wrong
total looks exactly like a right one.

So this package never guesses. Three rules:

**One adapter per layout.** No generic "find the total" fallback. Each supplier
format gets a class that knows where its fields are. An unrecognised document
raises `UnknownLayoutError` instead of being approximated.

**Amounts are parsed against a stated convention.** `1.234` is 1234 in German
and 1.234 in English — a factor of a thousand apart, and both look perfectly
normal in a spreadsheet. With `locale="auto"`, that string raises
`AmbiguousAmountError` rather than picking one.

**Dates are parsed against an explicit format list, day-first only.**
`03/08/2026` is the 3rd of August under every default format. A month-first
source is supported, but you have to say so — the choice stays visible in the
code instead of hiding in a heuristic.

Everything that cannot be read stops the run. A failed import is cheap; a
wrong number that reaches a booking system is not.

---

## Tests

`pytest` — 62 tests, no PDF files, under a tenth of a second.

That last part is deliberate. The adapters work on a `PdfContent` object
(text plus tables), so a test builds a page by hand. Simulating a supplier who
moved a field is three lines, and the suite runs on a machine with no sample
documents.

The tests worth reading are the ones about things going wrong:

| File | What it pins down |
|---|---|
| `tests/test_dates.py` | A real defect: a permissive parser read `03/08/2026` as the 8th of March instead of the 3rd of August and moved five months of invoices into the wrong quarter. Nothing crashed. The tests here make that reading impossible to reintroduce. |
| `tests/test_amounts.py` | The thousands-separator ambiguity, non-breaking spaces from PDF extraction, and a set of malformed inputs that must raise rather than come back as `0.0`. |
| `tests/test_adapters.py` | Unknown layouts, and — more important — layouts that still *match* but lost a field, which is how a supplier's template change turns into a hole in the data. |

The amount shape check exists because of one of these tests: `1.2.3` was
happily read as `123` once the separators were stripped, and the test caught it
before the code was ever used on anything.

---

## Adding a supplier

Write a class with `matches` and `parse`, and append it to `ADAPTERS`:

```python
class AcmeAdapter(InvoiceAdapter):
    name = "acme"

    def matches(self, content: PdfContent) -> bool:
        return "ACME Corp" in content.text

    def parse(self, content: PdfContent) -> Invoice:
        ...
```

Adapters are tried in order and the first match wins, so the ordering is
explicit rather than emergent.

---

## Install and run

```bash
pip install -e ".[dev]"          # pdfplumber, openpyxl, pytest
pytest                           # run the suite

pip install fpdf2                # only needed for the sample generator
python examples/make_sample_invoices.py
python -m invoice_extractor examples/pdfs demo.xlsx
```

Python 3.9 or newer.

By default the extractor stops at the first document it cannot read. Pass
`--keep-going` when triaging an unfamiliar batch: every file is attempted and
the failures are reported together, which reads as a to-do list of adapters to
write.

---

## About this repository

A work sample by [Maik Wimmer](https://www.linkedin.com/in/maik-wimmer-166b2039a/),
who builds data extraction and reporting automation — Python, Power Automate,
Power BI, Excel.

The sample invoices are fictional. No client data appears anywhere in this
repository.

No licence is granted: the code is published to be read, not reused.
