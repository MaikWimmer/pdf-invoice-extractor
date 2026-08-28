"""Parsing of the two field types that cause almost all real-world damage:
amounts and dates.

Both functions follow the same rule: convert what is unambiguous, refuse
what is not. Neither of them ever falls back to a permissive parser.
"""
from __future__ import annotations

import datetime as _dt
import re

from .errors import AmbiguousAmountError, UnknownDateFormatError

# currency symbols and codes that may sit next to the number
_CURRENCY = re.compile(r"(?:EUR|USD|CHF|GBP|[€$£])", re.IGNORECASE)
_ALLOWED = re.compile(r"^-?[\d.,\s]+$")

# Well-formed shapes per convention. Checking these is what stops "1.2.3"
# from quietly becoming 123 once the separators are stripped out.
_SHAPES = {
    "de": re.compile(r"^\d{1,3}(?:\.\d{3})*(?:,\d+)?$|^\d+(?:,\d+)?$"),
    "en": re.compile(r"^\d{1,3}(?:,\d{3})*(?:\.\d+)?$|^\d+(?:\.\d+)?$"),
}

#: Formats tried by :func:`parse_date`, in order. Day-first only - see the
#: docstring for why there is no month-first format in the default list.
DEFAULT_DATE_FORMATS = ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")


def parse_amount(text: str, locale: str = "de") -> float:
    """Turn an amount as printed on an invoice into a float.

    :param locale:
        ``"de"``   - ``1.234,56``  (dot groups thousands, comma is decimal)
        ``"en"``   - ``1,234.56``  (comma groups thousands, dot is decimal)
        ``"auto"`` - infer, and raise :class:`AmbiguousAmountError` when the
        text supports more than one reading.

    >>> parse_amount("1.234,56 EUR")
    1234.56
    >>> parse_amount("1,234.56", locale="en")
    1234.56
    >>> parse_amount("-83,50")
    -83.5
    """
    if text is None:
        raise AmbiguousAmountError("amount is None")

    cleaned = _CURRENCY.sub("", str(text)).strip()
    cleaned = cleaned.replace("\xa0", "").replace(" ", "")
    if not cleaned or not _ALLOWED.match(cleaned):
        raise AmbiguousAmountError(f"not a readable amount: {text!r}")

    negative = cleaned.startswith("-")
    digits = cleaned.lstrip("-")

    if locale in _SHAPES:
        if not _SHAPES[locale].match(digits):
            raise AmbiguousAmountError(
                f"{text!r} is not a well-formed {locale} amount"
            )
        normalised = (digits.replace(".", "").replace(",", ".")
                      if locale == "de" else digits.replace(",", ""))
    elif locale == "auto":
        normalised = _infer(digits, text)
    else:
        raise ValueError(f"unknown locale: {locale!r}")

    try:
        value = float(normalised)
    except ValueError:
        raise AmbiguousAmountError(f"not a readable amount: {text!r}") from None
    return -value if negative else value


def _infer(digits: str, original: str) -> str:
    """Decide between the two conventions, or refuse to."""
    has_dot, has_comma = "." in digits, "," in digits

    if has_dot and has_comma:
        # both present: whichever comes last is the decimal separator
        if digits.rfind(",") > digits.rfind("."):
            return digits.replace(".", "").replace(",", ".")
        return digits.replace(",", "")

    if not has_dot and not has_comma:
        return digits

    separator = "." if has_dot else ","
    groups = digits.split(separator)

    # More than one separator can only be thousands grouping: 1.234.567 -
    # but only if every group after the first really is three digits.
    if len(groups) > 2:
        if any(len(g) != 3 for g in groups[1:]) or not groups[0]:
            raise AmbiguousAmountError(f"{original!r} is not a well-formed amount")
        return digits.replace(separator, "")

    tail = groups[1]
    # Exactly three trailing digits is the classic ambiguity: "1.234" is
    # 1234 in German and 1.234 in English. Refuse rather than pick.
    if len(tail) == 3:
        raise AmbiguousAmountError(
            f"{original!r} reads as {''.join(groups)} or "
            f"{groups[0]}.{tail} - pass locale='de' or locale='en'"
        )
    return digits.replace(separator, ".")


def parse_date(text: str, formats=DEFAULT_DATE_FORMATS) -> _dt.date:
    """Parse a date using an explicit list of formats, in order.

    The default list is deliberately day-first and contains no month-first
    format. ``"03/08/2026"`` is the 3rd of August under every format in the
    list; adding ``"%m/%d/%Y"`` would make the same string parse as the 8th
    of March depending on position in the list, and nothing in the document
    would reveal which reading was used.

    If a source really is month-first, pass its format explicitly:

    >>> parse_date("03/08/2026", formats=("%m/%d/%Y",))
    datetime.date(2026, 3, 8)
    """
    if text is None:
        raise UnknownDateFormatError("date is None")

    candidate = str(text).strip()
    if not candidate:
        raise UnknownDateFormatError("date is empty")

    for fmt in formats:
        try:
            return _dt.datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue

    raise UnknownDateFormatError(
        f"{candidate!r} matches none of {list(formats)}"
    )
