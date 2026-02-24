#!/usr/bin/env python3
"""
Plate Reader Data Processor
Main entry point for the application.
"""
import tkinter as tk
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import PlateReaderApp


def main():
    """Main entry point."""
    root = tk.Tk()

    # Set application icon (if available)
    # root.iconbitmap('icon.ico')  # Uncomment if you have an icon

    # Bring window to foreground on macOS
    root.lift()
    root.attributes('-topmost', True)
    root.after(100, lambda: root.attributes('-topmost', False))

    # Create and run the application
    app = PlateReaderApp(root)
    app.run()


if __name__ == '__main__':
    main()
