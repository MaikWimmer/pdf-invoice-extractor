"""Amount parsing.

The interesting cases are not "does it parse 1.234,56" - they are the ones
where a number can be read two ways. Those are the cases that put a wrong
total into a booking system without anyone noticing.
"""
import pytest

from invoice_extractor import AmbiguousAmountError, parse_amount


class TestGerman:
    @pytest.mark.parametrize("text, expected", [
        ("1.234,56", 1234.56),
        ("1.234,56 EUR", 1234.56),
        ("€ 1.234,56", 1234.56),
        ("1.234.567,89", 1234567.89),
        ("12,50", 12.50),
        ("0,00", 0.0),
        ("-83,50", -83.50),
        ("1.234", 1234.0),          # unambiguous once the locale is stated
        ("999", 999.0),
    ])
    def test_reads_german_amounts(self, text, expected):
        assert parse_amount(text) == pytest.approx(expected)

    def test_non_breaking_space_between_number_and_currency(self):
        # PDF extraction hands out U+00A0 far more often than a plain space
        assert parse_amount("1.234,56\xa0EUR") == pytest.approx(1234.56)


class TestEnglish:
    @pytest.mark.parametrize("text, expected", [
        ("1,234.56", 1234.56),
        ("$1,234.56", 1234.56),
        ("1,234,567.89", 1234567.89),
        ("0.00", 0.0),
        ("-83.50", -83.50),
    ])
    def test_reads_english_amounts(self, text, expected):
        assert parse_amount(text, locale="en") == pytest.approx(expected)


class TestAuto:
    """Inference is allowed only where the text can mean one thing."""

    @pytest.mark.parametrize("text, expected", [
        ("1.234,56", 1234.56),      # both separators, comma last -> German
        ("1,234.56", 1234.56),      # both separators, dot last   -> English
        ("1.234.567", 1234567.0),   # two dots can only be grouping
        ("12,50", 12.50),           # two trailing digits -> decimal
        ("999", 999.0),
    ])
    def test_infers_where_it_can(self, text, expected):
        assert parse_amount(text, locale="auto") == pytest.approx(expected)

    @pytest.mark.parametrize("text", ["1.234", "1,234", "12.345", "9,876"])
    def test_refuses_the_classic_ambiguity(self, text):
        """One separator, three digits after it: 1234 or 1.234?

        This is the single most expensive silent bug in invoice parsing.
        A guess is wrong by a factor of a thousand and looks perfectly
        normal in a spreadsheet.
        """
        with pytest.raises(AmbiguousAmountError) as caught:
            parse_amount(text, locale="auto")
        assert "locale=" in str(caught.value)   # the message says how to fix it


class TestRejects:
    @pytest.mark.parametrize("text", ["", "   ", "abc", "12,34,56", None, "1.2.3"])
    def test_raises_instead_of_returning_zero(self, text):
        """Nothing here may come back as 0.0.

        Returning a default for unreadable input is how a missing amount
        turns into a booked amount of nothing.
        """
        with pytest.raises(AmbiguousAmountError):
            parse_amount(text)

    def test_unknown_locale_is_a_programming_error(self):
        with pytest.raises(ValueError):
            parse_amount("1,00", locale="fr")
