"""
勤怠計算ロジック

注意: このツールは勤怠時間の目安計算を行うものです。
法律上の正確な給与計算ツールではありません。
"""

from dataclasses import dataclass


class InvalidTimeError(ValueError):
    """不正な時間入力に対する例外"""
    pass


def parse_time_to_minutes(time_str: str) -> int:
    """
    時間文字列を分に変換する。

    対応フォーマット:
        "2"     → 120
        "2:30"  → 150
        "26:00" → 1560

    Raises:
        InvalidTimeError: フォーマットが不正または負の値の場合
    """
    s = str(time_str).strip()
    if not s:
        return 0

    if ":" in s:
        parts = s.split(":")
        if len(parts) != 2:
            raise InvalidTimeError(f"時間は「2:30」または「2」の形式で入力してください（入力値: '{time_str}'）")
        h_str, m_str = parts
        if not h_str.lstrip("-").isdigit() or not m_str.isdigit():
            raise InvalidTimeError(f"時間は「2:30」または「2」の形式で入力してください（入力値: '{time_str}'）")
        hours = int(h_str)
        minutes = int(m_str)
        if minutes < 0 or minutes >= 60:
            raise InvalidTimeError(f"分は 0〜59 の範囲で入力してください（入力値: '{time_str}'）")
        if hours < 0:
            raise InvalidTimeError(f"マイナスの時間は入力できません（入力値: '{time_str}'）")
        return hours * 60 + minutes
    else:
        if not s.lstrip("-").isdigit():
            raise InvalidTimeError(f"時間は「2:30」または「2」の形式で入力してください（入力値: '{time_str}'）")
        hours = int(s)
        if hours < 0:
            raise InvalidTimeError(f"マイナスの時間は入力できません（入力値: '{time_str}'）")
        return hours * 60


def minutes_to_hhmm(total_minutes: int) -> str:
    """
    分をHH:MM形式の文字列に変換する。

    例: 150 → "2:30"、1560 → "26:00"
    """
    if total_minutes < 0:
        total_minutes = 0
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}:{minutes:02d}"


def parse_days(value: str) -> float:
    """
    日数文字列を小数に変換する。

    Raises:
        InvalidTimeError: 不正な値の場合
    """
    s = str(value).strip()
    if not s:
        return 0.0
    try:
        days = float(s)
    except ValueError:
        raise InvalidTimeError(f"日数は半角数字で入力してください（入力値: '{value}'）")
    if days < 0:
        raise InvalidTimeError(f"マイナスの日数は入力できません（入力値: '{value}'）")
    return days


@dataclass
class AttendanceInput:
    """勤怠入力データ（分単位で保持）"""
    scheduled_work_days: float       # 月の所定労働日数
    scheduled_minutes_per_day: int   # 1日の所定労働時間（分）
    absent_days: float               # 欠勤日数
    early_leave_minutes: int         # 早退時間（分）
    overtime_minutes: int            # 普通残業時間（分）
    late_night_minutes: int          # 深夜労働時間（分）
    deemed_overtime_minutes: int     # みなし残業時間（分）


@dataclass
class AttendanceResult:
    """勤怠計算結果（分単位で保持）"""
    absent_shortage_minutes: int     # 欠勤による不足時間（分）
    early_leave_shortage_minutes: int  # 早退による不足時間（分）
    total_shortage_minutes: int      # 不足時間合計（分）
    excess_overtime_minutes: int     # みなし残業超過分（分）
    late_night_minutes: int          # 深夜労働時間（分）
    comment: str                     # 簡易コメント


def calc_absent_shortage(absent_days: float, scheduled_minutes_per_day: int) -> int:
    """欠勤による不足時間（分）を計算する"""
    return int(absent_days * scheduled_minutes_per_day)


def calc_excess_overtime(overtime_minutes: int, deemed_overtime_minutes: int) -> int:
    """みなし残業を超えた固定外残業時間（分）を計算する（マイナスにはならない）"""
    return max(0, overtime_minutes - deemed_overtime_minutes)


def generate_comment(
    total_shortage_minutes: int,
    excess_overtime_minutes: int,
    late_night_minutes: int,
) -> str:
    """勤怠状況に応じた簡易コメントを生成する"""
    parts = []

    if total_shortage_minutes > 0:
        parts.append(
            f"不足時間が{minutes_to_hhmm(total_shortage_minutes)}あります。勤怠状況を確認してください。"
        )

    if excess_overtime_minutes > 0:
        parts.append(f"みなし残業を{minutes_to_hhmm(excess_overtime_minutes)}超過しています。")

    if late_night_minutes > 0:
        parts.append(f"深夜労働が{minutes_to_hhmm(late_night_minutes)}あります。")

    return "\n".join(parts) if parts else "特記事項はありません。"


def calculate(inputs: AttendanceInput) -> AttendanceResult:
    """勤怠データを計算して結果を返す"""
    absent_shortage = calc_absent_shortage(
        inputs.absent_days,
        inputs.scheduled_minutes_per_day,
    )
    early_leave_shortage = inputs.early_leave_minutes
    total_shortage = absent_shortage + early_leave_shortage

    excess_overtime = calc_excess_overtime(
        inputs.overtime_minutes,
        inputs.deemed_overtime_minutes,
    )

    comment = generate_comment(total_shortage, excess_overtime, inputs.late_night_minutes)

    return AttendanceResult(
        absent_shortage_minutes=absent_shortage,
        early_leave_shortage_minutes=early_leave_shortage,
        total_shortage_minutes=total_shortage,
        excess_overtime_minutes=excess_overtime,
        late_night_minutes=inputs.late_night_minutes,
        comment=comment,
    )
