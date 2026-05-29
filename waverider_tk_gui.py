"""Native Tkinter desktop frontend for WaveRider SDR."""

from __future__ import annotations

import json
import pathlib
import tkinter as tk
from tkinter import ttk
from typing import cast

import numpy as np

_PRESETS_FILE = pathlib.Path(__file__).with_name("waverider_presets.json")

from waverider_common import AppState, BANDS


class WaveRiderTkGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("WaveRider SDR")
        self.root.geometry("1280x840")
        self.root.minsize(1000, 700)

        self._set_window_icon()
        self._configure_style()

        self.state = AppState()
        self.waterfall_photo: tk.PhotoImage | None = None
        self.spectrum_points: list[float] = []
        self.advanced_visible = False
        self.device_drawer_visible = False
        self.shortcuts_overlay: tk.Toplevel | None = None
        self.selected_preset_slot = 0
        self.preset_slots: list[dict[str, float | str] | None] = [None, None, None]
        self.spectrum_marker_ratio = 0.5
        self._startup_alpha = 0.0
        self._load_presets()
        self._build_ui()
        self._refresh_preset_buttons()
        self._animate_startup()
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

        ttk.Button(toolbar, text="Apply", style="Accent.TButton", command=self._apply_config).grid(row=0, column=1, padx=(8, 8), sticky="e")
        ttk.Button(toolbar, text="Start", style="Accent.TButton", command=self._start).grid(row=0, column=2, padx=(0, 8), sticky="e")
        ttk.Button(toolbar, text="Stop", style="Accent.TButton", command=self._stop).grid(row=0, column=3, sticky="e")

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

        self.status_var = tk.StringVar(value="Stopped")
        ttk.Label(badges, textvariable=self.status_var, style="Subtle.TLabel").grid(row=0, column=0, sticky="w")

        self.source_badge = ttk.Label(badges, text="SIMULATED", style="PanelTitle.TLabel")
        self.source_badge.grid(row=0, column=1, sticky="e", padx=(8, 0))
        self.signal_badge = ttk.Label(badges, text="-120.0 dB", style="PanelTitle.TLabel")
        self.signal_badge.grid(row=0, column=2, sticky="e", padx=(8, 0))
        self.rate_badge = ttk.Label(badges, text="2.4 MS/s", style="PanelTitle.TLabel")
        self.rate_badge.grid(row=0, column=3, sticky="e", padx=(8, 0))

        self.device_drawer_button = ttk.Button(statusbar, text="Device Status ▸", command=self._toggle_device_drawer)
        self.device_drawer_button.grid(row=0, column=1, sticky="e", padx=(12, 0))

        self.notice_var = tk.StringVar(value="")
        ttk.Label(status_area, textvariable=self.notice_var, style="Subtle.TLabel", foreground=self.colors["warning"]).grid(row=1, column=0, sticky="w", pady=(4, 0))

        drawer = ttk.Frame(status_area, padding=(0, 10, 0, 0), style="App.TFrame")
        drawer.grid(row=2, column=0, sticky="ew")
        drawer.columnconfigure(0, weight=1)
        drawer.columnconfigure(1, weight=1)
        self.device_drawer_frame = drawer
        self.device_drawer_frame.grid_remove()

        sdr_card = ttk.Frame(drawer, padding=12, style="Panel.TFrame")
        sdr_card.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        sdr_card.columnconfigure(0, weight=1)
        ttk.Label(sdr_card, text="SDR", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.sdr_device_var = tk.StringVar(value="Disconnected")
        self.sdr_count_var = tk.StringVar(value="Available devices: 0")
        self.sdr_error_var = tk.StringVar(value="Last error: none")
        ttk.Label(sdr_card, textvariable=self.sdr_device_var, style="Body.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(sdr_card, textvariable=self.sdr_count_var, style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(4, 0))
        ttk.Label(sdr_card, textvariable=self.sdr_error_var, style="Muted.TLabel", wraplength=360, justify="left").grid(row=3, column=0, sticky="w", pady=(4, 0))

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
        controls_card.columnconfigure(1, weight=1)
        controls_card.rowconfigure(13, weight=1)

        ttk.Label(controls_card, text="Control Panel", style="PanelTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(controls_card, text="Band", style="Body.TLabel").grid(row=1, column=0, sticky="w")
        self.band_var = tk.StringVar(value="")
        self.band_combo = ttk.Combobox(
            controls_card,
            textvariable=self.band_var,
            values=[band.name for band in BANDS],
            state="readonly",
        )
        self.band_combo.grid(row=2, column=0, sticky="ew", padx=(0, 8), pady=(2, 10))
        self.band_combo.bind("<<ComboboxSelected>>", self._on_band_change)

        ttk.Label(controls_card, text="Frequency (MHz)", style="Body.TLabel").grid(row=1, column=1, sticky="w")
        self.freq_var = tk.StringVar(value="100.0")
        ttk.Entry(controls_card, textvariable=self.freq_var).grid(row=2, column=1, sticky="ew", padx=(0, 8), pady=(2, 10))

        ttk.Label(controls_card, text="Sample Rate (Hz)", style="Body.TLabel").grid(row=3, column=0, sticky="w")
        self.sample_var = tk.StringVar(value="2400000")
        ttk.Combobox(
            controls_card,
            textvariable=self.sample_var,
            values=["2400000", "2048000", "1024000"],
            state="readonly",
        ).grid(row=4, column=0, sticky="ew", padx=(0, 8), pady=(2, 10))

        ttk.Label(controls_card, text="FFT Size", style="Body.TLabel").grid(row=3, column=1, sticky="w")
        self.fft_var = tk.StringVar(value="1024")
        ttk.Combobox(
            controls_card,
            textvariable=self.fft_var,
            values=["512", "1024", "2048", "4096"],
            state="readonly",
        ).grid(row=4, column=1, sticky="ew", padx=(0, 8), pady=(2, 10))

        ttk.Label(controls_card, text="Mode", style="Body.TLabel").grid(row=5, column=0, sticky="w")
        self.mode_var = tk.StringVar(value="None")
        ttk.Combobox(
            controls_card,
            textvariable=self.mode_var,
            values=["None", "AM", "FM", "USB", "LSB", "CW"],
            state="readonly",
        ).grid(row=6, column=0, sticky="ew", padx=(0, 8), pady=(2, 10))

        preset_memory = ttk.Frame(controls_card, style="Card.TFrame")
        preset_memory.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        preset_memory.columnconfigure(0, weight=1)
        ttk.Label(preset_memory, text="Preset Memory", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        preset_slots_row = ttk.Frame(preset_memory, style="Card.TFrame")
        preset_slots_row.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        preset_slots_row.columnconfigure((0, 1, 2, 3), weight=1)
        self.preset_buttons: list[ttk.Button] = []
        for index in range(3):
            button = ttk.Button(preset_slots_row, text=f"{index + 1} Empty", command=lambda slot=index: self._recall_preset(slot))
            button.grid(row=0, column=index, sticky="ew", padx=(0, 8))
            self.preset_buttons.append(button)
        ttk.Button(preset_slots_row, text="Store Current", command=self._store_current_preset).grid(row=0, column=3, sticky="ew")
        ttk.Label(
            preset_memory,
            text="Ctrl+1..3 recalls a slot. Shift+Ctrl+1..3 stores the current frequency and mode.",
            style="Muted.TLabel",
            wraplength=340,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(6, 0))

        advanced_toggle_row = ttk.Frame(controls_card, style="Card.TFrame")
        advanced_toggle_row.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        advanced_toggle_row.columnconfigure(0, weight=1)
        self.advanced_button = ttk.Button(advanced_toggle_row, text="Advanced ▸", command=self._toggle_advanced)
        self.advanced_button.grid(row=0, column=0, sticky="w")

        self.advanced_frame = ttk.Frame(controls_card, style="Card.TFrame")
        self.advanced_frame.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.advanced_frame.columnconfigure(0, weight=1)
        self.advanced_frame.columnconfigure(1, weight=1)
        self.advanced_frame.grid_remove()

        ttk.Label(self.advanced_frame, text="Squelch (dB)", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        self.squelch_var = tk.StringVar(value="-50")
        ttk.Entry(self.advanced_frame, textvariable=self.squelch_var).grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(2, 10))

        ttk.Label(self.advanced_frame, text="Min dB", style="Body.TLabel").grid(row=0, column=1, sticky="w")
        self.min_db_var = tk.StringVar(value="-80")
        ttk.Entry(self.advanced_frame, textvariable=self.min_db_var).grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(2, 10))

        ttk.Label(self.advanced_frame, text="Max dB", style="Body.TLabel").grid(row=2, column=0, sticky="w")
        self.max_db_var = tk.StringVar(value="0")
        ttk.Entry(self.advanced_frame, textvariable=self.max_db_var).grid(row=3, column=0, sticky="ew", padx=(0, 8), pady=(2, 10))

        meter_frame = ttk.Frame(controls_card, style="Card.TFrame")
        meter_frame.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(12, 0))
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

        button_row = ttk.Frame(controls_card, style="Card.TFrame")
        button_row.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        button_row.columnconfigure((0, 1, 2), weight=1)
        ttk.Button(button_row, text="Apply", style="Accent.TButton", command=self._apply_config).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(button_row, text="Start", style="Accent.TButton", command=self._start).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(button_row, text="Stop", style="Accent.TButton", command=self._stop).grid(row=0, column=2, sticky="ew")

        ttk.Separator(controls_card, orient=tk.HORIZONTAL).grid(row=12, column=0, columnspan=2, sticky="ew", pady=(14, 10))

        quickinfo = ttk.Frame(controls_card, style="Card.TFrame")
        quickinfo.grid(row=13, column=0, columnspan=2, sticky="nsew", pady=(0, 0))
        quickinfo.columnconfigure(0, weight=1)
        ttk.Label(quickinfo, text="Operating Notes", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            quickinfo,
            text="Use Apply after changing frequency or FFT size. Start pauses updates when you need a static view.",
            style="Muted.TLabel",
            wraplength=300,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

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

        ttk.Label(visuals_card, text="Waterfall", style="PanelTitle.TLabel").grid(row=2, column=0, sticky="w", pady=(12, 8))
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
        except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            pass

    def _save_presets(self) -> None:
        slots: list[dict[str, float | str] | None] = []
        for preset in self.preset_slots:
            if preset is None:
                slots.append(None)
            else:
                slots.append({"frequency_mhz": float(preset["frequency_mhz"]), "mode": str(preset["mode"])})
        try:
            _PRESETS_FILE.write_text(json.dumps({"presets": slots}, indent=2), encoding="utf-8")
        except OSError:
            pass

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

    def _toggle_device_drawer(self) -> None:
        self.device_drawer_visible = not self.device_drawer_visible
        if self.device_drawer_visible:
            self.device_drawer_frame.grid()
            self.device_drawer_button.configure(text="Device Status ▾")
        else:
            self.device_drawer_frame.grid_remove()
            self.device_drawer_button.configure(text="Device Status ▸")

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

    def _on_band_change(self, _event: tk.Event) -> None:
        band_name = self.band_var.get()
        with self.state.lock:
            if self.state.set_band(band_name):
                self.freq_var.set(f"{self.state.center_freq / 1_000_000.0:.3f}")
                self.mode_var.set(self.state.modulation_mode)

    def _toggle_advanced(self) -> None:
        self.advanced_visible = not self.advanced_visible
        if self.advanced_visible:
            self.advanced_frame.grid()
            self.advanced_button.configure(text="Advanced ▾")
        else:
            self.advanced_frame.grid_remove()
            self.advanced_button.configure(text="Advanced ▸")

    def _apply_view_preset(self, preset: str) -> None:
        if preset == "wide":
            self.root.geometry("1440x820")
        elif preset == "waterfall":
            self.root.geometry("1240x920")
        else:
            self.root.geometry("1280x840")

    def _start(self) -> None:
        with self.state.lock:
            self.state.start()

    def _stop(self) -> None:
        with self.state.lock:
            self.state.stop()

    def _apply_config(self) -> None:
        try:
            frequency_mhz = float(self.freq_var.get())
            sample_rate = float(self.sample_var.get())
            fft_size = int(self.fft_var.get())
            squelch = float(self.squelch_var.get())
            min_db = float(self.min_db_var.get())
            max_db = float(self.max_db_var.get())
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
            )
        self.notice_var.set("")

    def _schedule_update(self) -> None:
        self._update_frame()
        self.root.after(120, self._schedule_update)

    def _update_frame(self) -> None:
        with self.state.lock:
            if self.state.running:
                self.state.tick()
            waveform = self.state.waveform_data.copy()
            waterfall = self.state.waterfall_data.copy()
            status = self.state.get_status()
            min_db = self.state.waterfall_settings.min_db
            max_db = self.state.waterfall_settings.max_db

        self._draw_spectrum(waveform, min_db, max_db)
        self._draw_waterfall(waterfall, min_db, max_db)

        self.status_var.set(f"{'Running' if status['running'] else 'Stopped'}")
        self.notice_var.set(str(status.get("source_notice") or ""))

        self.mode_badge.configure(text=f"MODE: {str(status.get('modulation_mode') or 'NONE').upper()}")
        self.source_badge.configure(text=str(status.get("source") or "SIMULATED").upper())
        self.signal_badge.configure(text=f"{status['signal_strength_db']:.1f} dB")
        sample_rate_value = status.get("sample_rate")
        sample_rate_hz = sample_rate_value if isinstance(sample_rate_value, (int, float)) else 0.0
        self.rate_badge.configure(text=f"{sample_rate_hz / 1_000_000.0:.1f} MS/s")
        signal_value = status.get("signal_strength_db")
        signal_db = signal_value if isinstance(signal_value, (int, float)) else -120.0
        self._draw_meter(signal_db)
        self._update_device_drawer(status)

        morse_text = status.get("morse_text") or ""
        self.morse_var.set(str(morse_text if morse_text else "(none)"))

    def _draw_spectrum(self, data: np.ndarray, min_db: float, max_db: float) -> None:
        canvas = self.spectrum_canvas
        canvas.delete("all")

        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        if data.size < 2:
            return

        for i in range(1, 5):
            y = int((height * i) / 5)
            canvas.create_line(0, y, width, y, fill="#223247")

        canvas.create_text(14, 12, text="Live Spectrum", anchor="nw", fill=self.colors["muted"], font=("Segoe UI", 9, "bold"))

        if max_db <= min_db:
            max_db = min_db + 1.0

        points: list[float] = []
        size = data.size
        for i, value in enumerate(data):
            x = (i / (size - 1)) * width
            norm = (float(value) - min_db) / (max_db - min_db)
            norm = 0.0 if norm < 0.0 else 1.0 if norm > 1.0 else norm
            y = height - (norm * height)
            points.extend((x, y))

        canvas.create_line(*points, fill="#2ec4b6", width=2, smooth=False)
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

    def _draw_waterfall(self, matrix: np.ndarray, min_db: float, max_db: float) -> None:
        canvas = self.waterfall_canvas
        rows, cols = matrix.shape
        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        if rows == 0 or cols == 0 or width <= 1 or height <= 1:
            return

        step_x = max(1, cols // max(240, width // 4))
        step_y = max(1, rows // max(120, height // 4))

        reduced = matrix[::step_y, ::step_x]
        r_rows, r_cols = reduced.shape
        if r_rows == 0 or r_cols == 0:
            return

        if max_db <= min_db:
            max_db = min_db + 1.0

        resized = np.repeat(reduced, max(1, height // r_rows), axis=0)
        resized = np.repeat(resized, max(1, width // r_cols), axis=1)
        resized = resized[:height, :width]

        norm = (resized - min_db) / (max_db - min_db)
        norm = np.clip(norm, 0.0, 1.0)

        red = np.clip((norm * 2.0) * 255.0, 0, 255).astype(np.uint8)
        green = np.clip(np.sin(np.pi * norm) * 255.0, 0, 255).astype(np.uint8)
        blue = np.clip((1.0 - norm) * (1.0 - norm) * 255.0, 0, 255).astype(np.uint8)  # type: ignore[operator]
        rgb = np.stack((red, green, blue), axis=-1)

        lines: list[str] = []
        for row in rgb:
            row_colors: str = "{" + " ".join(f"#{int(pixel[0]):02x}{int(pixel[1]):02x}{int(pixel[2]):02x}" for pixel in row) + "}"
            lines.append(row_colors)

        if self.waterfall_photo is None or self.waterfall_photo.width() != width or self.waterfall_photo.height() != height:
            self.waterfall_photo = tk.PhotoImage(width=width, height=height)
            canvas.delete("waterfall_image")
            canvas.create_image(0, 0, anchor="nw", image=self.waterfall_photo, tags="waterfall_image")  # type: ignore[attr-defined]

        self.waterfall_photo.put(" ".join(lines), to=(0, 0))


def main() -> int:
    root = tk.Tk()
    WaveRiderTkGui(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
