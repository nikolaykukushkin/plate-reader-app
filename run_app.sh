#!/bin/bash

# Plate Reader Data Processor - Launch Script

echo "🧬 Plate Reader Data Processor"
echo "================================"
echo ""

# Path to virtual environment (adjust if your venv is elsewhere)
VENV_PATH="../.venv"

# Check if virtual environment exists
if [ -d "$VENV_PATH" ]; then
    echo "✓ Using virtual environment at $VENV_PATH"
    PYTHON="$VENV_PATH/bin/python"
    STREAMLIT="$VENV_PATH/bin/streamlit"

    # Check if streamlit is installed in venv
    if [ ! -f "$STREAMLIT" ]; then
        echo "Installing dependencies in virtual environment..."
        "$VENV_PATH/bin/pip" install -r requirements.txt
    fi
else
    echo "⚠️  Virtual environment not found at $VENV_PATH"
    echo "Using system Python..."
    PYTHON="python3"
    STREAMLIT="streamlit"

    # Check if streamlit is installed
    if ! command -v streamlit &> /dev/null; then
        echo "Installing dependencies..."
        pip3 install -r requirements.txt
    fi
fi

# Launch the application
echo ""
echo "🚀 Launching application..."
echo "The app will open in your browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

"$STREAMLIT" run streamlit_app.py
