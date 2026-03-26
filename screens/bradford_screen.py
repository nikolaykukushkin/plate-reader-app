"""
Screen 2: Bradford assay verification and configuration.
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Callable
import numpy as np

from parsing.bradford_parser import detect_bradford_grid, parse_bradford_grid
from widgets.grid_selector import GridSelectorDialog


class BradfordScreen(ttk.Frame):
    """Second screen: Bradford grid verification."""

    def __init__(self, parent, data_model, on_next: Callable, on_back: Callable):
        super().__init__(parent)
        self.data_model = data_model
        self.on_next = on_next
        self.on_back = on_back

        self._create_widgets()
        self._auto_detect_bradford()

    def _create_widgets(self):
        """Create and layout widgets."""
        # Title
        title = ttk.Label(self, text="Bradford Assay Configuration", font=('Helvetica', 14, 'bold'))
        title.pack(pady=10)

        # Main content frame with two columns
        content_frame = ttk.Frame(self)
        content_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Left column: Original grid
        left_frame = ttk.LabelFrame(content_frame, text="Original Grid", padding=10)
        left_frame.pack(side='left', padx=5, fill='both', expand=True)

        self.original_text = scrolledtext.ScrolledText(left_frame, width=40, height=15, font=('Courier', 9))
        self.original_text.pack(fill='both', expand=True)

        # Right column: Parsed grid
        right_frame = ttk.LabelFrame(content_frame, text="Parsed Grid", padding=10)
        right_frame.pack(side='left', padx=5, fill='both', expand=True)

        self.parsed_text = scrolledtext.ScrolledText(right_frame, width=40, height=15, font=('Courier', 9))
        self.parsed_text.pack(fill='both', expand=True)

        # Configuration frame
        config_frame = ttk.LabelFrame(self, text="Configuration", padding=10)
        config_frame.pack(padx=20, pady=10, fill='x')

        # Replicates
        row = 0
        ttk.Label(config_frame, text="Standard replicates:").grid(row=row, column=0, sticky='w', padx=5)
        self.std_replicates_var = tk.IntVar(value=3)
        std_rep_combo = ttk.Combobox(config_frame, textvariable=self.std_replicates_var,
                                      values=[1, 2, 3], width=5, state='readonly')
        std_rep_combo.grid(row=row, column=1, sticky='w', padx=5)
        std_rep_combo.bind('<<ComboboxSelected>>', lambda e: self._reparse_bradford())

        ttk.Label(config_frame, text="Sample replicates:").grid(row=row, column=2, sticky='w', padx=5)
        self.sample_replicates_var = tk.IntVar(value=3)
        sample_rep_combo = ttk.Combobox(config_frame, textvariable=self.sample_replicates_var,
                                         values=[1, 2, 3], width=5, state='readonly')
        sample_rep_combo.grid(row=row, column=3, sticky='w', padx=5)
        sample_rep_combo.bind('<<ComboboxSelected>>', lambda e: self._reparse_bradford())

        # Bradford standards (editable)
        row += 1
        ttk.Label(config_frame, text="Bradford Standards (mg/ml):", font=('Helvetica', 10, 'bold')).grid(
            row=row, column=0, columnspan=4, sticky='w', pady=(10, 5))

        # Create entry fields for standards
        self.standard_vars = []
        for i in range(8):
            row += 1
            ttk.Label(config_frame, text=f"Standard {i+1}:").grid(row=row, column=i % 4 * 2, sticky='w', padx=5)
            var = tk.DoubleVar(value=self.data_model.standard_concentrations[i])
            entry = ttk.Entry(config_frame, textvariable=var, width=8)
            entry.grid(row=row, column=i % 4 * 2 + 1, sticky='w', padx=5)
            self.standard_vars.append(var)
            if i == 3:
                row += 1  # Move to next row after 4 standards

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Manual Selection", command=self._manual_selection).pack(side='left', padx=5)
        ttk.Button(button_frame, text="← Back", command=self.on_back).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Next →", command=self._on_next_clicked).pack(side='left', padx=5)

    def _auto_detect_bradford(self):
        """Auto-detect and parse Bradford grid."""
        if self.data_model.raw_dataframe is None:
            return

        try:
            # Detect grid
            result = detect_bradford_grid(self.data_model.raw_dataframe)
            if result is None:
                messagebox.showwarning("Warning",
                                       "Could not auto-detect Bradford grid. Please use Manual Selection.")
                return

            grid, bounds = result
            self.data_model.bradford_raw_grid = grid
            self.data_model.bradford_raw_bounds = bounds

            # Display original grid
            self._display_original_grid()

            # Parse grid
            self._reparse_bradford()

        except Exception as e:
            messagebox.showerror("Error", f"Error detecting Bradford grid: {str(e)}")

    def _reparse_bradford(self):
        """Re-parse Bradford grid with current settings."""
        if self.data_model.bradford_raw_grid is None:
            return

        try:
            std_reps = self.std_replicates_var.get()
            sample_reps = self.sample_replicates_var.get()

            standards, samples = parse_bradford_grid(
                self.data_model.bradford_raw_grid,
                self.data_model.num_samples,
                std_reps,
                sample_reps
            )

            self.data_model.bradford_standards = standards
            self.data_model.bradford_samples = samples
            self.data_model.standard_replicates = std_reps
            self.data_model.sample_replicates = sample_reps

            # Display parsed grid
            self._display_parsed_grid()

        except Exception as e:
            messagebox.showerror("Error", f"Error parsing Bradford grid: {str(e)}")

    def _display_original_grid(self):
        """Display the original Bradford grid."""
        self.original_text.delete('1.0', tk.END)
        grid = self.data_model.bradford_raw_grid

        for row in grid:
            row_str = "  ".join([f"{val:7.4f}" for val in row])
            self.original_text.insert(tk.END, row_str + "\n")

    def _display_parsed_grid(self):
        """Display the parsed Bradford grid with labels."""
        self.parsed_text.delete('1.0', tk.END)

        standards = self.data_model.bradford_standards
        samples = self.data_model.bradford_samples

        # Display standards
        self.parsed_text.insert(tk.END, "STANDARDS:\n", 'bold')
        for i, std_row in enumerate(standards):
            conc = self.standard_vars[i].get()
            row_str = f"Std {i+1} ({conc} mg/ml):  "
            row_str += "  ".join([f"{val:7.4f}" for val in std_row])
            row_str += f"  →  Mean: {np.mean(std_row):.4f}\n"
            self.parsed_text.insert(tk.END, row_str)

        # Display samples
        self.parsed_text.insert(tk.END, "\nSAMPLES:\n", 'bold')
        for i, sample_row in enumerate(samples):
            row_str = f"Sample {i+1:2d}:  "
            row_str += "  ".join([f"{val:7.4f}" for val in sample_row])
            row_str += f"  →  Mean: {np.mean(sample_row):.4f}\n"
            self.parsed_text.insert(tk.END, row_str)

        # Configure tag for bold
        self.parsed_text.tag_config('bold', font=('Courier', 9, 'bold'))

    def _manual_selection(self):
        """Open manual grid selection dialog."""
        if self.data_model.raw_dataframe is None:
            messagebox.showwarning("Warning", "No data loaded. Please upload a file first.")
            return

        dialog = GridSelectorDialog(
            self, self.data_model.raw_dataframe, title="Select Bradford Grid Region"
        )

        if dialog.result is not None:
            grid, bounds = dialog.result
            self.data_model.bradford_raw_grid = grid
            self.data_model.bradford_raw_bounds = bounds
            self._display_original_grid()
            self._reparse_bradford()

    def _on_next_clicked(self):
        """Handle next button click."""
        # Update standard concentrations from entry fields
        self.data_model.standard_concentrations = [var.get() for var in self.standard_vars]

        # Validate that we have data
        if self.data_model.bradford_standards is None or self.data_model.bradford_samples is None:
            messagebox.showwarning("Warning", "Please ensure Bradford grid is properly parsed.")
            return

        # Proceed to next screen
        self.on_next()
