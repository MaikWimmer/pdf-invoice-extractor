"""Command line entry point.

    python -m invoice_extractor <folder> [output.xlsx] [--keep-going]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import ExtractionError
from .excel import write_workbook
from .reader import extract_folder


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="invoice_extractor",
        description="Turn a folder of invoice PDFs into an Excel workbook.",
    )
    parser.add_argument("folder", type=Path, help="folder containing the PDFs")
    parser.add_argument("output", type=Path, nargs="?", default=Path("invoices.xlsx"),
                        help="workbook to write (default: invoices.xlsx)")
    parser.add_argument("--keep-going", action="store_true",
                        help="process every file and report all failures at "
                             "the end, instead of stopping at the first one")
    args = parser.parse_args(argv)

    try:
        invoices = list(extract_folder(args.folder, keep_going=args.keep_going))
    except ExtractionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not invoices:
        print(f"no PDFs found in {args.folder}", file=sys.stderr)
        return 1

    target = write_workbook(invoices, args.output)
    items = sum(len(invoice.items) for invoice in invoices)
    total = sum(invoice.gross for invoice in invoices)
    print(f"{len(invoices)} invoices, {items} line items -> {target}")
    print(f"total gross: {total:,.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
