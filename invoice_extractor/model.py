"""The shapes the rest of the package passes around."""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import List, Optional, Sequence


@dataclass(frozen=True)
class PdfContent:
    """What a PDF reader hands to an adapter.

    Keeping this separate from the PDF library is what makes the adapters
    testable without a single PDF file: a test builds the text and tables
    by hand and calls the adapter directly.
    """

    text: str
    tables: Sequence[Sequence[Sequence[Optional[str]]]] = ()
    source_name: str = ""


@dataclass(frozen=True)
class LineItem:
    description: str
    quantity: int
    unit_price: float
    total: float


@dataclass(frozen=True)
class Invoice:
    source_file: str
    number: str
    date: _dt.date
    customer: str
    net: float
    vat: float
    gross: float
    items: List[LineItem] = field(default_factory=list)

    def items_total(self) -> float:
        return round(sum(item.total for item in self.items), 2)
