from app.utils.date_parsing import parse_localized_datetime


def test_parse_spanish_hour_without_minutes():
    parsed = parse_localized_datetime("Viernes 17 abril 19 h", ["es"])
    assert parsed is not None
    assert parsed.year == 2026
    assert parsed.month == 4
    assert parsed.day == 17
    assert parsed.hour == 19
    assert parsed.minute == 0


def test_parse_multi_day_spanish_range_uses_first_occurrence():
    parsed = parse_localized_datetime("15 y 16 de abril a las 20:00 horas", ["es"])
    assert parsed is not None
    assert parsed.year == 2026
    assert parsed.month == 4
    assert parsed.day == 15
    assert parsed.hour == 20
    assert parsed.minute == 0
