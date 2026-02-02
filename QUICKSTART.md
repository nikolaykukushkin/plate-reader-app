# Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Install Dependencies

```bash
cd plate_reader_app
pip3 install -r requirements.txt
```

Or if using a virtual environment:
```bash
cd plate_reader_app
source ../.venv/bin/activate  # Adjust path to your venv
pip install -r requirements.txt
```

### 2. Run the Application

```bash
streamlit run streamlit_app.py
```

The app will automatically open in your browser at `http://localhost:8501`

### 3. Process Your Data

1. **Upload Screen**: Upload your .txt or .xlsx file
   - The app will auto-fill experiment info from the filename
   - Adjust number of samples if needed (default: 24)

2. **Bradford Screen**: Verify the Bradford grid
   - Check that standards and samples are detected correctly
   - Adjust replicates if needed (default: 3)
   - Edit standard concentrations if they differ

3. **Luminescence Screen**: Verify the luminescence data
   - Check that all samples are detected correctly

4. **Results Screen**: Review and export
   - View the standard curve and R² value
   - Edit sample names if desired
   - Click "Export to Excel" to download results

## 💡 Tips

- **File Format**: Your filename should be `YYYYMMDD_experiment_name_OP.ext`
  - Example: `20260122_reverse_transplant_NK.txt`
  - This allows auto-filling of date, name, and operator

- **Grid Detection**: The app automatically detects Bradford (8×12) and luminescence grids
  - Bradford: 8 standards + 24 samples (or your specified number)
  - Luminescence: matches your sample count

- **Standard Curve**: Look for R² ≥ 0.95 for reliable results
  - The app will warn you if R² is below 0.95

- **Excel Export**: The output file contains:
  - Sheet 1: Raw data (copy of your original file)
  - Sheet 2: Processed results with metadata

## 🐛 Troubleshooting

**App won't start:**
```bash
# Make sure streamlit is installed
pip install streamlit

# Check Python version (need 3.9+)
python3 --version
```

**File won't upload:**
- Ensure file is .txt, .xls, or .xlsx format
- Check that the file is not corrupted

**Grid detection failed:**
- Verify your file has the expected data layout
- Check for non-numeric values in the grids

## 📧 Need Help?

If you encounter issues, check:
1. File format matches the expected layout
2. All dependencies are installed
3. Python version is 3.9 or higher

## 🎯 Example Workflow

Using the test file `20260122_reverse_transplant_NK.txt`:

1. Launch app: `streamlit run streamlit_app.py`
2. Upload the test file
3. Verify auto-filled metadata (date: 2026-01-22, name: "Reverse transplant", operator: "NK")
4. Click through screens to verify detection
5. Export results to Excel

Expected results:
- R² ≈ 0.9997 (excellent fit)
- 24 samples with protein concentrations and luminescence values
