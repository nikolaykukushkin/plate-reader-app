"""
Interactive grid selector dialog for manual cell selection.

Displays the raw dataframe in a scrollable grid and lets users
click-and-drag to select a rectangular region of numeric cells.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Tuple

import numpy as np
import pandas as pd


class GridSelectorDialog(tk.Toplevel):
    """Modal dialog that shows a spreadsheet grid and returns a rectangular selection."""

    # Appearance
    CELL_WIDTH = 72
    CELL_HEIGHT = 24
    FONT = ("Courier", 9)
    COLOR_DEFAULT = "#ffffff"
    COLOR_HOVER = "#e0e8f0"
    COLOR_SELECTED = "#4a90d9"
    COLOR_SELECTED_FG = "#ffffff"
    COLOR_NON_NUMERIC = "#f0f0f0"
    COLOR_HEADER_BG = "#d0d0d0"

    def __init__(
        self,
        parent: tk.Widget,
        dataframe: pd.DataFrame,
        title: str = "Select Grid Region",
    ):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()

        self.df = dataframe
        self.n_rows, self.n_cols = dataframe.shape

        # Selection state (row/col indices into self.df, inclusive)
        self._anchor: Optional[Tuple[int, int]] = None
        self._sel_start: Optional[Tuple[int, int]] = None
        self._sel_end: Optional[Tuple[int, int]] = None

        # Result – set when user confirms
        self.result: Optional[Tuple[np.ndarray, Tuple[int, int, int, int]]] = None

        self._build_ui()
        self._draw_grid()
        self._center_on_parent(parent)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.wait_window()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Info label
        info = ttk.Label(
            self,
            text="Click and drag to select a rectangular region of cells.",
        )
        info.pack(padx=10, pady=(10, 4))

        self._selection_label = ttk.Label(self, text="No selection")
        self._selection_label.pack(padx=10)

        # Scrollable canvas
        container = ttk.Frame(self)
        container.pack(padx=10, pady=6, fill="both", expand=True)

        self._canvas = tk.Canvas(container, bg="white")
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=self._canvas.xview)
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        h_scroll.pack(side="bottom", fill="x")
        v_scroll.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=(4, 10))
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side="left", padx=5)

        # Window sizing – aim for a reasonable default
        width = min(900, self.CELL_WIDTH * (self.n_cols + 1) + 40)
        height = min(600, self.CELL_HEIGHT * (self.n_rows + 1) + 140)
        self.geometry(f"{width}x{height}")

    def _center_on_parent(self, parent: tk.Widget):
        self.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w = self.winfo_width()
        h = self.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # Grid drawing
    # ------------------------------------------------------------------

    def _is_numeric(self, value) -> bool:
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def _draw_grid(self):
        canvas = self._canvas
        cw, ch = self.CELL_WIDTH, self.CELL_HEIGHT

        total_w = cw * (self.n_cols + 1)  # +1 for row-header column
        total_h = ch * (self.n_rows + 1)  # +1 for col-header row
        canvas.configure(scrollregion=(0, 0, total_w, total_h))

        self._cell_rects: dict[Tuple[int, int], int] = {}
        self._cell_texts: dict[Tuple[int, int], int] = {}

        # Column headers
        for c in range(self.n_cols):
            x0 = cw * (c + 1)
            canvas.create_rectangle(x0, 0, x0 + cw, ch, fill=self.COLOR_HEADER_BG, outline="gray")
            canvas.create_text(x0 + cw // 2, ch // 2, text=str(c), font=self.FONT)

        # Row headers + data cells
        data = self.df.values
        for r in range(self.n_rows):
            y0 = ch * (r + 1)
            # Row header
            canvas.create_rectangle(0, y0, cw, y0 + ch, fill=self.COLOR_HEADER_BG, outline="gray")
            canvas.create_text(cw // 2, y0 + ch // 2, text=str(r), font=self.FONT)

            for c in range(self.n_cols):
                x0 = cw * (c + 1)
                val = data[r][c]
                numeric = self._is_numeric(val)
                bg = self.COLOR_DEFAULT if numeric else self.COLOR_NON_NUMERIC

                rect_id = canvas.create_rectangle(
                    x0, y0, x0 + cw, y0 + ch, fill=bg, outline="gray"
                )
                display = ""
                if numeric:
                    fv = float(val)
                    display = f"{fv:.4g}" if abs(fv) < 10000 else f"{fv:.2e}"
                else:
                    display = str(val)[:8] if val is not None and str(val) != "nan" else ""

                text_id = canvas.create_text(
                    x0 + cw // 2, y0 + ch // 2, text=display, font=self.FONT
                )
                self._cell_rects[(r, c)] = rect_id
                self._cell_texts[(r, c)] = text_id

    # ------------------------------------------------------------------
    # Selection helpers
    # ------------------------------------------------------------------

    def _canvas_to_cell(self, event) -> Optional[Tuple[int, int]]:
        """Convert canvas coordinates to (row, col) or None."""
        cx = self._canvas.canvasx(event.x)
        cy = self._canvas.canvasy(event.y)
        col = int(cx // self.CELL_WIDTH) - 1  # subtract header column
        row = int(cy // self.CELL_HEIGHT) - 1  # subtract header row
        if 0 <= row < self.n_rows and 0 <= col < self.n_cols:
            return (row, col)
        return None

    def _update_highlight(self):
        """Redraw selection highlighting."""
        canvas = self._canvas
        sel_cells = self._selected_cells()
        data = self.df.values

        for (r, c), rect_id in self._cell_rects.items():
            text_id = self._cell_texts[(r, c)]
            if (r, c) in sel_cells:
                canvas.itemconfigure(rect_id, fill=self.COLOR_SELECTED)
                canvas.itemconfigure(text_id, fill=self.COLOR_SELECTED_FG)
            else:
                numeric = self._is_numeric(data[r][c])
                bg = self.COLOR_DEFAULT if numeric else self.COLOR_NON_NUMERIC
                canvas.itemconfigure(rect_id, fill=bg)
                canvas.itemconfigure(text_id, fill="black")

        # Update label
        if self._sel_start and self._sel_end:
            r1, c1 = self._sel_start
            r2, c2 = self._sel_end
            n = (r2 - r1 + 1) * (c2 - c1 + 1)
            self._selection_label.config(
                text=f"Selection: rows {r1}\u2013{r2}, cols {c1}\u2013{c2}  ({n} cells)"
            )
        else:
            self._selection_label.config(text="No selection")

    def _selected_cells(self) -> set:
        if self._sel_start is None or self._sel_end is None:
            return set()
        r1, c1 = self._sel_start
        r2, c2 = self._sel_end
        return {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}

    # ------------------------------------------------------------------
    # Mouse events
    # ------------------------------------------------------------------

    def _on_press(self, event):
        cell = self._canvas_to_cell(event)
        if cell is None:
            return
        self._anchor = cell
        self._sel_start = cell
        self._sel_end = cell
        self._update_highlight()

    def _on_drag(self, event):
        if self._anchor is None:
            return
        cell = self._canvas_to_cell(event)
        if cell is None:
            return
        ar, ac = self._anchor
        r, c = cell
        self._sel_start = (min(ar, r), min(ac, c))
        self._sel_end = (max(ar, r), max(ac, c))
        self._update_highlight()

    def _on_release(self, event):
        pass  # selection is already updated in _on_drag

    # ------------------------------------------------------------------
    # OK / Cancel
    # ------------------------------------------------------------------

    def _on_ok(self):
        if self._sel_start is None or self._sel_end is None:
            messagebox.showwarning("No Selection", "Please select a region first.", parent=self)
            return

        r1, c1 = self._sel_start
        r2, c2 = self._sel_end

        # Extract numeric values from the selected region
        data = self.df.values
        rows = r2 - r1 + 1
        cols = c2 - c1 + 1
        grid = np.full((rows, cols), np.nan)
        non_numeric_count = 0

        for r in range(rows):
            for c in range(cols):
                val = data[r1 + r][c1 + c]
                try:
                    grid[r, c] = float(val)
                except (ValueError, TypeError):
                    non_numeric_count += 1

        if non_numeric_count > 0:
            proceed = messagebox.askyesno(
                "Non-numeric cells",
                f"Selection contains {non_numeric_count} non-numeric cell(s) "
                f"(will be treated as NaN). Continue?",
                parent=self,
            )
            if not proceed:
                return

        # bounds: (row_start, row_end, col_start, col_end) with exclusive end
        bounds = (r1, r2 + 1, c1, c2 + 1)
        self.result = (grid, bounds)
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()
