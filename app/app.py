"""
Main application controller.
Manages screen navigation and application state.
"""
import tkinter as tk
from tkinter import ttk

from app.data_model import DataModel
from screens.upload_screen import UploadScreen
from screens.bradford_screen import BradfordScreen
from screens.luminescence_screen import LuminescenceScreen
from screens.results_screen import ResultsScreen


class PlateReaderApp:
    """Main application class."""

    def __init__(self, root):
        self.root = root
        self.root.title("Plate Reader Data Processor")
        self.root.geometry("900x700")

        # Initialize data model
        self.data_model = DataModel()

        # Container for screens
        self.container = ttk.Frame(self.root)
        self.container.pack(fill='both', expand=True)

        # Current screen
        self.current_screen = None

        # Show first screen
        self.show_upload_screen()

    def clear_screen(self):
        """Remove current screen from view."""
        if self.current_screen:
            self.current_screen.pack_forget()
            self.current_screen.destroy()
            self.current_screen = None

    def show_upload_screen(self):
        """Show the upload screen."""
        self.clear_screen()
        self.current_screen = UploadScreen(
            self.container,
            self.data_model,
            on_next=self.show_bradford_screen
        )
        self.current_screen.pack(fill='both', expand=True)

    def show_bradford_screen(self):
        """Show the Bradford verification screen."""
        self.clear_screen()
        self.current_screen = BradfordScreen(
            self.container,
            self.data_model,
            on_next=self.show_luminescence_screen,
            on_back=self.show_upload_screen
        )
        self.current_screen.pack(fill='both', expand=True)

    def show_luminescence_screen(self):
        """Show the luminescence verification screen."""
        self.clear_screen()
        self.current_screen = LuminescenceScreen(
            self.container,
            self.data_model,
            on_next=self.show_results_screen,
            on_back=self.show_bradford_screen
        )
        self.current_screen.pack(fill='both', expand=True)

    def show_results_screen(self):
        """Show the results and export screen."""
        self.clear_screen()
        self.current_screen = ResultsScreen(
            self.container,
            self.data_model,
            on_back=self.show_luminescence_screen
        )
        self.current_screen.pack(fill='both', expand=True)

    def run(self):
        """Start the application."""
        self.root.mainloop()
