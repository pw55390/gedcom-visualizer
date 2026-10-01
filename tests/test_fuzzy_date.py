"""
Unit tests for FuzzyDate engine, GEDCOM date parser, JDN conversion, and age calculation.
"""

import pytest
from src.core.enums import DateModifier
from src.core.fuzzy_date import FuzzyDate, gregorian_to_jdn, jdn_to_gregorian


def test_jdn_roundtrip():
    year, month, day = 1920, 1, 15
    jdn = gregorian_to_jdn(year, month, day)
    y, m, d = jdn_to_gregorian(jdn)
    assert (y, m, d) == (year, month, day)


def test_parse_exact_date():
    fd = FuzzyDate.parse("15 JAN 1920")
    assert fd.modifier == DateModifier.EXACT
    assert fd.year == 1920
    assert fd.month == 1
    assert fd.day == 15
    assert fd.to_display_string("PL") == "15 stycznia 1920 r."


def test_parse_dot_date():
    fd = FuzzyDate.parse("15.01.1920")
    assert fd.modifier == DateModifier.EXACT
    assert fd.year == 1920
    assert fd.month == 1
    assert fd.day == 15


def test_parse_about_date():
    fd = FuzzyDate.parse("ABT 1850")
    assert fd.modifier == DateModifier.ABOUT
    assert fd.year == 1850
    assert fd.to_display_string("PL") == "ok. 1850 r."
    # JDN bounds should span 1845 to 1855
    jdn_1845 = gregorian_to_jdn(1845, 1, 1)
    jdn_1855 = gregorian_to_jdn(1855, 12, 31)
    assert fd.jdn_min == jdn_1845
    assert fd.jdn_max == jdn_1855


def test_parse_between_date():
    fd = FuzzyDate.parse("BET 1910 AND 1920")
    assert fd.modifier == DateModifier.BETWEEN
    assert fd.year == 1910
    assert fd.year_end == 1920
    assert "1910" in fd.to_display_string("PL")
    assert "1920" in fd.to_display_string("PL")


def test_age_calculation():
    birth = FuzzyDate.parse("15 JAN 1920")
    death = FuzzyDate.parse("20 FEB 2000")
    age = birth.calculate_age_at(death)
    assert age == 80

    death_before_birthday = FuzzyDate.parse("10 JAN 2000")
    age2 = birth.calculate_age_at(death_before_birthday)
    assert age2 == 79
