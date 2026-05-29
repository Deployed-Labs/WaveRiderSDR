"""Native Tkinter desktop frontend for WaveRider SDR."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import numpy as np

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
        self._build_ui()
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
            foreground=[("active", "#ffffff")],
            background=[("active", self.colors["accent_soft"])],
        )
        style.configure("TButton", padding=(10, 6))
        style.configure("TEntry", fieldbackground="#0f1726", foreground=self.colors["text"], insertcolor=self.colors["text"])
        style.configure("TCombobox", fieldbackground="#0f1726", foreground=self.colors["text"])
        style.map("TCombobox", fieldbackground=[("readonly", "#0f1726")], foreground=[("readonly", self.colors["text"])])
        style.configure("TSeparator", background=self.colors["grid"])

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        header = ttk.Frame(self.root, padding=(16, 14, 16, 8), style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)
        ttk.Label(header, text="WaveRider SDR", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Native desktop console for spectrum, waterfall, and signal control",
            style="Subtle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.mode_badge = ttk.Label(header, text="MODE: IDLE", style="PanelTitle.TLabel")
        self.mode_badge.grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))

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

        statusbar = ttk.Frame(self.root, padding=(16, 0, 16, 8), style="App.TFrame")
        statusbar.grid(row=2, column=0, sticky="ew")
        statusbar.columnconfigure(0, weight=1)
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

        self.notice_var = tk.StringVar(value="")
        ttk.Label(statusbar, textvariable=self.notice_var, style="Subtle.TLabel", foreground=self.colors["warning"]).grid(row=1, column=0, sticky="w", pady=(4, 0))

        splitter = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        splitter.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))

        controls_card = ttk.Frame(splitter, padding=14, style="Card.TFrame")
        visuals_card = ttk.Frame(splitter, padding=14, style="Panel.TFrame")
        splitter.add(controls_card, weight=1)  # type: ignore[attr-defined]
        splitter.add(visuals_card, weight=3)  # type: ignore[attr-defined]

        controls_card.columnconfigure(0, weight=1)
        controls_card.columnconfigure(1, weight=1)
        controls_card.rowconfigure(11, weight=1)

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

        advanced_toggle_row = ttk.Frame(controls_card, style="Card.TFrame")
        advanced_toggle_row.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        advanced_toggle_row.columnconfigure(0, weight=1)
        self.advanced_button = ttk.Button(advanced_toggle_row, text="Advanced ▸", command=self._toggle_advanced)
        self.advanced_button.grid(row=0, column=0, sticky="w")

        self.advanced_frame = ttk.Frame(controls_card, style="Card.TFrame")
        self.advanced_frame.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 0))
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
        meter_frame.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(12, 0))
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
        button_row.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        button_row.columnconfigure((0, 1, 2), weight=1)
        ttk.Button(button_row, text="Apply", style="Accent.TButton", command=self._apply_config).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(button_row, text="Start", style="Accent.TButton", command=self._start).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(button_row, text="Stop", style="Accent.TButton", command=self._stop).grid(row=0, column=2, sticky="ew")

        ttk.Separator(controls_card, orient=tk.HORIZONTAL).grid(row=11, column=0, columnspan=2, sticky="ew", pady=(14, 10))

        quickinfo = ttk.Frame(controls_card, style="Card.TFrame")
        quickinfo.grid(row=10, column=0, columnspan=2, sticky="nsew", pady=(14, 0))
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
            text="Center line marks the tuned frequency",
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
        self.root.bind("<Control-Return>", lambda _event: self._apply_config())
        self.root.bind("<F5>", lambda _event: self._start())
        self.root.bind("<Escape>", lambda _event: self._stop())

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

        self.status_var.set(
            f"{'Running' if status['running'] else 'Stopped'}"
        )
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
        center_x = width // 2
        canvas.create_line(center_x, 0, center_x, height, fill=self.colors["warning"], dash=(4, 4), width=1)
        canvas.create_text(center_x + 10, 12, text="Center", anchor="nw", fill=self.colors["warning"], font=("Segoe UI", 8, "bold"))

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
        blue = np.clip((1.0 - norm) * (1.0 - norm) * 255.0, 0, 255).astype(np.uint8)
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
