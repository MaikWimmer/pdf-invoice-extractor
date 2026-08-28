"""Date parsing.

This file exists because of a real defect. An earlier version of this code
handed date strings to a permissive parser. It read the German
``03/08/2026`` as the 8th of March instead of the 3rd of August, which moved
five months of invoices into the wrong quarter. Nothing crashed, nothing
looked odd, and it was only found by someone comparing a monthly total
against a printout.

The tests below pin down the behaviour that prevents it.
"""
import datetime as dt

import pytest

from invoice_extractor import DEFAULT_DATE_FORMATS, UnknownDateFormatError, parse_date


class TestAcceptedFormats:
    @pytest.mark.parametrize("text, expected", [
        ("02.06.2026", dt.date(2026, 6, 2)),
        ("2026-06-02", dt.date(2026, 6, 2)),
        ("02/06/2026", dt.date(2026, 6, 2)),
        ("02-06-2026", dt.date(2026, 6, 2)),
    ])
    def test_the_four_default_formats(self, text, expected):
        assert parse_date(text) == expected

    def test_whitespace_around_the_value_is_tolerated(self):
        assert parse_date("  02.06.2026 ") == dt.date(2026, 6, 2)


class TestTheDefectThisFilePrevents:
    def test_slash_dates_are_read_day_first(self):
        """``03/08/2026`` is the 3rd of August, not the 8th of March."""
        assert parse_date("03/08/2026") == dt.date(2026, 8, 3)

    def test_no_default_format_is_month_first(self):
        """A month-first format in the default list would make the result
        depend on list order rather than on the document."""
        assert not any("%m/%d" in fmt or "%m.%d" in fmt
                       for fmt in DEFAULT_DATE_FORMATS)

    def test_month_first_sources_must_say_so_explicitly(self):
        """Month-first input is supported - but only when stated, so the
        choice is visible in the code and not hidden in a heuristic."""
        assert parse_date("03/08/2026", formats=("%m/%d/%Y",)) == dt.date(2026, 3, 8)

    def test_the_two_readings_really_do_differ(self):
        """Guard against the test above passing for the wrong reason."""
        day_first = parse_date("03/08/2026")
        month_first = parse_date("03/08/2026", formats=("%m/%d/%Y",))
        assert day_first != month_first


class TestRejects:
    @pytest.mark.parametrize("text", [
        "32.01.2026",        # no such day
        "2026-13-01",        # no such month
        "01.06.26",          # two-digit year is not in the default list
        "June 2nd, 2026",
        "",
        "   ",
        None,
    ])
    def test_raises_instead_of_returning_today(self, text):
        with pytest.raises(UnknownDateFormatError):
            parse_date(text)

    def test_the_error_names_the_formats_that_were_tried(self):
        """So whoever reads the log knows what to add."""
        with pytest.raises(UnknownDateFormatError) as caught:
            parse_date("01.06.26")
        assert "%d.%m.%Y" in str(caught.value)
