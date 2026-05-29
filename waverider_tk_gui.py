"""Native Tkinter desktop frontend for WaveRider SDR."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import numpy as np

from waverider_common import AppState, BANDS


class WaveRiderTkGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("WaveRider SDR Desktop")
        self.root.geometry("1100x760")
        self.root.minsize(900, 620)

        self.state = AppState()
        self._build_ui()
        self._schedule_update()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        controls = ttk.Frame(self.root, padding=10)
        controls.grid(row=0, column=0, sticky="ew")
        for col in range(9):
            controls.columnconfigure(col, weight=1)

        ttk.Label(controls, text="Band").grid(row=0, column=0, sticky="w")
        self.band_var = tk.StringVar(value="")
        self.band_combo = ttk.Combobox(
            controls,
            textvariable=self.band_var,
            values=[band.name for band in BANDS],
            state="readonly",
        )
        self.band_combo.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.band_combo.bind("<<ComboboxSelected>>", self._on_band_change)

        ttk.Label(controls, text="Frequency (MHz)").grid(row=0, column=1, sticky="w")
        self.freq_var = tk.StringVar(value="100.0")
        ttk.Entry(controls, textvariable=self.freq_var).grid(row=1, column=1, sticky="ew", padx=(0, 8))

        ttk.Label(controls, text="Sample Rate (Hz)").grid(row=0, column=2, sticky="w")
        self.sample_var = tk.StringVar(value="2400000")
        ttk.Combobox(
            controls,
            textvariable=self.sample_var,
            values=["2400000", "2048000", "1024000"],
            state="readonly",
        ).grid(row=1, column=2, sticky="ew", padx=(0, 8))

        ttk.Label(controls, text="FFT Size").grid(row=0, column=3, sticky="w")
        self.fft_var = tk.StringVar(value="1024")
        ttk.Combobox(
            controls,
            textvariable=self.fft_var,
            values=["512", "1024", "2048", "4096"],
            state="readonly",
        ).grid(row=1, column=3, sticky="ew", padx=(0, 8))

        ttk.Label(controls, text="Mode").grid(row=0, column=4, sticky="w")
        self.mode_var = tk.StringVar(value="None")
        ttk.Combobox(
            controls,
            textvariable=self.mode_var,
            values=["None", "AM", "FM", "USB", "LSB", "CW"],
            state="readonly",
        ).grid(row=1, column=4, sticky="ew", padx=(0, 8))

        ttk.Label(controls, text="Squelch (dB)").grid(row=0, column=5, sticky="w")
        self.squelch_var = tk.StringVar(value="-50")
        ttk.Entry(controls, textvariable=self.squelch_var).grid(row=1, column=5, sticky="ew", padx=(0, 8))

        ttk.Label(controls, text="Min dB").grid(row=0, column=6, sticky="w")
        self.min_db_var = tk.StringVar(value="-80")
        ttk.Entry(controls, textvariable=self.min_db_var).grid(row=1, column=6, sticky="ew", padx=(0, 8))

        ttk.Label(controls, text="Max dB").grid(row=0, column=7, sticky="w")
        self.max_db_var = tk.StringVar(value="0")
        ttk.Entry(controls, textvariable=self.max_db_var).grid(row=1, column=7, sticky="ew", padx=(0, 8))

        buttons = ttk.Frame(controls)
        buttons.grid(row=1, column=8, sticky="e")
        ttk.Button(buttons, text="Apply", command=self._apply_config).grid(row=0, column=0, padx=3)
        ttk.Button(buttons, text="Start", command=self._start).grid(row=0, column=1, padx=3)
        ttk.Button(buttons, text="Stop", command=self._stop).grid(row=0, column=2, padx=3)

        status = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        status.grid(row=1, column=0, sticky="ew")
        status.columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value="Stopped | Source: Simulated | Signal: -120.0 dB")
        ttk.Label(status, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

        self.notice_var = tk.StringVar(value="")
        ttk.Label(status, textvariable=self.notice_var, foreground="#a35700").grid(row=1, column=0, sticky="w")

        charts = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        charts.grid(row=2, column=0, sticky="nsew")
        charts.rowconfigure(1, weight=1)
        charts.rowconfigure(3, weight=1)
        charts.columnconfigure(0, weight=1)

        ttk.Label(charts, text="Spectrum").grid(row=0, column=0, sticky="w", pady=(6, 2))
        self.spectrum_canvas = tk.Canvas(charts, height=220, background="#0d1420", highlightthickness=1)
        self.spectrum_canvas.grid(row=1, column=0, sticky="nsew")

        ttk.Label(charts, text="Waterfall").grid(row=2, column=0, sticky="w", pady=(8, 2))
        self.waterfall_canvas = tk.Canvas(charts, height=300, background="#02060c", highlightthickness=1)
        self.waterfall_canvas.grid(row=3, column=0, sticky="nsew")

        ttk.Label(charts, text="Morse Output").grid(row=4, column=0, sticky="w", pady=(8, 2))
        self.morse_var = tk.StringVar(value="(none)")
        ttk.Label(charts, textvariable=self.morse_var).grid(row=5, column=0, sticky="w")

    def _on_band_change(self, _event: tk.Event) -> None:
        band_name = self.band_var.get()
        with self.state.lock:
            if self.state.set_band(band_name):
                self.freq_var.set(f"{self.state.center_freq / 1_000_000.0:.3f}")
                self.mode_var.set(self.state.modulation_mode)

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
            f"{'Running' if status['running'] else 'Stopped'} | "
            f"Source: {status['source']} | "
            f"Signal: {status['signal_strength_db']:.1f} dB"
        )
        self.notice_var.set(status.get("source_notice") or "")

        morse_text = status.get("morse_text") or ""
        self.morse_var.set(morse_text if morse_text else "(none)")

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

    def _draw_waterfall(self, matrix: np.ndarray, min_db: float, max_db: float) -> None:
        canvas = self.waterfall_canvas
        canvas.delete("all")

        rows, cols = matrix.shape
        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        if rows == 0 or cols == 0:
            return

        step_x = max(1, cols // 220)
        step_y = max(1, rows // 90)

        reduced = matrix[::step_y, ::step_x]
        r_rows, r_cols = reduced.shape
        if r_rows == 0 or r_cols == 0:
            return

        if max_db <= min_db:
            max_db = min_db + 1.0

        cell_w = width / r_cols
        cell_h = height / r_rows

        for y in range(r_rows):
            y0 = y * cell_h
            y1 = y0 + cell_h
            for x in range(r_cols):
                value = float(reduced[y, x])
                norm = (value - min_db) / (max_db - min_db)
                norm = 0.0 if norm < 0.0 else 1.0 if norm > 1.0 else norm

                red = int(255 * min(1.0, norm * 2.0))
                green = int(255 * np.sin(np.pi * norm))
                blue = int(255 * (1.0 - norm) * (1.0 - norm))
                color = f"#{red:02x}{green:02x}{blue:02x}"

                x0 = x * cell_w
                x1 = x0 + cell_w
                canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")


def main() -> int:
    root = tk.Tk()
    WaveRiderTkGui(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
