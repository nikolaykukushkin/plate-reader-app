"""
Screen 1: File upload and experiment configuration.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from typing import Callable

from parsing.file_reader import read_file
from parsing.filename_parser import parse_filename


class UploadScreen(ttk.Frame):
    """First screen: file upload and metadata configuration."""

    def __init__(self, parent, data_model, on_next: Callable):
        super().__init__(parent)
        self.data_model = data_model
        self.on_next = on_next

        self._create_widgets()

    def _create_widgets(self):
        """Create and layout widgets."""
        # Title
        title = ttk.Label(self, text="Plate Reader Data Processor", font=('Helvetica', 16, 'bold'))
        title.pack(pady=20)

        # File selection area
        file_frame = ttk.LabelFrame(self, text="File Selection", padding=20)
        file_frame.pack(padx=20, pady=10, fill='x')

        self.file_label = ttk.Label(file_frame, text="No file selected", foreground='gray')
        self.file_label.pack(pady=10)

        browse_btn = ttk.Button(file_frame, text="Browse for File", command=self._browse_file)
        browse_btn.pack(pady=5)

        # Configuration frame
        config_frame = ttk.LabelFrame(self, text="Experiment Configuration", padding=20)
        config_frame.pack(padx=20, pady=10, fill='x')

        # Number of samples
        row = 0
        ttk.Label(config_frame, text="Number of samples:").grid(row=row, column=0, sticky='w', pady=5)
        self.num_samples_var = tk.IntVar(value=24)
        num_samples_entry = ttk.Entry(config_frame, textvariable=self.num_samples_var, width=10)
        num_samples_entry.grid(row=row, column=1, sticky='w', padx=10, pady=5)

        # Experiment date
        row += 1
        ttk.Label(config_frame, text="Experiment date:").grid(row=row, column=0, sticky='w', pady=5)
        self.date_var = tk.StringVar(value="")
        date_entry = ttk.Entry(config_frame, textvariable=self.date_var, width=30)
        date_entry.grid(row=row, column=1, sticky='w', padx=10, pady=5)

        # Experiment name
        row += 1
        ttk.Label(config_frame, text="Experiment name:").grid(row=row, column=0, sticky='w', pady=5)
        self.name_var = tk.StringVar(value="")
        name_entry = ttk.Entry(config_frame, textvariable=self.name_var, width=30)
        name_entry.grid(row=row, column=1, sticky='w', padx=10, pady=5)

        # Operator initials
        row += 1
        ttk.Label(config_frame, text="Operator initials:").grid(row=row, column=0, sticky='w', pady=5)
        self.operator_var = tk.StringVar(value="")
        operator_entry = ttk.Entry(config_frame, textvariable=self.operator_var, width=10)
        operator_entry.grid(row=row, column=1, sticky='w', padx=10, pady=5)

        # Next button
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=20)

        self.next_btn = ttk.Button(button_frame, text="Next →", command=self._on_next_clicked, state='disabled')
        self.next_btn.pack()

    def _browse_file(self):
        """Open file browser dialog."""
        filetypes = [
            ("All supported files", "*.txt *.xls *.xlsx"),
            ("Text files", "*.txt"),
            ("Excel files", "*.xls *.xlsx"),
            ("All files", "*.*")
        ]

        filepath = filedialog.askopenfilename(
            title="Select plate reader file",
            filetypes=filetypes
        )

        if filepath:
            self._load_file(filepath)

    def _load_file(self, filepath: str):
        """Load and parse the selected file."""
        try:
            # Read the file
            df = read_file(filepath)
            if df is None:
                messagebox.showerror("Error", "Failed to read file. Please check the file format.")
                return

            # Store in data model
            self.data_model.file_path = filepath
            self.data_model.raw_dataframe = df

            # Update file label
            filename = os.path.basename(filepath)
            self.file_label.config(text=filename, foreground='black')

            # Parse filename for metadata
            metadata = parse_filename(filepath)
            if metadata['date']:
                self.date_var.set(metadata['date'])
            if metadata['name']:
                self.name_var.set(metadata['name'])
            if metadata['operator']:
                self.operator_var.set(metadata['operator'])

            # Enable next button
            self.next_btn.config(state='normal')

        except Exception as e:
            messagebox.showerror("Error", f"Error loading file: {str(e)}")

    def _on_next_clicked(self):
        """Handle next button click."""
        # Validate inputs
        if not self.data_model.file_path:
            messagebox.showwarning("Warning", "Please select a file first.")
            return

        try:
            num_samples = self.num_samples_var.get()
            if num_samples <= 0:
                messagebox.showwarning("Warning", "Number of samples must be greater than 0.")
                return
        except tk.TclError:
            messagebox.showwarning("Warning", "Please enter a valid number for samples.")
            return

        # Store values in data model
        self.data_model.num_samples = self.num_samples_var.get()
        self.data_model.experiment_date = self.date_var.get()
        self.data_model.experiment_name = self.name_var.get()
        self.data_model.operator_initials = self.operator_var.get()

        # Initialize sample names
        self.data_model.set_sample_names_size(self.data_model.num_samples)

        # Proceed to next screen
        self.on_next()

    def on_file_dropped(self, filepath: str):
        """Handle file drop event (will be connected later with drag-drop support)."""
        self._load_file(filepath)
