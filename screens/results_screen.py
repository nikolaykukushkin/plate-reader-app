"""
Screen 4: Results display and Excel export.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable
import numpy as np
import pandas as pd
from datetime import datetime
import os

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from analysis.calculations import calculate_protein_concentrations, format_equation
from parsing.file_reader import save_to_excel


class ResultsScreen(ttk.Frame):
    """Fourth screen: Results and export."""

    def __init__(self, parent, data_model, on_back: Callable):
        super().__init__(parent)
        self.data_model = data_model
        self.on_back = on_back

        self._calculate_results()
        self._create_widgets()
        self._display_results()

    def _calculate_results(self):
        """Calculate protein concentrations and specific luminescence."""
        try:
            protein_conc, specific_lumi, curve_params = calculate_protein_concentrations(
                self.data_model.bradford_samples,
                self.data_model.bradford_standards,
                np.array(self.data_model.standard_concentrations),
                self.data_model.luminescence_samples
            )

            self.data_model.protein_concentrations = protein_conc
            self.data_model.specific_luminescence = specific_lumi
            self.data_model.standard_curve_params = curve_params

        except Exception as e:
            messagebox.showerror("Error", f"Error calculating results: {str(e)}")

    def _create_widgets(self):
        """Create and layout widgets."""
        # Title
        title = ttk.Label(self, text="Results", font=('Helvetica', 14, 'bold'))
        title.pack(pady=10)

        # Main content frame
        content_frame = ttk.Frame(self)
        content_frame.pack(padx=10, pady=5, fill='both', expand=True)

        # Top section: Standard curve plot
        plot_frame = ttk.LabelFrame(content_frame, text="Standard Curve", padding=10)
        plot_frame.pack(fill='x', padx=5, pady=5)

        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # Warning label (if R² is poor)
        self.warning_label = ttk.Label(content_frame, text="", foreground='red', font=('Helvetica', 10, 'bold'))
        self.warning_label.pack()

        # Bottom section: Results table
        table_frame = ttk.LabelFrame(content_frame, text="Sample Results", padding=10)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create scrollable frame for table
        table_scroll_frame = ttk.Frame(table_frame)
        table_scroll_frame.pack(fill='both', expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_scroll_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        # Canvas for scrolling
        canvas = tk.Canvas(table_scroll_frame, yscrollcommand=scrollbar.set, height=200)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=canvas.yview)

        # Frame inside canvas
        self.table_inner_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.table_inner_frame, anchor='nw')

        # Create table headers
        headers = ["Sample Name", "#", "Protein (mg/ml)", "Luminescence (RLU)", "Specific (RLU/mg)"]
        for col, header in enumerate(headers):
            label = ttk.Label(self.table_inner_frame, text=header, font=('Helvetica', 9, 'bold'),
                              relief='solid', borderwidth=1, padding=5)
            label.grid(row=0, column=col, sticky='ew')

        # Create entry widgets for sample names and data labels
        self.name_entries = []
        self.data_labels = []

        for i in range(self.data_model.num_samples):
            row = i + 1

            # Sample name entry
            name_var = tk.StringVar(value=self.data_model.get_sample_name(i))
            name_entry = ttk.Entry(self.table_inner_frame, textvariable=name_var, width=15)
            name_entry.grid(row=row, column=0, sticky='ew', padx=2, pady=1)
            self.name_entries.append(name_var)

            # Sample number
            num_label = ttk.Label(self.table_inner_frame, text=str(i + 1), relief='solid',
                                  borderwidth=1, padding=5)
            num_label.grid(row=row, column=1, sticky='ew')

            # Placeholder labels for data (will be filled in _display_results)
            data_row_labels = []
            for col in range(2, 5):
                label = ttk.Label(self.table_inner_frame, text="", relief='solid',
                                  borderwidth=1, padding=5)
                label.grid(row=row, column=col, sticky='ew')
                data_row_labels.append(label)
            self.data_labels.append(data_row_labels)

        # Update scroll region
        self.table_inner_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox('all'))

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="← Back", command=self.on_back).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Export to Excel", command=self._export_to_excel).pack(side='left', padx=5)

    def _display_results(self):
        """Display the standard curve and results table."""
        self._plot_standard_curve()
        self._update_results_table()

    def _plot_standard_curve(self):
        """Plot the standard curve with error bars."""
        params = self.data_model.standard_curve_params
        if params is None:
            return

        self.ax.clear()

        # Plot standards with error bars
        self.ax.errorbar(
            params['std_concentrations'],
            params['std_absorbances_mean'],
            yerr=params['std_absorbances_sem'],
            fmt='o',
            capsize=5,
            capthick=2,
            label='Standards'
        )

        # Plot regression line
        x_fit = np.linspace(0, max(params['std_concentrations']), 100)
        y_fit = params['slope'] * x_fit + params['intercept']
        self.ax.plot(x_fit, y_fit, 'r-', label='Linear fit')

        # Labels and title
        self.ax.set_xlabel('BSA Concentration (mg/ml)', fontsize=10)
        self.ax.set_ylabel('Absorbance', fontsize=10)
        self.ax.set_title('Bradford Standard Curve', fontsize=12, fontweight='bold')
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)

        # Add equation and R² to plot
        equation = format_equation(params['slope'], params['intercept'])
        r_squared = params['r_squared']
        text = f"{equation}\nR² = {r_squared:.4f}"
        self.ax.text(0.05, 0.95, text, transform=self.ax.transAxes,
                     verticalalignment='top', fontsize=9,
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        self.fig.tight_layout()
        self.canvas.draw()

        # Show warning if R² is poor
        if r_squared < 0.95:
            self.warning_label.config(
                text=f"⚠ Warning: R² = {r_squared:.4f} is below 0.95. Results may be unreliable."
            )
        else:
            self.warning_label.config(text="")

    def _update_results_table(self):
        """Update the results table with calculated values."""
        for i in range(self.data_model.num_samples):
            protein = self.data_model.protein_concentrations[i]
            luminescence = self.data_model.luminescence_samples[i]
            specific = self.data_model.specific_luminescence[i]

            self.data_labels[i][0].config(text=f"{protein:.4f}")
            self.data_labels[i][1].config(text=f"{luminescence:.0f}")
            self.data_labels[i][2].config(text=f"{specific:.0f}")

    def _export_to_excel(self):
        """Export results to Excel file."""
        # Update sample names from entry fields
        for i, var in enumerate(self.name_entries):
            self.data_model.sample_names[i] = var.get()

        # Ask for save location
        default_filename = f"{self.data_model.experiment_name}_{self.data_model.experiment_date}_results.xlsx"
        default_filename = default_filename.replace(" ", "_").replace(":", "-")

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=default_filename
        )

        if not filepath:
            return

        try:
            # Prepare raw data sheet
            raw_df = self.data_model.raw_dataframe.copy()

            # Prepare processed results sheet
            results_data = {
                'Sample': [self.data_model.get_sample_name(i) if self.data_model.sample_names[i]
                           else f"Sample {i+1}" for i in range(self.data_model.num_samples)],
                'Sample #': list(range(1, self.data_model.num_samples + 1)),
                'Protein Concentration (mg/ml)': self.data_model.protein_concentrations,
                'Luminescence (RLU)': self.data_model.luminescence_samples,
                'Specific Luminescence (RLU per mg/ml)': self.data_model.specific_luminescence
            }
            results_df = pd.DataFrame(results_data)

            # Prepare metadata
            metadata = {
                'Experiment Date': self.data_model.experiment_date,
                'Experiment Name': self.data_model.experiment_name,
                'Operator': self.data_model.operator_initials,
                'Processing Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'R²': f"{self.data_model.standard_curve_params['r_squared']:.6f}",
                'Regression Equation': format_equation(
                    self.data_model.standard_curve_params['slope'],
                    self.data_model.standard_curve_params['intercept']
                )
            }

            # Save to Excel
            sheet_data = {
                'Raw Data': raw_df,
                'Processed Results': results_df
            }

            save_to_excel(filepath, sheet_data, metadata)

            messagebox.showinfo("Success", f"Results exported successfully to:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Error", f"Error exporting to Excel: {str(e)}")
