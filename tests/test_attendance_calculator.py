"""
attendance_calculator.py のテスト
"""

import pytest
from attendance_calculator import (
    AttendanceInput,
    InvalidTimeError,
    calc_absent_shortage,
    calc_excess_overtime,
    calculate,
    generate_comment,
    minutes_to_hhmm,
    parse_days,
    parse_time_to_minutes,
)


# ------------------------------------------------------------------
# parse_time_to_minutes
# ------------------------------------------------------------------

class TestParseTimeToMinutes:
    def test_integer_string(self):
        assert parse_time_to_minutes("2") == 120

    def test_hhmm_format(self):
        assert parse_time_to_minutes("2:30") == 150

    def test_over_24h(self):
        assert parse_time_to_minutes("26:00") == 1560

    def test_zero(self):
        assert parse_time_to_minutes("0") == 0

    def test_zero_colon(self):
        assert parse_time_to_minutes("0:00") == 0

    def test_empty_string(self):
        assert parse_time_to_minutes("") == 0

    def test_fractional_hour_not_supported(self):
        with pytest.raises(InvalidTimeError):
            parse_time_to_minutes("1.5")

    def test_negative_value(self):
        with pytest.raises(InvalidTimeError):
            parse_time_to_minutes("-1")

    def test_invalid_minutes(self):
        with pytest.raises(InvalidTimeError):
            parse_time_to_minutes("1:60")

    def test_invalid_format_letters(self):
        with pytest.raises(InvalidTimeError):
            parse_time_to_minutes("abc")

    def test_too_many_colons(self):
        with pytest.raises(InvalidTimeError):
            parse_time_to_minutes("1:30:00")


# ------------------------------------------------------------------
# minutes_to_hhmm
# ------------------------------------------------------------------

class TestMinutesToHHMM:
    def test_zero(self):
        assert minutes_to_hhmm(0) == "0:00"

    def test_60_minutes(self):
        assert minutes_to_hhmm(60) == "1:00"

    def test_90_minutes(self):
        assert minutes_to_hhmm(90) == "1:30"

    def test_over_24h(self):
        assert minutes_to_hhmm(1500) == "25:00"

    def test_negative_returns_zero(self):
        assert minutes_to_hhmm(-10) == "0:00"

    def test_padding(self):
        assert minutes_to_hhmm(65) == "1:05"


# ------------------------------------------------------------------
# parse_days
# ------------------------------------------------------------------

class TestParseDays:
    def test_integer(self):
        assert parse_days("20") == 20.0

    def test_float(self):
        assert parse_days("1.5") == 1.5

    def test_zero(self):
        assert parse_days("0") == 0.0

    def test_empty_string(self):
        assert parse_days("") == 0.0

    def test_negative(self):
        with pytest.raises(InvalidTimeError):
            parse_days("-1")

    def test_non_numeric(self):
        with pytest.raises(InvalidTimeError):
            parse_days("abc")


# ------------------------------------------------------------------
# calc_absent_shortage
# ------------------------------------------------------------------

class TestCalcAbsentShortage:
    def test_no_absence(self):
        assert calc_absent_shortage(0, 480) == 0

    def test_one_day(self):
        assert calc_absent_shortage(1, 480) == 480

    def test_half_day(self):
        assert calc_absent_shortage(0.5, 480) == 240

    def test_fractional_days(self):
        assert calc_absent_shortage(1.5, 480) == 720


# ------------------------------------------------------------------
# 早退時間（parse経由で計算）
# ------------------------------------------------------------------

class TestEarlyLeave:
    def test_no_early_leave(self):
        assert parse_time_to_minutes("0:00") == 0

    def test_30min_early_leave(self):
        assert parse_time_to_minutes("0:30") == 30

    def test_90min_early_leave(self):
        assert parse_time_to_minutes("1:30") == 90


# ------------------------------------------------------------------
# calc_excess_overtime
# ------------------------------------------------------------------

class TestCalcExcessOvertime:
    def test_within_deemed(self):
        assert calc_excess_overtime(1200, 1800) == 0

    def test_exact_deemed(self):
        assert calc_excess_overtime(1800, 1800) == 0

    def test_exceed_deemed(self):
        assert calc_excess_overtime(2400, 1800) == 600

    def test_no_deemed(self):
        assert calc_excess_overtime(600, 0) == 600

    def test_no_overtime(self):
        assert calc_excess_overtime(0, 1800) == 0


# ------------------------------------------------------------------
# calculate（統合）
# ------------------------------------------------------------------

class TestCalculate:
    def test_standard_case(self):
        inputs = AttendanceInput(
            scheduled_work_days=20,
            scheduled_minutes_per_day=480,
            absent_days=1,
            early_leave_minutes=120,
            overtime_minutes=900,
            late_night_minutes=180,
            deemed_overtime_minutes=600,
        )
        result = calculate(inputs)

        assert result.absent_shortage_minutes == 480       # 1日 × 8h
        assert result.early_leave_shortage_minutes == 120  # 2h早退
        assert result.total_shortage_minutes == 600        # 合計10h
        assert result.excess_overtime_minutes == 300       # 15h - 10h みなし
        assert result.late_night_minutes == 180
        assert isinstance(result.comment, str)

    def test_no_absence_no_overtime(self):
        inputs = AttendanceInput(
            scheduled_work_days=20,
            scheduled_minutes_per_day=480,
            absent_days=0,
            early_leave_minutes=0,
            overtime_minutes=0,
            late_night_minutes=0,
            deemed_overtime_minutes=1200,
        )
        result = calculate(inputs)

        assert result.total_shortage_minutes == 0
        assert result.excess_overtime_minutes == 0
        assert "みなし" in result.comment


# ------------------------------------------------------------------
# generate_comment
# ------------------------------------------------------------------

class TestGenerateComment:
    def test_all_zero(self):
        comment = generate_comment(0, 0, 0)
        assert "みなし" in comment

    def test_shortage_appears(self):
        comment = generate_comment(480, 0, 0)
        assert "不足時間" in comment

    def test_excess_overtime_appears(self):
        comment = generate_comment(0, 600, 0)
        assert "超過" in comment

    def test_late_night_appears(self):
        comment = generate_comment(0, 0, 120)
        assert "深夜労働" in comment
