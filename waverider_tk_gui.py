"""Native Tkinter desktop frontend for WaveRider SDR."""

from __future__ import annotations

import json
import pathlib
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import cast
import webbrowser

import numpy as np

_PRESETS_FILE = pathlib.Path(__file__).with_name("waverider_presets.json")
_SDR_SETUP_FILE = pathlib.Path(__file__).with_name("SDR_SETUP.md")

# Pre-built hex lookup table — avoids per-pixel f-string calls in the waterfall hot path.
_WF_HEX: list[str] = [f"{i:02x}" for i in range(256)]

from waverider_common import AppState, BANDS, FrequencyScanner, run_startup_preflight


class WaveRiderTkGui:
    def __init__(self, root: tk.Tk, startup_notice: str = "", startup_missing_required: bool = False) -> None:
        self.root = root
        self.root.title("WaveRider SDR")
        self.root.geometry("1280x840")
        self.root.minsize(1000, 700)

        self._set_window_icon()
        self._configure_style()

        self.state = AppState()
        self.scanner = FrequencyScanner()
        if startup_notice:
            self.state.source_notice = startup_notice
        # Run the signal-processing loop (FFT + hardware I/O) on a dedicated
        # daemon thread so the Tk event loop is never blocked by compute.
        _signal_thread = threading.Thread(target=self._signal_loop, daemon=True)
        _signal_thread.start()
        self.waterfall_photo: tk.PhotoImage | None = None
        self.spectrum_points: list[float] = []
        self.device_drawer_visible = False
        self.shortcuts_overlay: tk.Toplevel | None = None
        self.selected_preset_slot = 0
        self.preset_slots: list[dict[str, float | str] | None] = [None, None, None]
        self.spectrum_marker_ratio = 0.5
        self.startup_notice = startup_notice
        self.startup_missing_required = startup_missing_required
        self._saved_settings: dict[str, object] = {}
        self._startup_alpha = 0.0
        self._wf_pos: int = -1  # circular-buffer write pointer; -1 = needs init
        self._load_presets()
        self._build_ui()
        self._restore_saved_settings()
        self._refresh_preset_buttons()
        self._animate_startup()
        self._show_startup_requirements_dialog_if_needed()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._schedule_update()

    def _set_window_icon(self) -> None:
        return

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        self.colors = {
            "bg": "#0b1220",
            "panel": "#111a2b",
            "panel_alt": "#162235",
            "panel_soft": "#1c2940",
            "text": "#eef4ff",
            "muted": "#a3b3cc",
            "accent": "#36d1c4",
            "accent_soft": "#1f8f88",
            "warning": "#ffb15c",
            "danger": "#ff6b6b",
            "grid": "#24334a",
            "canvas": "#07101a",
            "button_hover": "#17304d",
            "button_press": "#264966",
        }

        self.root.configure(background=self.colors["bg"])
        style.configure("App.TFrame", background=self.colors["bg"])
        style.configure("Panel.TFrame", background=self.colors["panel"])
        style.configure("Card.TFrame", background=self.colors["panel_alt"])
        style.configure("Header.TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 17, "bold"))
        style.configure("Subtle.TLabel", background=self.colors["bg"], foreground=self.colors["muted"], font=("Segoe UI", 9))
        style.configure("PanelTitle.TLabel", background=self.colors["panel_alt"], foreground=self.colors["text"], font=("Segoe UI", 10, "bold"))
        style.configure("Body.TLabel", background=self.colors["panel_alt"], foreground=self.colors["text"], font=("Segoe UI", 9))
        style.configure("Muted.TLabel", background=self.colors["panel_alt"], foreground=self.colors["muted"], font=("Segoe UI", 9))
        style.configure("GoodBadge.TLabel", background="#173a32", foreground="#b8fff3", font=("Segoe UI", 9, "bold"))
        style.configure("WarnBadge.TLabel", background="#46321c", foreground="#ffd8a6", font=("Segoe UI", 9, "bold"))
        style.configure("DangerBadge.TLabel", background="#4a2525", foreground="#ffd2d2", font=("Segoe UI", 9, "bold"))
        style.configure("IdleBadge.TLabel", background=self.colors["panel_alt"], foreground=self.colors["muted"], font=("Segoe UI", 9, "bold"))
        style.configure("Accent.TButton", font=("Segoe UI", 9, "bold"), padding=(12, 7))
        style.map(
            "Accent.TButton",
            padding=[("pressed", (12, 9)), ("active", (12, 8))],
            foreground=[("active", "#ffffff")],
            background=[("active", self.colors["accent_soft"]), ("pressed", self.colors["button_press"])],
        )
        style.map(
            "TButton",
            padding=[("pressed", (10, 8)), ("active", (10, 7))],
            foreground=[("active", self.colors["text"]), ("pressed", self.colors["text"])],
            background=[("active", self.colors["button_hover"]), ("pressed", self.colors["button_press"])],
        )
        style.configure("TButton", padding=(10, 6))
        style.configure("TEntry", fieldbackground="#0f1726", foreground=self.colors["text"], insertcolor=self.colors["text"])
        style.configure("TCombobox", fieldbackground="#0f1726", foreground=self.colors["text"])
        style.map("TCombobox", fieldbackground=[("readonly", "#0f1726")], foreground=[("readonly", self.colors["text"])])
        style.configure("TSeparator", background=self.colors["grid"])

    def _animate_startup(self) -> None:
        try:
            self.root.attributes("-alpha", 0.0)  # type: ignore[call-overload]
        except tk.TclError:
            return

        def step() -> None:
            self._startup_alpha = min(1.0, self._startup_alpha + 0.08)
            try:
                self.root.attributes("-alpha", self._startup_alpha)  # type: ignore[call-overload]
            except tk.TclError:
                return
            if self._startup_alpha < 1.0:
                self.root.after(16, step)

        self.root.after(16, step)

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

        header = ttk.Frame(self.root, padding=(16, 14, 16, 8), style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)
        header.columnconfigure(2, weight=0)
        ttk.Label(header, text="WaveRider SDR", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Native desktop console for spectrum, waterfall, and signal control",
            style="Subtle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.mode_badge = ttk.Label(header, text="MODE: IDLE", style="PanelTitle.TLabel")
        self.mode_badge.grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))
        ttk.Button(header, text="Shortcuts", command=self._toggle_shortcuts_overlay).grid(row=0, column=2, rowspan=2, sticky="e", padx=(12, 0))

        toolbar = ttk.Frame(self.root, padding=(16, 0, 16, 4), style="App.TFrame")
        toolbar.grid(row=1, column=0, sticky="ew")
        toolbar.columnconfigure(0, weight=1)
        toolbar.columnconfigure(1, weight=0)
        toolbar.columnconfigure(2, weight=0)
        toolbar.columnconfigure(3, weight=0)

        preset_row = ttk.Frame(toolbar, style="App.TFrame")
        preset_row.grid(row=0, column=0, sticky="w")
        ttk.Label(preset_row, text="View", style="Subtle.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Button(preset_row, text="Wide Spectrum", command=lambda: self._apply_view_preset("wide")).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(preset_row, text="Waterfall Focus", command=lambda: self._apply_view_preset("waterfall")).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(preset_row, text="Balanced", command=lambda: self._apply_view_preset("balanced")).grid(row=0, column=3)

        self.toolbar_apply_btn = ttk.Button(toolbar, text="Apply", style="Accent.TButton", command=self._apply_config)
        self.toolbar_apply_btn.grid(row=0, column=1, padx=(8, 8), sticky="e")
        self.toolbar_start_btn = ttk.Button(toolbar, text="Start", style="Accent.TButton", command=self._start)
        self.toolbar_start_btn.grid(row=0, column=2, padx=(0, 8), sticky="e")
        self.toolbar_stop_btn = ttk.Button(toolbar, text="Stop", style="Accent.TButton", command=self._stop)
        self.toolbar_stop_btn.grid(row=0, column=3, sticky="e")

        status_area = ttk.Frame(self.root, padding=(16, 0, 16, 8), style="App.TFrame")
        status_area.grid(row=2, column=0, sticky="ew")
        status_area.columnconfigure(0, weight=1)
        status_area.columnconfigure(1, weight=0)
        status_area.columnconfigure(2, weight=0)

        statusbar = ttk.Frame(status_area, style="App.TFrame")
        statusbar.grid(row=0, column=0, sticky="ew")
        statusbar.columnconfigure(0, weight=1)
        statusbar.columnconfigure(1, weight=0)
        badges = ttk.Frame(statusbar, style="App.TFrame")
        badges.grid(row=0, column=0, sticky="ew")
        badges.columnconfigure(0, weight=1)
        badges.columnconfigure(1, weight=0)
        badges.columnconfigure(2, weight=0)
        badges.columnconfigure(3, weight=0)
        badges.columnconfigure(4, weight=0)

        self.status_var = tk.StringVar(value="Stopped")
        ttk.Label(badges, textvariable=self.status_var, style="Subtle.TLabel").grid(row=0, column=0, sticky="w")

        self.source_badge = ttk.Label(badges, text="SIMULATED", style="PanelTitle.TLabel")
        self.source_badge.grid(row=0, column=1, sticky="e", padx=(8, 0))
        self.signal_badge = ttk.Label(badges, text="-120.0 dB", style="PanelTitle.TLabel")
        self.signal_badge.grid(row=0, column=2, sticky="e", padx=(8, 0))
        self.rate_badge = ttk.Label(badges, text="2.4 MS/s", style="PanelTitle.TLabel")
        self.rate_badge.grid(row=0, column=3, sticky="e", padx=(8, 0))
        self.squelch_badge = ttk.Label(badges, text="SQ -50 dB", style="IdleBadge.TLabel")
        self.squelch_badge.grid(row=0, column=4, sticky="e", padx=(8, 0))

        self.device_drawer_button = ttk.Button(statusbar, text="Device Status ▸", command=self._toggle_device_drawer)
        self.device_drawer_button.grid(row=0, column=1, sticky="e", padx=(12, 0))

        self.notice_var = tk.StringVar(value=self.startup_notice)
        self.notice_label = ttk.Label(status_area, textvariable=self.notice_var, style="Subtle.TLabel", foreground=self.colors["warning"])
        self.notice_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        drawer = ttk.Frame(status_area, padding=(0, 10, 0, 0), style="App.TFrame")
        drawer.grid(row=2, column=0, sticky="ew")
        drawer.columnconfigure(0, weight=1)
        drawer.columnconfigure(1, weight=1)
        self.device_drawer_frame = drawer
        self.device_drawer_frame.grid_remove()

        sdr_card = ttk.Frame(drawer, padding=12, style="Panel.TFrame")
        sdr_card.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        sdr_card.columnconfigure(0, weight=1)
        sdr_card.columnconfigure(1, weight=0)
        ttk.Label(sdr_card, text="SDR", style="PanelTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        self.sdr_device_var = tk.StringVar(value="Disconnected")
        self.sdr_count_var = tk.StringVar(value="Available devices: 0")
        self.sdr_error_var = tk.StringVar(value="Last error: none")
        ttk.Label(sdr_card, textvariable=self.sdr_device_var, style="Body.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.sdr_connect_var = tk.StringVar()
        self.sdr_combo = ttk.Combobox(
            sdr_card, textvariable=self.sdr_connect_var, state="readonly", width=22,
        )
        self.sdr_combo.grid(row=2, column=0, sticky="ew", padx=(0, 6), pady=(6, 0))
        sdr_btn_row = ttk.Frame(sdr_card, style="Panel.TFrame")
        sdr_btn_row.grid(row=2, column=1, sticky="e", pady=(6, 0))
        ttk.Button(sdr_btn_row, text="Connect", command=self._connect_sdr).grid(row=0, column=0, padx=(0, 4))
        ttk.Button(sdr_btn_row, text="Disconnect", command=self._disconnect_sdr).grid(row=0, column=1)
        ttk.Label(sdr_card, textvariable=self.sdr_count_var, style="Muted.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Label(sdr_card, textvariable=self.sdr_error_var, style="Muted.TLabel", wraplength=360, justify="left").grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Button(sdr_card, text="Driver Help", command=self._open_driver_help).grid(row=5, column=0, sticky="w", pady=(8, 0))

        mesh_card = ttk.Frame(drawer, padding=12, style="Panel.TFrame")
        mesh_card.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        mesh_card.columnconfigure(0, weight=1)
        ttk.Label(mesh_card, text="Meshtastic", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.mesh_count_var = tk.StringVar(value="Detected devices: 0")
        self.mesh_ports_var = tk.StringVar(value="Ports: none")
        ttk.Label(mesh_card, textvariable=self.mesh_count_var, style="Body.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(mesh_card, textvariable=self.mesh_ports_var, style="Muted.TLabel", wraplength=360, justify="left").grid(row=2, column=0, sticky="w", pady=(4, 0))

        splitter = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        splitter.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))

        controls_card = ttk.Frame(splitter, padding=14, style="Card.TFrame")
        visuals_card = ttk.Frame(splitter, padding=14, style="Panel.TFrame")
        splitter.add(controls_card, weight=1)  # type: ignore[attr-defined]
        splitter.add(visuals_card, weight=3)  # type: ignore[attr-defined]

        controls_card.columnconfigure(0, weight=1)
        controls_card.rowconfigure(1, weight=1)

        # Header with title
        ttk.Label(controls_card, text="Control Panel", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8), padx=(0, 8))

        # Create tabbed interface
        self.control_tabs = ttk.Notebook(controls_card)
        self.control_tabs.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

        # ============= TAB 1: GENERAL =============
        general_tab = ttk.Frame(self.control_tabs, style="Card.TFrame")
        general_tab.columnconfigure(0, weight=1)
        general_tab.columnconfigure(1, weight=1)
        self.control_tabs.add(general_tab, text="General")

        ttk.Label(general_tab, text="Band", style="Body.TLabel").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 0))
        self.band_var = tk.StringVar(value="")
        self.band_combo = ttk.Combobox(
            general_tab,
            textvariable=self.band_var,
            values=[band.name for band in BANDS],
            state="readonly",
        )
        self.band_combo.grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 10))
        self.band_combo.bind("<<ComboboxSelected>>", self._on_band_change)

        ttk.Label(general_tab, text="Frequency (MHz)", style="Body.TLabel").grid(row=0, column=1, sticky="w", padx=12, pady=(12, 0))
        self.freq_var = tk.StringVar(value="100.0")
        ttk.Entry(general_tab, textvariable=self.freq_var).grid(row=1, column=1, sticky="ew", padx=12, pady=(2, 10))

        ttk.Label(general_tab, text="Mode", style="Body.TLabel").grid(row=2, column=0, sticky="w", padx=12, pady=(0, 0))
        self.mode_var = tk.StringVar(value="None")
        ttk.Combobox(
            general_tab,
            textvariable=self.mode_var,
            values=["None", "AM", "FM", "USB", "LSB", "CW"],
            state="readonly",
        ).grid(row=3, column=0, sticky="ew", padx=12, pady=(2, 10))

        ttk.Label(general_tab, text="Sample Rate (Hz)", style="Body.TLabel").grid(row=2, column=1, sticky="w", padx=12, pady=(0, 0))
        self.sample_var = tk.StringVar(value="2400000")
        ttk.Combobox(
            general_tab,
            textvariable=self.sample_var,
            values=["2400000", "2048000", "1024000"],
            state="readonly",
        ).grid(row=3, column=1, sticky="ew", padx=12, pady=(2, 10))

        ttk.Label(general_tab, text="FFT Size", style="Body.TLabel").grid(row=4, column=0, sticky="w", padx=12, pady=(0, 0))
        self.fft_var = tk.StringVar(value="1024")
        ttk.Combobox(
            general_tab,
            textvariable=self.fft_var,
            values=["512", "1024", "2048", "4096"],
            state="readonly",
        ).grid(row=5, column=0, sticky="ew", padx=12, pady=(2, 12))

        # ============= TAB 2: CW/MORSE =============
        cw_tab = ttk.Frame(self.control_tabs, style="Card.TFrame")
        cw_tab.columnconfigure(0, weight=1)
        cw_tab.columnconfigure(1, weight=1)
        self.control_tabs.add(cw_tab, text="CW/Morse")

        ttk.Label(cw_tab, text="Morse Decode", style="Body.TLabel").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 0))
        self.morse_enable_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            cw_tab, text="Enable Morse Decoder", variable=self.morse_enable_var,
            command=self._toggle_morse_decode,
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(2, 10))

        ttk.Label(cw_tab, text="WPM", style="Body.TLabel").grid(row=2, column=0, sticky="w", padx=12, pady=(0, 0))
        self.morse_wpm_var = tk.StringVar(value="20")
        ttk.Entry(cw_tab, textvariable=self.morse_wpm_var, width=8).grid(row=3, column=0, sticky="w", padx=12, pady=(2, 10))

        ttk.Label(cw_tab, text="Output", style="Body.TLabel").grid(row=4, column=0, sticky="w", padx=12, pady=(0, 0))
        self.morse_output_var = tk.StringVar(value="(none)")
        morse_output_frame = ttk.Frame(cw_tab, style="Card.TFrame")
        morse_output_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=12, pady=(2, 12))
        morse_output_frame.columnconfigure(0, weight=1)
        ttk.Label(
            morse_output_frame,
            textvariable=self.morse_output_var,
            style="Body.TLabel",
            background=self.colors["canvas"],
            relief="sunken",
        ).grid(row=0, column=0, sticky="ew")

        # ============= TAB 3: PRESETS =============
        preset_tab = ttk.Frame(self.control_tabs, style="Card.TFrame")
        preset_tab.columnconfigure(0, weight=1)
        self.control_tabs.add(preset_tab, text="Presets")

        preset_slots_row = ttk.Frame(preset_tab, style="Card.TFrame")
        preset_slots_row.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 0))
        preset_slots_row.columnconfigure((0, 1, 2, 3), weight=1)
        self.preset_buttons: list[ttk.Button] = []
        for index in range(3):
            button = ttk.Button(preset_slots_row, text=f"{index + 1} Empty", command=lambda slot=index: self._recall_preset(slot))
            button.grid(row=0, column=index, sticky="ew", padx=(0, 6))
            self.preset_buttons.append(button)
        ttk.Button(preset_slots_row, text="Store Current", command=self._store_current_preset).grid(row=0, column=3, sticky="ew")

        ttk.Label(
            preset_tab,
            text="Ctrl+1..3: Recall | Shift+Ctrl+1..3: Store",
            style="Muted.TLabel",
            wraplength=320,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(12, 0))

        # ============= TAB 4: SCANNER =============
        scanner_tab = ttk.Frame(self.control_tabs, style="Card.TFrame")
        scanner_tab.columnconfigure(0, weight=1)
        scanner_tab.columnconfigure(1, weight=1)
        self.control_tabs.add(scanner_tab, text="Scanner")

        ttk.Label(scanner_tab, text="Start (MHz)", style="Body.TLabel").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 0))
        self.scan_start_var = tk.StringVar(value="88.0")
        ttk.Entry(scanner_tab, textvariable=self.scan_start_var).grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 10))

        ttk.Label(scanner_tab, text="Stop (MHz)", style="Body.TLabel").grid(row=0, column=1, sticky="w", padx=12, pady=(12, 0))
        self.scan_stop_var = tk.StringVar(value="108.0")
        ttk.Entry(scanner_tab, textvariable=self.scan_stop_var).grid(row=1, column=1, sticky="ew", padx=12, pady=(2, 10))

        ttk.Label(scanner_tab, text="Step (kHz)", style="Body.TLabel").grid(row=2, column=0, sticky="w", padx=12, pady=(0, 0))
        self.scan_step_var = tk.StringVar(value="100")
        ttk.Entry(scanner_tab, textvariable=self.scan_step_var).grid(row=3, column=0, sticky="ew", padx=12, pady=(2, 10))

        ttk.Label(scanner_tab, text="Dwell (ms)", style="Body.TLabel").grid(row=2, column=1, sticky="w", padx=12, pady=(0, 0))
        self.scan_dwell_var = tk.StringVar(value="200")
        ttk.Entry(scanner_tab, textvariable=self.scan_dwell_var).grid(row=3, column=1, sticky="ew", padx=12, pady=(2, 10))

        self.scan_pause_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(scanner_tab, text="Pause on signal", variable=self.scan_pause_var).grid(row=4, column=0, sticky="w", padx=12, pady=(0, 10))

        scanner_preset_row = ttk.Frame(scanner_tab, style="Card.TFrame")
        scanner_preset_row.grid(row=4, column=1, sticky="e", padx=12, pady=(0, 10))
        ttk.Button(scanner_preset_row, text="FM", command=lambda: self._apply_scan_preset("fm")).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(scanner_preset_row, text="2m", command=lambda: self._apply_scan_preset("2m")).grid(row=0, column=1, padx=(0, 6))
        ttk.Button(scanner_preset_row, text="NOAA", command=lambda: self._apply_scan_preset("noaa")).grid(row=0, column=2)

        scanner_btn_row = ttk.Frame(scanner_tab, style="Card.TFrame")
        scanner_btn_row.grid(row=5, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 10))
        scanner_btn_row.columnconfigure((0, 1), weight=1)
        self.scan_start_btn = ttk.Button(scanner_btn_row, text="Start Scan", style="Accent.TButton", command=self._start_scan)
        self.scan_start_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.scan_stop_btn = ttk.Button(scanner_btn_row, text="Stop Scan", style="Accent.TButton", command=self._stop_scan)
        self.scan_stop_btn.grid(row=0, column=1, sticky="ew")

        ttk.Label(scanner_tab, text="Scanner Status", style="Body.TLabel").grid(row=6, column=0, sticky="w", padx=12, pady=(0, 0))
        self.scan_status_var = tk.StringVar(value="Idle")
        ttk.Label(scanner_tab, textvariable=self.scan_status_var, style="Muted.TLabel").grid(row=7, column=0, columnspan=2, sticky="w", padx=12, pady=(2, 6))

        self.scan_progress = ttk.Progressbar(scanner_tab, orient="horizontal", mode="determinate", maximum=100)
        self.scan_progress.grid(row=8, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))

        # ============= TAB 5: ADVANCED =============
        adv_tab = ttk.Frame(self.control_tabs, style="Card.TFrame")
        adv_tab.columnconfigure(0, weight=1)
        adv_tab.columnconfigure(1, weight=1)
        self.control_tabs.add(adv_tab, text="Advanced")

        ttk.Label(adv_tab, text="Squelch (dB)", style="Body.TLabel").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 0))
        self.squelch_var = tk.StringVar(value="-50")
        ttk.Entry(adv_tab, textvariable=self.squelch_var).grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 10))

        ttk.Label(adv_tab, text="Min dB", style="Body.TLabel").grid(row=0, column=1, sticky="w", padx=12, pady=(12, 0))
        self.min_db_var = tk.StringVar(value="-80")
        ttk.Entry(adv_tab, textvariable=self.min_db_var).grid(row=1, column=1, sticky="ew", padx=12, pady=(2, 10))

        ttk.Label(adv_tab, text="Max dB", style="Body.TLabel").grid(row=2, column=0, sticky="w", padx=12, pady=(0, 0))
        self.max_db_var = tk.StringVar(value="0")
        ttk.Entry(adv_tab, textvariable=self.max_db_var).grid(row=3, column=0, sticky="ew", padx=12, pady=(2, 10))

        ttk.Label(adv_tab, text="Auto Range", style="Body.TLabel").grid(row=2, column=1, sticky="w", padx=12, pady=(0, 0))
        ttk.Button(adv_tab, text="Auto", command=self._auto_range_db).grid(row=3, column=1, sticky="ew", padx=12, pady=(2, 10))

        ttk.Label(adv_tab, text="Bandwidth (Hz)", style="Body.TLabel").grid(row=4, column=0, sticky="w", padx=12, pady=(0, 0))
        self.bandwidth_var = tk.StringVar(value="0")
        ttk.Entry(adv_tab, textvariable=self.bandwidth_var).grid(row=5, column=0, sticky="ew", padx=12, pady=(2, 10))

        ttk.Label(adv_tab, text="PPM Correction", style="Body.TLabel").grid(row=4, column=1, sticky="w", padx=12, pady=(0, 0))
        self.ppm_var = tk.StringVar(value="0")
        ttk.Entry(adv_tab, textvariable=self.ppm_var).grid(row=5, column=1, sticky="ew", padx=12, pady=(2, 10))

        ttk.Label(adv_tab, text="Noise Blanker", style="Body.TLabel").grid(row=6, column=0, sticky="w", padx=12, pady=(0, 0))
        self.noise_blanker_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(adv_tab, text="Enable impulse blanking", variable=self.noise_blanker_var).grid(row=7, column=0, sticky="w", padx=12, pady=(2, 12))

        ttk.Label(adv_tab, text="NB Threshold", style="Body.TLabel").grid(row=6, column=1, sticky="w", padx=12, pady=(0, 0))
        self.nb_threshold_var = tk.StringVar(value="3.0")
        ttk.Entry(adv_tab, textvariable=self.nb_threshold_var).grid(row=7, column=1, sticky="ew", padx=12, pady=(2, 12))

        # Signal meter (at bottom of all tabs)
        meter_frame = ttk.Frame(controls_card, style="Card.TFrame")
        meter_frame.grid(row=2, column=0, sticky="ew", padx=(0, 8), pady=(8, 0))
        meter_frame.columnconfigure(0, weight=1)
        ttk.Label(meter_frame, text="Signal Meter", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.meter_canvas = tk.Canvas(
            meter_frame,
            height=24,
            background=self.colors["canvas"],
            highlightthickness=1,
            highlightbackground=self.colors["grid"],
            bd=0,
        )
        self.meter_canvas.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        # Control buttons
        button_row = ttk.Frame(controls_card, style="Card.TFrame")
        button_row.grid(row=3, column=0, sticky="ew", padx=(0, 8), pady=(8, 0))
        button_row.columnconfigure((0, 1, 2), weight=1)
        self.panel_apply_btn = ttk.Button(button_row, text="Apply", style="Accent.TButton", command=self._apply_config)
        self.panel_apply_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.panel_start_btn = ttk.Button(button_row, text="Start", style="Accent.TButton", command=self._start)
        self.panel_start_btn.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.panel_stop_btn = ttk.Button(button_row, text="Stop", style="Accent.TButton", command=self._stop)
        self.panel_stop_btn.grid(row=0, column=2, sticky="ew")

        visuals_card.columnconfigure(0, weight=1)
        visuals_card.rowconfigure(1, weight=1)
        visuals_card.rowconfigure(3, weight=1)

        spectrum_header = ttk.Frame(visuals_card, style="Panel.TFrame")
        spectrum_header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        spectrum_header.columnconfigure(0, weight=1)
        ttk.Label(spectrum_header, text="Spectrum", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            spectrum_header,
            text="Click or drag the marker to retune the center",
            style="Subtle.TLabel",
        ).grid(row=0, column=1, sticky="e")
        self.spectrum_canvas = tk.Canvas(
            visuals_card,
            height=220,
            background=self.colors["canvas"],
            highlightthickness=1,
            highlightbackground=self.colors["grid"],
            bd=0,
        )
        self.spectrum_canvas.grid(row=1, column=0, sticky="nsew")
        self.spectrum_canvas.bind("<Button-1>", self._on_spectrum_click)
        self.spectrum_canvas.bind("<B1-Motion>", self._on_spectrum_drag)
        self.spectrum_canvas.bind("<ButtonRelease-1>", self._on_spectrum_release)

        wf_header = ttk.Frame(visuals_card, style="Panel.TFrame")
        wf_header.grid(row=2, column=0, sticky="ew", pady=(12, 8))
        wf_header.columnconfigure(0, weight=1)
        ttk.Label(wf_header, text="Waterfall", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.peak_hold_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            wf_header, text="Peak Hold", variable=self.peak_hold_var,
            command=self._toggle_peak_hold,
        ).grid(row=0, column=1, sticky="e", padx=(12, 0))
        self.waterfall_canvas = tk.Canvas(
            visuals_card,
            height=360,
            background=self.colors["canvas"],
            highlightthickness=1,
            highlightbackground=self.colors["grid"],
            bd=0,
        )
        self.waterfall_canvas.grid(row=3, column=0, sticky="nsew")

        footer = ttk.Frame(visuals_card, style="Panel.TFrame")
        footer.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, text="Morse Output", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.morse_var = tk.StringVar(value="(none)")
        ttk.Label(footer, textvariable=self.morse_var, style="Body.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.waterfall_canvas.bind("<Configure>", self._on_waterfall_resize)
        self.root.bind_all("<Control-Return>", lambda _event: self._apply_config())
        self.root.bind_all("<F5>", lambda _event: self._start())
        self.root.bind_all("<Escape>", self._handle_escape)
        self.root.bind_all("<F1>", lambda _event: self._toggle_shortcuts_overlay())
        self.root.bind_all("<Control-slash>", lambda _event: self._toggle_shortcuts_overlay())
        self.root.bind_all("<space>", self._toggle_running)
        self.root.bind_all("<Left>", lambda _event: self._nudge_tuning_marker(-0.01, commit=True))
        self.root.bind_all("<Right>", lambda _event: self._nudge_tuning_marker(0.01, commit=True))
        self.root.bind_all("<Shift-Left>", lambda _event: self._nudge_tuning_marker(-0.05, commit=True))
        self.root.bind_all("<Shift-Right>", lambda _event: self._nudge_tuning_marker(0.05, commit=True))
        self.root.bind_all("<Control-KeyPress-1>", lambda _event: self._recall_preset(0))
        self.root.bind_all("<Control-KeyPress-2>", lambda _event: self._recall_preset(1))
        self.root.bind_all("<Control-KeyPress-3>", lambda _event: self._recall_preset(2))
        self.root.bind_all("<Control-Shift-KeyPress-1>", lambda _event: self._store_preset(0))
        self.root.bind_all("<Control-Shift-KeyPress-2>", lambda _event: self._store_preset(1))
        self.root.bind_all("<Control-Shift-KeyPress-3>", lambda _event: self._store_preset(2))

    def _handle_escape(self, _event: tk.Event) -> str:
        if self.shortcuts_overlay is not None and self.shortcuts_overlay.winfo_exists() and self.shortcuts_overlay.state() == "normal":
            self._toggle_shortcuts_overlay()
            return "break"
        if self.device_drawer_visible:
            self._toggle_device_drawer()
            return "break"
        self._stop()
        return "break"

    def _toggle_running(self, _event: tk.Event | None = None) -> str:
        with self.state.lock:
            if self.state.running:
                self.state.stop()
            else:
                self.state.start()
        return "break"

    def _spectrum_frequency_hz(self, ratio: float) -> float:
        with self.state.lock:
            center_freq = self.state.center_freq
            sample_rate = self.state.sample_rate
        low = center_freq - (sample_rate / 2.0)
        return max(0.0, low + (sample_rate * ratio))

    def _set_tuning_marker_from_x(self, x: int, commit: bool = False) -> None:
        width = max(1, self.spectrum_canvas.winfo_width())
        ratio = max(0.0, min(1.0, x / max(1, width - 1)))
        self.spectrum_marker_ratio = ratio
        frequency_hz = self._spectrum_frequency_hz(ratio)
        self.freq_var.set(f"{frequency_hz / 1_000_000.0:.3f}")
        if commit:
            self._apply_config()

    def _on_spectrum_click(self, event: tk.Event) -> None:
        self._set_tuning_marker_from_x(event.x, commit=True)

    def _on_spectrum_drag(self, event: tk.Event) -> None:
        self._set_tuning_marker_from_x(event.x, commit=False)

    def _on_spectrum_release(self, event: tk.Event) -> None:
        self._set_tuning_marker_from_x(event.x, commit=True)

    def _nudge_tuning_marker(self, delta_ratio: float, commit: bool = False) -> str:
        width = max(1, self.spectrum_canvas.winfo_width())
        x = int(round((self.spectrum_marker_ratio + delta_ratio) * max(1, width - 1)))
        self._set_tuning_marker_from_x(x, commit=commit)
        return "break"

    def _load_presets(self) -> None:
        try:
            data = json.loads(_PRESETS_FILE.read_text(encoding="utf-8"))
            slots = data.get("presets", [])
            for index in range(min(len(self.preset_slots), len(slots))):
                entry = slots[index]
                if entry is None:
                    self.preset_slots[index] = None
                elif isinstance(entry, dict) and "frequency_mhz" in entry and "mode" in entry:
                    typed: dict[str, object] = entry  # type: ignore[assignment]
                    self.preset_slots[index] = {
                        "frequency_mhz": float(typed["frequency_mhz"]),  # type: ignore[arg-type]
                        "mode": str(typed["mode"]),
                    }

            settings = data.get("settings", {})
            if isinstance(settings, dict):
                self._saved_settings = cast(dict[str, object], settings)
            else:
                self._saved_settings = {}
        except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            self._saved_settings = {}

    def _save_presets(self) -> None:
        slots: list[dict[str, float | str] | None] = []
        for preset in self.preset_slots:
            if preset is None:
                slots.append(None)
            else:
                slots.append({"frequency_mhz": float(preset["frequency_mhz"]), "mode": str(preset["mode"])})

        settings: dict[str, object] = {
            "bandwidth_hz": self.bandwidth_var.get(),
            "ppm_correction": self.ppm_var.get(),
            "noise_blanker": bool(self.noise_blanker_var.get()),
            "noise_blanker_threshold": self.nb_threshold_var.get(),
            "scan_start_mhz": self.scan_start_var.get(),
            "scan_stop_mhz": self.scan_stop_var.get(),
            "scan_step_khz": self.scan_step_var.get(),
            "scan_dwell_ms": self.scan_dwell_var.get(),
            "scan_pause_on_signal": bool(self.scan_pause_var.get()),
        }
        try:
            _PRESETS_FILE.write_text(json.dumps({"presets": slots, "settings": settings}, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _restore_saved_settings(self) -> None:
        settings = self._saved_settings
        value = settings.get("bandwidth_hz")
        if value is not None:
            self.bandwidth_var.set(str(value))
        value = settings.get("ppm_correction")
        if value is not None:
            self.ppm_var.set(str(value))
        value = settings.get("noise_blanker")
        if value is not None:
            self.noise_blanker_var.set(bool(value))
        value = settings.get("noise_blanker_threshold")
        if value is not None:
            self.nb_threshold_var.set(str(value))
        value = settings.get("scan_start_mhz")
        if value is not None:
            self.scan_start_var.set(str(value))
        value = settings.get("scan_stop_mhz")
        if value is not None:
            self.scan_stop_var.set(str(value))
        value = settings.get("scan_step_khz")
        if value is not None:
            self.scan_step_var.set(str(value))
        value = settings.get("scan_dwell_ms")
        if value is not None:
            self.scan_dwell_var.set(str(value))
        value = settings.get("scan_pause_on_signal")
        if value is not None:
            self.scan_pause_var.set(bool(value))

    def _on_close(self) -> None:
        self._save_presets()
        self.root.destroy()

    def _preset_data(self, slot: int) -> dict[str, float | str] | None:
        if 0 <= slot < len(self.preset_slots):
            return self.preset_slots[slot]
        return None

    def _refresh_preset_buttons(self) -> None:
        if not hasattr(self, "preset_buttons"):
            return
        for index, button in enumerate(self.preset_buttons):
            preset = self._preset_data(index)
            if preset is None:
                button.configure(text=f"{index + 1} Empty")
                continue
            frequency_mhz = float(preset["frequency_mhz"])
            mode = str(preset["mode"])
            button.configure(text=f"{index + 1} {frequency_mhz:.3f} {mode}")

    def _store_preset(self, slot: int) -> str:
        try:
            frequency_mhz = float(self.freq_var.get())
        except ValueError:
            self.notice_var.set("Invalid frequency for preset save.")
            return "break"
        self.preset_slots[slot] = {"frequency_mhz": frequency_mhz, "mode": self.mode_var.get()}
        self.selected_preset_slot = slot
        self._refresh_preset_buttons()
        self._save_presets()
        self.notice_var.set(f"Stored preset {slot + 1}.")
        return "break"

    def _store_current_preset(self) -> None:
        self._store_preset(self.selected_preset_slot)

    def _recall_preset(self, slot: int) -> str:
        preset = self._preset_data(slot)
        self.selected_preset_slot = slot
        if preset is None:
            self.notice_var.set(f"Preset {slot + 1} is empty.")
            self._refresh_preset_buttons()
            return "break"
        self.freq_var.set(f"{float(preset['frequency_mhz']):.3f}")
        self.mode_var.set(str(preset["mode"]))
        self.spectrum_marker_ratio = 0.5
        self._apply_config()
        self._refresh_preset_buttons()
        self.notice_var.set(f"Recalled preset {slot + 1}.")
        return "break"

    def _auto_range_db(self) -> None:
        with self.state.lock:
            waveform = self.state.waveform_data.copy()
        if waveform.size < 2:
            return
        lo = float(np.percentile(waveform, 5))
        hi = float(np.percentile(waveform, 99))
        margin = max(5.0, (hi - lo) * 0.1)
        self.min_db_var.set(f"{lo - margin:.0f}")
        self.max_db_var.set(f"{hi + margin:.0f}")
        self._apply_config()

    def _toggle_peak_hold(self) -> None:
        with self.state.lock:
            self.state.waterfall_settings.peak_hold = self.peak_hold_var.get()

    def _toggle_morse_decode(self) -> None:
        with self.state.lock:
            self.state.morse_enabled = self.morse_enable_var.get()
            # Update WPM if specified
            try:
                wpm = float(self.morse_wpm_var.get())
                if wpm > 0:
                    self.state.morse_decoder.wpm = wpm
            except ValueError:
                pass

    def _toggle_device_drawer(self) -> None:
        self.device_drawer_visible = not self.device_drawer_visible
        if self.device_drawer_visible:
            self.device_drawer_frame.grid()
            self.device_drawer_button.configure(text="Device Status ▾")
        else:
            self.device_drawer_frame.grid_remove()
            self.device_drawer_button.configure(text="Device Status ▸")

    def _connect_sdr(self) -> None:
        device_id = self.sdr_connect_var.get()
        if not device_id:
            self.notice_var.set("Select a device from the list first.")
            return
        with self.state.lock:
            ok = self.state.sdr.connect(device_id)
            error = self.state.sdr.last_error
        if ok:
            self.notice_var.set(f"Connected to {device_id}.")
        else:
            self.notice_var.set(f"Connection failed: {error or 'unknown error'}")

    def _disconnect_sdr(self) -> None:
        with self.state.lock:
            self.state.sdr.disconnect()
        self.notice_var.set("SDR device disconnected.")

    def _open_driver_help(self) -> None:
        try:
            if _SDR_SETUP_FILE.exists():
                webbrowser.open(_SDR_SETUP_FILE.resolve().as_uri())
                self.notice_var.set("Opened SDR setup guide.")
                return
        except Exception:
            pass

        messagebox.showinfo(
            "Driver Setup Help",
            "Could not open SDR_SETUP.md automatically."
            "\nOpen SDR_SETUP.md in this project for Windows Zadig and backend setup steps.",
        )

    def _show_startup_requirements_dialog_if_needed(self) -> None:
        if not self.startup_missing_required:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Startup Check Failed")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        frame = ttk.Frame(dialog, padding=14, style="Card.TFrame")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Missing required Python dependencies", style="PanelTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            frame,
            text=(
                "WaveRider could not install one or more required packages during startup.\n"
                "Select Retry Install to try again now."
            ),
            style="Body.TLabel",
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        self.retry_status_var = tk.StringVar(value=self.startup_notice)
        ttk.Label(
            frame,
            textvariable=self.retry_status_var,
            style="Muted.TLabel",
            wraplength=520,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))

        button_row = ttk.Frame(frame, style="Card.TFrame")
        button_row.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        ttk.Button(button_row, text="Retry Install", command=lambda: self._retry_startup_install(dialog)).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(button_row, text="Continue", command=dialog.destroy).grid(row=0, column=1)

        dialog.update_idletasks()
        x = self.root.winfo_rootx() + max(20, (self.root.winfo_width() - dialog.winfo_width()) // 2)
        y = self.root.winfo_rooty() + 120
        dialog.geometry(f"+{x}+{max(20, y)}")

    def _retry_startup_install(self, dialog: tk.Toplevel) -> None:
        result = run_startup_preflight(auto_install=True, force_refresh=True)
        self.startup_notice = result.short_notice()
        self.notice_var.set(self.startup_notice)

        if result.missing_required:
            self.retry_status_var.set(
                "Retry failed. Missing: " + ", ".join(result.missing_required)
            )
            return

        self.retry_status_var.set("Retry succeeded. Required dependencies are installed.")
        self.startup_missing_required = False
        self.root.after(250, dialog.destroy)

    def _update_device_drawer(self, status: dict[str, object]) -> None:
        sdr_devices = cast(list[dict[str, object]], status.get("sdr_devices") or [])
        connected_id = status.get("connected_sdr_id")
        connected_device: dict[str, object] | None = None
        for device in sdr_devices:
            if device.get("id") == connected_id:
                connected_device = device
                break

        if connected_device is None:
            self.sdr_device_var.set("Connected: simulated source")
        else:
            device_type = str(connected_device.get("device_type", "SDR"))
            device_name = str(connected_device.get("name", "unknown"))
            self.sdr_device_var.set(f"Connected: {device_type} ({device_name})")

        self.sdr_count_var.set(f"Available devices: {len(sdr_devices)}")
        self.sdr_error_var.set(f"Last error: {status.get('sdr_last_error') or 'none'}")

        # Keep the device-select combobox in sync with detected hardware.
        device_ids = [str(d.get("id", "")) for d in sdr_devices if d.get("id")]
        if list(self.sdr_combo["values"]) != device_ids:
            self.sdr_combo["values"] = device_ids
            if device_ids and not self.sdr_connect_var.get():
                self.sdr_connect_var.set(device_ids[0])

        meshtastic_devices = cast(list[dict[str, object]], status.get("meshtastic_devices") or [])
        mesh_ports = [str(device.get("port")) for device in meshtastic_devices[:3] if device.get("port")]
        ports_text = ", ".join(mesh_ports) if mesh_ports else "none"
        if len(meshtastic_devices) > 3:
            ports_text = f"{ports_text}, +{len(meshtastic_devices) - 3} more"

        self.mesh_count_var.set(f"Detected devices: {len(meshtastic_devices)}")
        self.mesh_ports_var.set(f"Ports: {ports_text}")

    def _ensure_shortcuts_overlay(self) -> None:
        if self.shortcuts_overlay is not None and self.shortcuts_overlay.winfo_exists():
            return

        overlay = tk.Toplevel(self.root)
        overlay.withdraw()
        overlay.overrideredirect(True)
        overlay.transient(self.root)
        try:
            overlay.attributes("-topmost", True)  # type: ignore[call-overload]
            overlay.attributes("-alpha", 0.98)  # type: ignore[call-overload]
        except tk.TclError:
            pass
        overlay.configure(background=self.colors["bg"])
        overlay.protocol("WM_DELETE_WINDOW", self._toggle_shortcuts_overlay)
        overlay.bind("<FocusOut>", lambda _event: self._toggle_shortcuts_overlay())

        shell = ttk.Frame(overlay, padding=16, style="Panel.TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(1, weight=1)
        ttk.Label(shell, text="Keyboard Shortcuts", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(shell, text="Fast controls for tuning, presets, and run state.", style="Subtle.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 12))

        shortcuts = [
            ("F1 / Ctrl+/", "Toggle this overlay"),
            ("Ctrl+Enter", "Apply the control panel"),
            ("F5 / Space", "Start or toggle running"),
            ("Esc", "Stop or close overlays"),
            ("Ctrl+1..3", "Recall preset slots"),
            ("Shift+Ctrl+1..3", "Store preset slots"),
            ("Left / Right", "Nudge the tuning marker"),
            ("Shift+Left / Shift+Right", "Nudge faster"),
        ]
        for row_index, (keys, description) in enumerate(shortcuts, start=2):
            ttk.Label(shell, text=keys, style="PanelTitle.TLabel").grid(row=row_index, column=0, sticky="w", padx=(0, 16), pady=(0, 6))
            ttk.Label(shell, text=description, style="Body.TLabel").grid(row=row_index, column=1, sticky="w", pady=(0, 6))

        self.shortcuts_overlay = overlay

    def _toggle_shortcuts_overlay(self) -> None:
        self._ensure_shortcuts_overlay()
        assert self.shortcuts_overlay is not None
        if self.shortcuts_overlay.state() == "withdrawn":
            self.shortcuts_overlay.deiconify()
            self.shortcuts_overlay.update_idletasks()
            width = 520
            height = 300
            x = self.root.winfo_rootx() + (self.root.winfo_width() - width) // 2
            y = self.root.winfo_rooty() + 90
            self.shortcuts_overlay.geometry(f"{width}x{height}+{max(20, x)}+{max(20, y)}")
            self.shortcuts_overlay.lift()  # type: ignore[call-overload]
            self.shortcuts_overlay.focus_force()
        else:
            self.shortcuts_overlay.withdraw()

    def _on_waterfall_resize(self, _event: tk.Event) -> None:
        self.waterfall_photo = None
        self._wf_pos = -1

    def _on_band_change(self, _event: tk.Event) -> None:
        band_name = self.band_var.get()
        with self.state.lock:
            if self.state.set_band(band_name):
                self.freq_var.set(f"{self.state.center_freq / 1_000_000.0:.3f}")
                self.mode_var.set(self.state.modulation_mode)


    def _apply_view_preset(self, preset: str) -> None:
        if preset == "wide":
            self.root.geometry("1440x820")
        elif preset == "waterfall":
            self.root.geometry("1240x920")
        else:
            self.root.geometry("1280x840")

    def _start_scan(self) -> None:
        try:
            start_mhz = float(self.scan_start_var.get())
            stop_mhz = float(self.scan_stop_var.get())
            step_khz = float(self.scan_step_var.get())
            dwell_ms = int(float(self.scan_dwell_var.get()))
        except ValueError:
            self.notice_var.set("Invalid scanner numeric input.")
            return

        start_hz = start_mhz * 1_000_000.0
        stop_hz = stop_mhz * 1_000_000.0
        step_hz = step_khz * 1_000.0

        if start_hz >= stop_hz:
            self.notice_var.set("Scanner start must be lower than stop.")
            return

        with self.state.lock:
            self.scanner.start(
                start_hz=start_hz,
                stop_hz=stop_hz,
                step_hz=step_hz,
                dwell_ms=dwell_ms,
                pause_on_signal=self.scan_pause_var.get(),
            )
        self._save_presets()
        self.notice_var.set("Scanner started.")

    def _apply_scan_preset(self, preset: str) -> None:
        if preset == "fm":
            self.scan_start_var.set("88.0")
            self.scan_stop_var.set("108.0")
            self.scan_step_var.set("100")
            self.scan_dwell_var.set("200")
            self.scan_pause_var.set(True)
            self.notice_var.set("Scanner preset: FM broadcast")
        elif preset == "2m":
            self.scan_start_var.set("144.0")
            self.scan_stop_var.set("148.0")
            self.scan_step_var.set("12.5")
            self.scan_dwell_var.set("250")
            self.scan_pause_var.set(True)
            self.notice_var.set("Scanner preset: 2m amateur")
        elif preset == "noaa":
            self.scan_start_var.set("162.400")
            self.scan_stop_var.set("162.550")
            self.scan_step_var.set("25")
            self.scan_dwell_var.set("300")
            self.scan_pause_var.set(True)
            self.notice_var.set("Scanner preset: NOAA weather")
        self._save_presets()

    def _stop_scan(self) -> None:
        with self.state.lock:
            self.scanner.stop()
        self.notice_var.set("Scanner stopped.")

    def _start(self) -> None:
        with self.state.lock:
            self.state.start()
        self.notice_var.set("SDR started.")

    def _stop(self) -> None:
        with self.state.lock:
            self.state.stop()
        self.notice_var.set("SDR stopped.")

    def _apply_config(self) -> None:
        try:
            frequency_mhz = float(self.freq_var.get())
            sample_rate = float(self.sample_var.get())
            fft_size = int(self.fft_var.get())
            squelch = float(self.squelch_var.get())
            min_db = float(self.min_db_var.get())
            max_db = float(self.max_db_var.get())
            bandwidth_hz = float(self.bandwidth_var.get())
            ppm_correction = float(self.ppm_var.get())
            nb_threshold = float(self.nb_threshold_var.get())
        except ValueError:
            self.notice_var.set("Invalid numeric input in controls.")
            return

        with self.state.lock:
            self.state.configure(
                frequency_mhz=frequency_mhz,
                sample_rate_hz=sample_rate,
                fft_size=fft_size,
                modulation_mode=self.mode_var.get(),
                squelch_db=squelch,
                min_db=min_db,
                max_db=max_db,
                bandwidth_hz=bandwidth_hz,
                noise_blanker=self.noise_blanker_var.get(),
                noise_blanker_threshold=nb_threshold,
                ppm_correction=ppm_correction,
            )
        self._save_presets()
        self.notice_var.set("Configuration updated.")

    def _schedule_update(self) -> None:
        self._update_frame()
        self.root.after(50, self._schedule_update)

    def _signal_loop(self) -> None:
        """Runs on a background daemon thread; owns all AppState.tick() calls."""
        while True:
            with self.state.lock:
                if self.state.running:
                    self.scanner.update(self.state)
                    self.state.tick()
            time.sleep(0.04)  # ~25 Hz signal update rate

    def _update_frame(self) -> None:
        with self.state.lock:
            waveform = self.state.waveform_data.copy()
            status = self.state.get_status()
            min_db = self.state.waterfall_settings.min_db
            max_db = self.state.waterfall_settings.max_db
            center_freq = self.state.center_freq
            sample_rate = self.state.sample_rate
            squelch_db = self.state.demodulator.squelch_db

        self._draw_spectrum(waveform, min_db, max_db, center_freq, sample_rate, squelch_db)
        if status.get("running"):
            self._draw_waterfall(waveform, min_db, max_db)

        self.status_var.set(f"{'Running' if status['running'] else 'Stopped'}")
        source_notice = str(status.get("source_notice") or "")
        if source_notice:
            self.notice_var.set(source_notice)

        self.mode_badge.configure(text=f"MODE: {str(status.get('modulation_mode') or 'NONE').upper()}")
        self.source_badge.configure(text=str(status.get("source") or "SIMULATED").upper())
        self.signal_badge.configure(text=f"{status['signal_strength_db']:.1f} dB")
        bw_value = status.get("bandwidth_hz")
        if isinstance(bw_value, (int, float)):
            self.bandwidth_var.set(f"{float(bw_value):.0f}")
        ppm_value = status.get("ppm_correction")
        if isinstance(ppm_value, (int, float)):
            self.ppm_var.set(f"{float(ppm_value):.0f}")
        nb_enabled = bool(status.get("noise_blanker"))
        self.noise_blanker_var.set(nb_enabled)
        nb_thresh = status.get("noise_blanker_threshold")
        if isinstance(nb_thresh, (int, float)):
            self.nb_threshold_var.set(f"{float(nb_thresh):.1f}")
        sample_rate_value = status.get("sample_rate")
        sample_rate_hz = sample_rate_value if isinstance(sample_rate_value, (int, float)) else 0.0
        self.rate_badge.configure(text=f"{sample_rate_hz / 1_000_000.0:.1f} MS/s")
        signal_value = status.get("signal_strength_db")
        signal_db = signal_value if isinstance(signal_value, (int, float)) else -120.0
        signal_detected = bool(status.get("signal_detected"))
        squelch_value = status.get("squelch_db")
        squelch_db = squelch_value if isinstance(squelch_value, (int, float)) else -50.0
        self.squelch_badge.configure(text=f"SQ {squelch_db:.0f} dB")
        self.squelch_badge.configure(style="GoodBadge.TLabel" if signal_detected else "IdleBadge.TLabel")

        running = bool(status.get("running"))
        if running:
            self.mode_badge.configure(style="GoodBadge.TLabel")
            self.toolbar_start_btn.state(["disabled"])
            self.panel_start_btn.state(["disabled"])
            self.toolbar_stop_btn.state(["!disabled"])
            self.panel_stop_btn.state(["!disabled"])
        else:
            self.mode_badge.configure(style="IdleBadge.TLabel")
            self.toolbar_start_btn.state(["!disabled"])
            self.panel_start_btn.state(["!disabled"])
            self.toolbar_stop_btn.state(["disabled"])
            self.panel_stop_btn.state(["disabled"])

        if signal_db >= -40:
            self.signal_badge.configure(style="DangerBadge.TLabel")
        elif signal_db >= -70:
            self.signal_badge.configure(style="WarnBadge.TLabel")
        else:
            self.signal_badge.configure(style="GoodBadge.TLabel")

        scan_status = self.scanner.get_status()
        if scan_status.get("active"):
            current_raw = scan_status.get("current_freq_hz")
            start_raw = scan_status.get("start_hz")
            stop_raw = scan_status.get("stop_hz")
            current_hz = float(current_raw) if isinstance(current_raw, (int, float)) else 0.0
            start_hz = float(start_raw) if isinstance(start_raw, (int, float)) else 0.0
            stop_hz = float(stop_raw) if isinstance(stop_raw, (int, float)) else 1.0
            signal_paused = bool(scan_status.get("signal_paused"))
            self.scan_status_var.set(
                ("Paused" if signal_paused else "Scanning") +
                f" @ {current_hz / 1_000_000.0:.3f} MHz"
            )
            span = max(1.0, stop_hz - start_hz)
            progress = max(0.0, min(100.0, ((current_hz - start_hz) / span) * 100.0))
            self.scan_progress["value"] = progress
            self.scan_start_btn.state(["disabled"])
            self.scan_stop_btn.state(["!disabled"])
        else:
            self.scan_status_var.set("Idle")
            self.scan_progress["value"] = 0
            self.scan_start_btn.state(["!disabled"])
            self.scan_stop_btn.state(["disabled"])

        self._draw_meter(signal_db)
        self._update_device_drawer(status)

        morse_text = status.get("morse_text") or ""
        morse_display = str(morse_text if morse_text else "(none)")
        self.morse_var.set(morse_display)
        if hasattr(self, 'morse_output_var'):
            self.morse_output_var.set(morse_display)

    def _draw_spectrum(
        self,
        data: np.ndarray,
        min_db: float,
        max_db: float,
        center_freq_hz: float = 0.0,
        sample_rate_hz: float = 0.0,
        squelch_db: float = -120.0,
    ) -> None:
        canvas = self.spectrum_canvas
        canvas.delete("all")

        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        if data.size < 2 or width < 4 or height < 4:
            return

        for i in range(1, 5):
            y = int((height * i) / 5)
            canvas.create_line(0, y, width, y, fill="#223247")

        canvas.create_text(14, 12, text="Live Spectrum", anchor="nw", fill=self.colors["muted"], font=("Segoe UI", 9, "bold"))

        if max_db <= min_db:
            max_db = min_db + 1.0

        # Vectorised: downsample to canvas width so no sub-pixel points are drawn.
        n_pts = min(data.size, width)
        indices = np.linspace(0, data.size - 1, n_pts).astype(np.intp)
        sampled = data[indices]
        norm = np.clip(
            (sampled.astype(np.float64) - min_db) / (max_db - min_db), 0.0, 1.0
        )
        xs = np.linspace(0.0, float(width), n_pts, dtype=np.float64)
        ys = float(height) - norm * float(height)
        pts = np.empty(n_pts * 2, dtype=np.float64)
        pts[0::2] = xs
        pts[1::2] = ys
        canvas.create_line(*pts.tolist(), fill="#2ec4b6", width=2, smooth=False)

        # Squelch threshold line.
        sq_norm = (squelch_db - min_db) / (max_db - min_db)
        sq_y = int(max(0.0, min(1.0, 1.0 - sq_norm)) * height)
        canvas.create_line(0, sq_y, width, sq_y, fill=self.colors["danger"], dash=(3, 6), width=1)
        canvas.create_text(
            width - 6, sq_y - 4, text="SQ", anchor="se",
            fill=self.colors["danger"], font=("Segoe UI", 8, "bold")
        )

        # Frequency axis labels along the bottom.
        if sample_rate_hz > 0:
            lo_mhz = (center_freq_hz - sample_rate_hz / 2.0) / 1e6
            hi_mhz = (center_freq_hz + sample_rate_hz / 2.0) / 1e6
            ctr_mhz = center_freq_hz / 1e6
            y_lbl = height - 4
            canvas.create_text(4, y_lbl, text=f"{lo_mhz:.3f} MHz", anchor="sw",
                               fill=self.colors["muted"], font=("Segoe UI", 8))
            canvas.create_text(width // 2, y_lbl, text=f"{ctr_mhz:.3f} MHz", anchor="s",
                               fill=self.colors["muted"], font=("Segoe UI", 8))
            canvas.create_text(width - 4, y_lbl, text=f"{hi_mhz:.3f} MHz", anchor="se",
                               fill=self.colors["muted"], font=("Segoe UI", 8))

        self._draw_frequency_marker(canvas, width, height)

    def _draw_frequency_marker(self, canvas: tk.Canvas, width: int, height: int) -> None:
        marker_x = int(max(0, min(width - 1, self.spectrum_marker_ratio * max(1, width - 1))))
        canvas.create_line(marker_x, 0, marker_x, height, fill=self.colors["warning"], dash=(4, 4), width=1)
        canvas.create_oval(marker_x - 4, 6, marker_x + 4, 14, fill=self.colors["warning"], outline="")
        frequency_mhz = self._spectrum_frequency_hz(self.spectrum_marker_ratio) / 1_000_000.0
        label_x = marker_x + 10 if marker_x < width - 150 else marker_x - 140
        canvas.create_text(label_x, 12, text=f"Tune {frequency_mhz:.3f} MHz", anchor="nw", fill=self.colors["warning"], font=("Segoe UI", 8, "bold"))

    def _draw_meter(self, signal_db: float) -> None:
        canvas = self.meter_canvas
        canvas.delete("all")

        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        canvas.create_rectangle(0, 0, width, height, fill=self.colors["canvas"], outline="")

        normalized = (signal_db + 120.0) / 120.0
        normalized = 0.0 if normalized < 0.0 else 1.0 if normalized > 1.0 else normalized
        fill_width = int(width * normalized)

        if signal_db >= -40:
            color = self.colors["danger"]
        elif signal_db >= -70:
            color = self.colors["warning"]
        else:
            color = self.colors["accent"]

        canvas.create_rectangle(0, 0, fill_width, height, fill=color, outline="")
        canvas.create_text(10, height // 2, text=f"{signal_db:.1f} dB", anchor="w", fill=self.colors["text"], font=("Segoe UI", 9, "bold"))

    def _draw_waterfall(self, spectrum_row: np.ndarray, min_db: float, max_db: float) -> None:
        """Incremental circular-buffer waterfall: encodes only 1 new row per frame."""
        canvas = self.waterfall_canvas
        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        if width <= 1 or height <= 1 or spectrum_row.size < 2:
            return

        # The PhotoImage is 2× the canvas height so the circular buffer has no
        # seam: we write each row to two symmetric positions and position the
        # canvas item so the newest row always appears at y=0.
        photo_h = height * 2
        if (
            self.waterfall_photo is None
            or self.waterfall_photo.width() != width
            or self.waterfall_photo.height() != photo_h
        ):
            self.waterfall_photo = tk.PhotoImage(width=width, height=photo_h)
            canvas.delete("waterfall_image")
            canvas.create_image(0, 0, anchor="nw", image=self.waterfall_photo, tags="waterfall_image")  # type: ignore[attr-defined]
            self._wf_pos = height - 1

        if max_db <= min_db:
            max_db = min_db + 1.0

        # Resample the spectrum to the exact display width using one numpy index.
        indices = np.linspace(0, spectrum_row.size - 1, width).astype(np.intp)
        row_db = spectrum_row[indices]

        norm = np.clip(
            (row_db.astype(np.float32) - min_db) / (max_db - min_db), 0.0, 1.0
        )
        r = np.clip(norm * 2.0 * 255.0, 0.0, 255.0).astype(np.uint8)
        g = np.clip(np.sin(np.pi * norm) * 255.0, 0.0, 255.0).astype(np.uint8)
        inv = np.float32(1.0) - norm
        b = np.clip(inv * inv * 255.0, 0.0, 255.0).astype(np.uint8)

        # Build the single-row Tcl colour string using the pre-built LUT.
        # This is O(width) not O(width × height) — the key speedup.
        row_str = "{" + " ".join(
            "#" + _WF_HEX[int(rv)] + _WF_HEX[int(gv)] + _WF_HEX[int(bv)]
            for rv, gv, bv in zip(r.tolist(), g.tolist(), b.tolist())
        ) + "}"

        # Double-write into both halves of the circular buffer.
        self.waterfall_photo.put(row_str, to=(0, self._wf_pos))
        self.waterfall_photo.put(row_str, to=(0, self._wf_pos + height))

        # Position the canvas image so the newest row is at the visual top.
        canvas.coords("waterfall_image", 0, -self._wf_pos)

        # Advance the write pointer: decrement wraps within [0, height).
        self._wf_pos = (self._wf_pos - 1) % height


def main() -> int:
    preflight = run_startup_preflight(auto_install=True)
    print(preflight.summary())
    for warning in preflight.warnings:
        print(f"[startup] {warning}")

    root = tk.Tk()
    WaveRiderTkGui(
        root,
        startup_notice=preflight.short_notice(),
        startup_missing_required=bool(preflight.missing_required),
    )
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
