"""Errors raised by the extractor.

Every one of these exists so that a bad input stops the run instead of
producing a number that looks plausible. A wrong invoice total is far more
expensive than a failed import, because nobody goes looking for it.
"""


class ExtractionError(Exception):
    """Base class - catch this to catch everything from this package."""


class AmbiguousAmountError(ExtractionError):
    """The text could be read as more than one number.

    "1.234" is 1234 under German conventions and 1.234 under English ones.
    Without a stated locale there is no honest way to choose, so we refuse.
    """


class UnknownDateFormatError(ExtractionError):
    """None of the accepted date formats matched.

    Deliberately not solved by handing the string to a permissive parser:
    "03/08/2026" is the 3rd of August in Europe and the 8th of March in the
    US, and a parser that guesses will silently pick one.
    """


class UnknownLayoutError(ExtractionError):
    """No adapter recognised the document.

    A parser that falls back to "find something that looks like a total"
    will eventually find the wrong thing. Each supplier layout gets an
    explicit adapter, and an unknown layout is reported, not approximated.
    """


class MissingFieldError(ExtractionError):
    """A required field is absent from a document the adapter did match.

    This usually means the layout changed. It is a defect in the adapter,
    not a data problem, and it should be visible immediately.
    """
