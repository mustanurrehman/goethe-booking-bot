#!/usr/bin/env python3
"""
Goethe Booking Bot - GUI Control Panel
=======================================
Tkinter-based interface to start/stop the bot and view real-time status.

Usage:
  python gui.py
"""

from __future__ import annotations

import csv
import logging
import os
import queue
import sys
import threading
import time
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Button, Text, Entry, Canvas,
    Scrollbar, ttk, filedialog, messagebox, END, NORMAL, DISABLED
)
from typing import Dict, List, Optional

# Add project dir to path
PROJECT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_DIR))

import booking_helper as bot

# ── Colour palette ──
BG = "#1e1e2e"
FG = "#cdd6f4"
ACCENT = "#89b4fa"
SUCCESS = "#a6e3a1"
ERROR = "#f38ba8"
WARNING = "#f9e2af"
CARD_BG = "#313244"
BTN_BG = "#45475a"
BTN_HOVER = "#585b70"


class QueuedHandler(logging.Handler):
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord):
        self.log_queue.put(self.format(record))


class StudentCard(Frame):
    def __init__(self, parent, student: Dict[str, str], index: int):
        super().__init__(parent, bg=CARD_BG, highlightbackground=ACCENT, highlightthickness=1)
        self.student = student
        self.name = student.get("name", f"Student {index+1}")
        self.level = student.get("level", student.get("exam_level", "?"))
        self.city = student.get("city", "?")
        self.booking_time = student.get("booking_datetime", "?")

        title = Label(self, text=f"👤 {self.name}", font=("Segoe UI", 11, "bold"),
                      bg=CARD_BG, fg=FG, anchor="w")
        title.pack(fill="x", padx=10, pady=(8, 2))

        detail_text = f"  {self.level} | {self.city} | Booking: {self.booking_time}"
        det = Label(self, text=detail_text, font=("Segoe UI", 9), bg=CARD_BG, fg="#a6adc8", anchor="w")
        det.pack(fill="x", padx=10, pady=(0, 2))

        self.status_label = Label(self, text="Status: ⏳ Waiting", font=("Segoe UI", 9, "bold"),
                                  bg=CARD_BG, fg=WARNING, anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=(0, 8))

    def update_status(self, text: str, colour: str = WARNING):
        self.status_label.config(text=f"Status: {text}", fg=colour)
        self.update_idletasks()


class BotGUI:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Goethe Booking Bot")
        self.root.geometry("800x650")
        self.root.configure(bg=BG)
        self.root.minsize(700, 550)

        self.stop_event = threading.Event()
        self.bot_thread: Optional[threading.Thread] = None
        self.running = False
        self.log_queue: queue.Queue = queue.Queue()
        self.students: List[Dict[str, str]] = []
        self.cards: List[StudentCard] = []

        self._setup_styles()
        self._build_ui()
        self._poll_log_queue()
        self._load_default_config()

    def _setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("TFrame", background=BG)
        style.configure("TLabelframe", background=BG, foreground=FG)
        style.configure("TLabelframe.Label", background=BG, foreground=FG)

    def _build_ui(self):
        # ── Header ──
        header = Frame(self.root, bg=BG)
        header.pack(fill="x", padx=15, pady=(12, 5))
        Label(header, text="🎓 Goethe Exam Booking Bot", font=("Segoe UI", 16, "bold"),
              bg=BG, fg=FG).pack(side="left")
        Label(header, text="v1.0", font=("Segoe UI", 9), bg=BG, fg="#6c7086").pack(side="left", padx=8)

        # ── Config row ──
        cfg_frame = Frame(self.root, bg=BG)
        cfg_frame.pack(fill="x", padx=15, pady=5)
        Label(cfg_frame, text="Config:", font=("Segoe UI", 10), bg=BG, fg=FG).pack(side="left")
        self.config_path_var = Entry(cfg_frame, font=("Segoe UI", 9), bg=CARD_BG, fg=FG,
                                     insertbackground=FG, relief="flat", bd=4)
        self.config_path_var.pack(side="left", fill="x", expand=True, padx=8)
        Button(cfg_frame, text="Browse", font=("Segoe UI", 9), bg=BTN_BG, fg=FG,
               activebackground=BTN_HOVER, activeforeground=FG,
               relief="flat", bd=2, padx=10, cursor="hand2",
               command=self._browse_config).pack(side="left")
        Button(cfg_frame, text="Reload", font=("Segoe UI", 9), bg=BTN_BG, fg=FG,
               activebackground=BTN_HOVER, activeforeground=FG,
               relief="flat", bd=2, padx=10, cursor="hand2",
               command=self._reload_config).pack(side="left", padx=(5, 0))

        # ── Control buttons ──
        ctrl = Frame(self.root, bg=BG)
        ctrl.pack(fill="x", padx=15, pady=8)

        self.start_btn = Button(ctrl, text="▶ Start Bot", font=("Segoe UI", 11, "bold"),
                                bg="#40a02b", fg="white", activebackground="#50c040",
                                activeforeground="white", relief="flat", bd=2,
                                padx=18, pady=6, cursor="hand2", command=self._start_bot)
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = Button(ctrl, text="■ Stop Bot", font=("Segoe UI", 11, "bold"),
                               bg="#d20f39", fg="white", activebackground="#e64553",
                               activeforeground="white", relief="flat", bd=2,
                               padx=18, pady=6, cursor="hand2", state=DISABLED,
                               command=self._stop_bot)
        self.stop_btn.pack(side="left")

        self.status_global = Label(ctrl, text="● Idle", font=("Segoe UI", 10, "bold"),
                                   bg=BG, fg="#6c7086")
        self.status_global.pack(side="right")

        # ── Split pane: Students (left) + Logs (right) ──
        panes = Frame(self.root, bg=BG)
        panes.pack(fill="both", expand=True, padx=15, pady=(0, 12))

        # Left: Student cards
        left = Frame(panes, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        Label(left, text="Students", font=("Segoe UI", 11, "bold"), bg=BG, fg=FG).pack(anchor="w", pady=(0, 5))

        canvas = Canvas(left, bg=BG, highlightthickness=0)
        scrollbar = Scrollbar(left, orient="vertical", command=canvas.yview)
        self.scrollable_frame = Frame(canvas, bg=BG)

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Right: Logs
        right = Frame(panes, bg=BG)
        right.pack(side="right", fill="both", expand=True)

        Label(right, text="Live Log", font=("Segoe UI", 11, "bold"), bg=BG, fg=FG).pack(anchor="w", pady=(0, 5))

        log_frame = Frame(right, bg=BG)
        log_frame.pack(fill="both", expand=True)

        self.log_text = Text(log_frame, font=("Consolas", 9), bg="#11111b", fg=FG,
                             insertbackground=FG, relief="flat", bd=4, wrap="word",
                             state=DISABLED)
        self.log_text.pack(side="left", fill="both", expand=True)

        log_scroll = Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=log_scroll.set)

        # tag configs for log colours
        self.log_text.tag_config("INFO", foreground=FG)
        self.log_text.tag_config("WARNING", foreground=WARNING)
        self.log_text.tag_config("ERROR", foreground=ERROR)
        self.log_text.tag_config("CRITICAL", foreground=ERROR, font=("Consolas", 9, "bold"))
        self.log_text.tag_config("DEBUG", foreground="#6c7086")

        # ── Footer ──
        footer = Frame(self.root, bg=BG)
        footer.pack(fill="x", padx=15, pady=(0, 10))
        Label(footer, text="⚠ Personal use only. Respect Goethe-Institut Terms of Service.",
              font=("Segoe UI", 8), bg=BG, fg="#6c7086").pack(side="left")

    def _load_default_config(self):
        cfg_path = PROJECT_DIR / "config.csv"
        if cfg_path.exists():
            self.config_path_var.delete(0, END)
            self.config_path_var.insert(0, str(cfg_path))
            self._reload_config()

    def _browse_config(self):
        path = filedialog.askopenfilename(
            title="Select config.csv",
            filetypes=[("CSV files", "*.csv")],
            initialdir=str(PROJECT_DIR),
        )
        if path:
            self.config_path_var.delete(0, END)
            self.config_path_var.insert(0, path)
            self._reload_config()

    def _reload_config(self):
        path = self.config_path_var.get().strip()
        if not path or not Path(path).exists():
            messagebox.showerror("Error", "Config file not found")
            return
        try:
            self.students = bot.load_all_students(path)
            self._rebuild_cards()
            self._log(f"Loaded {len(self.students)} student(s) from {Path(path).name}", "INFO")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load config:\n{exc}")

    def _rebuild_cards(self):
        for w in self.scrollable_frame.winfo_children():
            w.destroy()
        self.cards.clear()
        for i, student in enumerate(self.students):
            card = StudentCard(self.scrollable_frame, student, i)
            card.pack(fill="x", padx=5, pady=4)
            self.cards.append(card)

    def _start_bot(self):
        if self.running:
            return
        if not self.students:
            messagebox.showwarning("No students", "Load a config.csv first")
            return

        self.stop_event.clear()
        self.running = True
        self.start_btn.config(state=DISABLED)
        self.stop_btn.config(state=NORMAL)
        self.status_global.config(text="● Running", fg=SUCCESS)
        self._update_all_cards("⏳ Waiting for booking time", WARNING)

        self.bot_thread = threading.Thread(target=self._run_bot, daemon=True)
        self.bot_thread.start()

    def _stop_bot(self):
        if not self.running:
            return
        self.stop_event.set()
        self.status_global.config(text="● Stopping...", fg=WARNING)
        self.stop_btn.config(state=DISABLED)
        self._log("Stop requested...", "WARNING")

    def _run_bot(self):
        logger = logging.getLogger("gui_bot")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        handler = QueuedHandler(self.log_queue)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)

        threads = []
        results = []

        def update_log_from_student(s_name: str):
            std_logger = logging.getLogger(f"bot_{s_name}")
            std_logger.handlers.clear()
            std_handler = QueuedHandler(self.log_queue)
            std_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            std_logger.addHandler(std_handler)

        for i, student in enumerate(self.students):
            name = student.get("name", f"Student_{i}")
            update_log_from_student(name)

            t = threading.Thread(
                target=self._run_one_student,
                args=(student, i, results),
                daemon=True,
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        if self.stop_event.is_set():
            self._update_all_cards("⛔ Stopped by user", ERROR)
        else:
            self._update_all_cards("✅ Complete", SUCCESS)

        self.root.after(0, self._on_bot_finished)

    def _run_one_student(self, student: Dict[str, str], index: int, results: List):
        name = student.get("name", "Unknown")
        student_logger = logging.getLogger(f"bot_{name}")
        student_logger.handlers.clear()
        handler = QueuedHandler(self.log_queue)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        student_logger.addHandler(handler)

        self.root.after(0, lambda: self._update_card(index, "▶ Starting...", ACCENT))

        result = bot.run_student_flow(
            student,
            use_headless=False,
            logger=student_logger,
            stop_event=self.stop_event,
        )
        results.append(result)

        status = result.get("status", "failed")
        if status == "confirmed":
            self.root.after(0, lambda: self._update_card(index, "✅ Confirmed!", SUCCESS))
        elif status == "submitted":
            self.root.after(0, lambda: self._update_card(index, "✅ Submitted", SUCCESS))
        elif status == "stopped":
            self.root.after(0, lambda: self._update_card(index, "⛔ Stopped", ERROR))
        elif status == "failed":
            self.root.after(0, lambda: self._update_card(index, "❌ Failed", ERROR))
        else:
            self.root.after(0, lambda: self._update_card(index, status, WARNING))

    def _update_card(self, index: int, status_text: str, colour: str):
        if 0 <= index < len(self.cards):
            self.cards[index].update_status(status_text, colour)

    def _update_all_cards(self, text: str, colour: str):
        for card in self.cards:
            card.update_status(text, colour)

    def _on_bot_finished(self):
        self.running = False
        self.start_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)
        self.status_global.config(text="● Idle", fg="#6c7086")

    def _poll_log_queue(self):
        while True:
            try:
                record = self.log_queue.get_nowait()
                self._log(record)
            except queue.Empty:
                break
        self.root.after(200, self._poll_log_queue)

    def _log(self, message: str, level: str = "INFO"):
        self.log_text.config(state=NORMAL)
        if "|" in message and ("INFO" in message or "WARNING" in message or "ERROR" in message):
            parts = message.split("|", 2)
            if len(parts) == 3:
                msg_level = parts[1].strip().strip("[]")
                tag = msg_level if msg_level in ("INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG") else "INFO"
                self.log_text.insert(END, message + "\n", tag)
            else:
                self.log_text.insert(END, message + "\n", "INFO")
        else:
            self.log_text.insert(END, message + "\n", level if level in ("INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG") else "INFO")
        self.log_text.see(END)
        self.log_text.config(state=DISABLED)

    def on_close(self):
        if self.running:
            if messagebox.askyesno("Quit", "Bot is still running. Stop and quit?"):
                self.stop_event.set()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = Tk()
    app = BotGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
