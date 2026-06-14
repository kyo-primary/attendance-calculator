"""
勤怠計算ツール Tkinter GUI
"""

import tkinter as tk
from tkinter import ttk, font

from attendance_calculator import (
    AttendanceInput,
    InvalidTimeError,
    calculate,
    minutes_to_hhmm,
    parse_days,
    parse_time_to_minutes,
)

# --- 定数 ---
APP_TITLE = "勤怠計算ツール（目安）"
WIN_WIDTH = 560
WIN_HEIGHT = 660
BG = "#F5F7FA"
ACCENT = "#4A7FBF"
ACCENT_LIGHT = "#D6E4F5"
BTN_CLEAR = "#E0E0E0"
TEXT_FG = "#2C2C2C"
ERROR_FG = "#C0392B"
RESULT_BG = "#EAF2FB"
FONT_FAMILY = "Yu Gothic UI"
PAD = 12


class AttendanceApp(tk.Tk):
    """勤怠計算GUIアプリ"""

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.resizable(False, False)
        self.configure(bg=BG)
        self._center_window()
        self._build_ui()

    def _center_window(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - WIN_WIDTH) // 2
        y = (sh - WIN_HEIGHT) // 2
        self.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}+{x}+{y}")

    # ------------------------------------------------------------------
    # UI 構築
    # ------------------------------------------------------------------

    def _build_ui(self):
        # タイトル
        title_lbl = tk.Label(
            self,
            text="勤怠計算ツール",
            font=(FONT_FAMILY, 16, "bold"),
            bg=BG,
            fg=ACCENT,
        )
        title_lbl.pack(pady=(16, 4))

        note_lbl = tk.Label(
            self,
            text="※ あくまで目安計算です。正確な給与計算は会社の規定をご確認ください。",
            font=(FONT_FAMILY, 8),
            bg=BG,
            fg="#888888",
        )
        note_lbl.pack()

        # 入力フレーム
        input_frame = tk.LabelFrame(
            self,
            text="  入力項目  ",
            font=(FONT_FAMILY, 10, "bold"),
            bg=BG,
            fg=ACCENT,
            padx=PAD,
            pady=PAD,
        )
        input_frame.pack(fill="x", padx=PAD * 2, pady=(12, 6))

        self._entries: dict[str, tk.StringVar] = {}

        fields = [
            ("scheduled_days",      "月の所定労働日数（日）",    "20",   "日"),
            ("hours_per_day",       "1日の所定労働時間",          "8:00", "（例: 8 / 8:00）"),
            ("absent_days",         "欠勤日数（日）",             "0",    "日"),
            ("early_leave",         "早退時間",                   "0:00", "（例: 1:30）"),
            ("overtime",            "普通残業時間",               "0:00", "（例: 10:30）"),
            ("late_night",          "深夜労働時間",               "0:00", "（例: 2:00）"),
            ("deemed_overtime",     "みなし残業時間",             "0:00", "（例: 20:00）"),
        ]

        for key, label, default, hint in fields:
            row = tk.Frame(input_frame, bg=BG)
            row.pack(fill="x", pady=3)

            tk.Label(
                row,
                text=label,
                font=(FONT_FAMILY, 10),
                bg=BG,
                fg=TEXT_FG,
                width=22,
                anchor="w",
            ).pack(side="left")

            var = tk.StringVar(value=default)
            self._entries[key] = var

            entry = tk.Entry(
                row,
                textvariable=var,
                font=(FONT_FAMILY, 10),
                width=10,
                relief="solid",
                bd=1,
            )
            entry.pack(side="left", padx=(4, 6))

            tk.Label(
                row,
                text=hint,
                font=(FONT_FAMILY, 8),
                bg=BG,
                fg="#888888",
            ).pack(side="left")

        # ボタン行
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(pady=8)

        calc_btn = tk.Button(
            btn_frame,
            text="　計　算　",
            font=(FONT_FAMILY, 11, "bold"),
            bg=ACCENT,
            fg="white",
            activebackground="#3A6FAF",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._on_calculate,
        )
        calc_btn.pack(side="left", padx=8, ipady=4)

        clear_btn = tk.Button(
            btn_frame,
            text="　クリア　",
            font=(FONT_FAMILY, 11),
            bg=BTN_CLEAR,
            fg=TEXT_FG,
            activebackground="#C8C8C8",
            relief="flat",
            cursor="hand2",
            command=self._on_clear,
        )
        clear_btn.pack(side="left", padx=8, ipady=4)

        # エラー表示
        self._error_var = tk.StringVar()
        self._error_lbl = tk.Label(
            self,
            textvariable=self._error_var,
            font=(FONT_FAMILY, 9),
            bg=BG,
            fg=ERROR_FG,
            wraplength=WIN_WIDTH - PAD * 4,
        )
        self._error_lbl.pack()

        # 結果フレーム
        result_frame = tk.LabelFrame(
            self,
            text="  計算結果  ",
            font=(FONT_FAMILY, 10, "bold"),
            bg=BG,
            fg=ACCENT,
            padx=PAD,
            pady=PAD,
        )
        result_frame.pack(fill="x", padx=PAD * 2, pady=(4, PAD))

        result_rows = [
            ("absent_shortage",      "欠勤による不足時間"),
            ("early_leave_shortage", "早退による不足時間"),
            ("total_shortage",       "不足時間合計"),
            ("excess_overtime",      "みなし残業超過分"),
            ("late_night",           "深夜労働時間"),
        ]

        self._result_vars: dict[str, tk.StringVar] = {}

        for key, label in result_rows:
            row = tk.Frame(result_frame, bg=RESULT_BG, bd=0)
            row.pack(fill="x", pady=2)

            tk.Label(
                row,
                text=label,
                font=(FONT_FAMILY, 10),
                bg=RESULT_BG,
                fg=TEXT_FG,
                width=24,
                anchor="w",
                padx=6,
            ).pack(side="left")

            var = tk.StringVar(value="--:--")
            self._result_vars[key] = var

            tk.Label(
                row,
                textvariable=var,
                font=(FONT_FAMILY, 11, "bold"),
                bg=RESULT_BG,
                fg=ACCENT,
                width=10,
                anchor="e",
                padx=6,
            ).pack(side="right")

        # コメント欄
        self._comment_var = tk.StringVar(value="")
        comment_frame = tk.Frame(result_frame, bg=BG)
        comment_frame.pack(fill="x", pady=(8, 0))

        tk.Label(
            comment_frame,
            text="コメント:",
            font=(FONT_FAMILY, 9, "bold"),
            bg=BG,
            fg=TEXT_FG,
        ).pack(anchor="w")

        self._comment_lbl = tk.Label(
            comment_frame,
            textvariable=self._comment_var,
            font=(FONT_FAMILY, 9),
            bg=BG,
            fg=TEXT_FG,
            wraplength=WIN_WIDTH - PAD * 6,
            justify="left",
            anchor="w",
        )
        self._comment_lbl.pack(anchor="w", pady=(2, 0))

    # ------------------------------------------------------------------
    # イベントハンドラ
    # ------------------------------------------------------------------

    def _on_calculate(self):
        self._error_var.set("")
        try:
            inputs = self._parse_inputs()
        except InvalidTimeError as e:
            self._error_var.set(f"入力エラー: {e}")
            return

        result = calculate(inputs)

        self._result_vars["absent_shortage"].set(
            minutes_to_hhmm(result.absent_shortage_minutes)
        )
        self._result_vars["early_leave_shortage"].set(
            minutes_to_hhmm(result.early_leave_shortage_minutes)
        )
        self._result_vars["total_shortage"].set(
            minutes_to_hhmm(result.total_shortage_minutes)
        )
        self._result_vars["excess_overtime"].set(
            minutes_to_hhmm(result.excess_overtime_minutes)
        )
        self._result_vars["late_night"].set(
            minutes_to_hhmm(result.late_night_minutes)
        )
        self._comment_var.set(result.comment)

    def _on_clear(self):
        defaults = {
            "scheduled_days": "20",
            "hours_per_day":  "8:00",
            "absent_days":    "0",
            "early_leave":    "0:00",
            "overtime":       "0:00",
            "late_night":     "0:00",
            "deemed_overtime":"0:00",
        }
        for key, val in defaults.items():
            self._entries[key].set(val)

        for var in self._result_vars.values():
            var.set("--:--")

        self._comment_var.set("")
        self._error_var.set("")

    # ------------------------------------------------------------------
    # 入力解析
    # ------------------------------------------------------------------

    def _parse_inputs(self) -> AttendanceInput:
        scheduled_days = parse_days(self._entries["scheduled_days"].get())
        hours_per_day = parse_time_to_minutes(self._entries["hours_per_day"].get())
        absent_days = parse_days(self._entries["absent_days"].get())
        early_leave = parse_time_to_minutes(self._entries["early_leave"].get())
        overtime = parse_time_to_minutes(self._entries["overtime"].get())
        late_night = parse_time_to_minutes(self._entries["late_night"].get())
        deemed_overtime = parse_time_to_minutes(self._entries["deemed_overtime"].get())

        return AttendanceInput(
            scheduled_work_days=scheduled_days,
            scheduled_minutes_per_day=hours_per_day,
            absent_days=absent_days,
            early_leave_minutes=early_leave,
            overtime_minutes=overtime,
            late_night_minutes=late_night,
            deemed_overtime_minutes=deemed_overtime,
        )


def launch():
    """GUIを起動する"""
    app = AttendanceApp()
    app.mainloop()
