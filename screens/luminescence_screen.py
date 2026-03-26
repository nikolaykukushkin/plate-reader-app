"""
Screen 3: Luminescence assay verification.
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Callable

from parsing.luminescence_parser import detect_luminescence_grid, parse_luminescence_grid
from widgets.grid_selector import GridSelectorDialog


class LuminescenceScreen(ttk.Frame):
    """Third screen: Luminescence grid verification."""

    def __init__(self, parent, data_model, on_next: Callable, on_back: Callable):
        super().__init__(parent)
        self.data_model = data_model
        self.on_next = on_next
        self.on_back = on_back

        self._create_widgets()
        self._auto_detect_luminescence()

    def _create_widgets(self):
        """Create and layout widgets."""
        # Title
        title = ttk.Label(self, text="Luminescence Assay Verification", font=('Helvetica', 14, 'bold'))
        title.pack(pady=10)

        # Main content frame with two columns
        content_frame = ttk.Frame(self)
        content_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Left column: Original grid
        left_frame = ttk.LabelFrame(content_frame, text="Original Grid", padding=10)
        left_frame.pack(side='left', padx=5, fill='both', expand=True)

        self.original_text = scrolledtext.ScrolledText(left_frame, width=40, height=20, font=('Courier', 9))
        self.original_text.pack(fill='both', expand=True)

        # Right column: Parsed column
        right_frame = ttk.LabelFrame(content_frame, text="Parsed Samples", padding=10)
        right_frame.pack(side='left', padx=5, fill='both', expand=True)

        self.parsed_text = scrolledtext.ScrolledText(right_frame, width=40, height=20, font=('Courier', 9))
        self.parsed_text.pack(fill='both', expand=True)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Manual Selection", command=self._manual_selection).pack(side='left', padx=5)
        ttk.Button(button_frame, text="← Back", command=self.on_back).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Next →", command=self._on_next_clicked).pack(side='left', padx=5)

    def _auto_detect_luminescence(self):
        """Auto-detect and parse luminescence grid."""
        if self.data_model.raw_dataframe is None:
            return

        try:
            # Detect grid
            result = detect_luminescence_grid(
                self.data_model.raw_dataframe,
                self.data_model.num_samples,
                self.data_model.bradford_raw_bounds
            )

            if result is None:
                messagebox.showwarning("Warning",
                                       "Could not auto-detect luminescence grid. Please use Manual Selection.")
                return

            grid, bounds = result
            self.data_model.luminescence_raw_grid = grid
            self.data_model.luminescence_raw_bounds = bounds

            # Display original grid
            self._display_original_grid()

            # Parse grid
            self._parse_luminescence()

        except Exception as e:
            messagebox.showerror("Error", f"Error detecting luminescence grid: {str(e)}")

    def _parse_luminescence(self):
        """Parse luminescence grid."""
        if self.data_model.luminescence_raw_grid is None:
            return

        try:
            samples = parse_luminescence_grid(
                self.data_model.luminescence_raw_grid,
                self.data_model.num_samples
            )

            self.data_model.luminescence_samples = samples

            # Display parsed samples
            self._display_parsed_samples()

        except Exception as e:
            messagebox.showerror("Error", f"Error parsing luminescence grid: {str(e)}")

    def _display_original_grid(self):
        """Display the original luminescence grid."""
        self.original_text.delete('1.0', tk.END)
        grid = self.data_model.luminescence_raw_grid

        for row in grid:
            row_str = "  ".join([f"{val:8.0f}" for val in row])
            self.original_text.insert(tk.END, row_str + "\n")

    def _display_parsed_samples(self):
        """Display the parsed luminescence samples."""
        self.parsed_text.delete('1.0', tk.END)

        samples = self.data_model.luminescence_samples

        self.parsed_text.insert(tk.END, "LUMINESCENCE SAMPLES:\n\n", 'bold')

        for i, value in enumerate(samples):
            sample_str = f"Sample {i+1:2d}:  {value:10.0f} RLU\n"
            self.parsed_text.insert(tk.END, sample_str)

        # Configure tag for bold
        self.parsed_text.tag_config('bold', font=('Courier', 9, 'bold'))

    def _manual_selection(self):
        """Open manual grid selection dialog."""
        if self.data_model.raw_dataframe is None:
            messagebox.showwarning("Warning", "No data loaded. Please upload a file first.")
            return

        dialog = GridSelectorDialog(
            self, self.data_model.raw_dataframe, title="Select Luminescence Grid Region"
        )

        if dialog.result is not None:
            grid, bounds = dialog.result
            self.data_model.luminescence_raw_grid = grid
            self.data_model.luminescence_raw_bounds = bounds
            self._display_original_grid()
            self._parse_luminescence()

    def _on_next_clicked(self):
        """Handle next button click."""
        # Validate that we have data
        if self.data_model.luminescence_samples is None:
            messagebox.showwarning("Warning", "Please ensure luminescence grid is properly parsed.")
            return

        # Check that we have the right number of samples
        if len(self.data_model.luminescence_samples) != self.data_model.num_samples:
            messagebox.showwarning("Warning",
                                   f"Expected {self.data_model.num_samples} samples, "
                                   f"but found {len(self.data_model.luminescence_samples)}.")
            return

        # Proceed to next screen
        self.on_next()
