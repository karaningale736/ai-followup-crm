from datetime import date
from app.core.workdays import working_days_between, add_working_days, is_working_day


def test_friday_to_monday_is_one_working_day():
    friday = date(2026, 8, 14)  # Friday
    monday = date(2026, 8, 17)  # Monday
    assert working_days_between(friday, monday) == 1


def test_same_day_is_zero_working_days():
    d = date(2026, 8, 10)
    assert working_days_between(d, d) == 0


def test_weekend_is_not_a_working_day():
    saturday = date(2026, 8, 15)
    assert is_working_day(saturday) is False


def test_holiday_excluded_from_working_days():
    monday = date(2026, 8, 10)
    wednesday = date(2026, 8, 12)
    holidays = {date(2026, 8, 11)}  # Tuesday off
    assert working_days_between(monday, wednesday, holidays) == 1


def test_add_working_days_skips_weekend():
    friday = date(2026, 8, 14)
    result = add_working_days(friday, 1)
    assert result == date(2026, 8, 17)  # Monday


def test_add_working_days_multiple():
    monday = date(2026, 8, 10)
    result = add_working_days(monday, 5)
    assert result == date(2026, 8, 17)  # next Monday (5 working days later)
