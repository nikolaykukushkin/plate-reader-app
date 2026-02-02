# Plate Reader Data Processor

A web-based application for processing plate reader data files containing Bradford protein measurements and luciferase luminescence reads.

## Features

- 🌐 **Web-based interface** - runs in your browser, works on any OS
- 📁 Supports .txt and .xls/.xlsx file formats
- 🔍 Automatic detection and parsing of Bradford and luminescence grids
- 📊 Linear regression analysis with standard curve visualization
- 📈 Calculation of protein concentrations and specific luminescence
- 💾 Export results to Excel with raw data and processed results
- ✏️ Editable sample names and Bradford standard concentrations
- ⚙️ Configurable replicates for standards and samples

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package installer)

### Install Dependencies

```bash
cd plate_reader_app
pip3 install -r requirements.txt
```

The application requires the following packages:
- numpy
- pandas
- matplotlib
- scipy
- openpyxl
- chardet
- streamlit

## Usage

### Running the Web Application (Recommended)

```bash
cd plate_reader_app
streamlit run streamlit_app.py
```

The application will automatically open in your default web browser at `http://localhost:8501`

### Alternative: Desktop GUI (macOS compatibility issues)

If you prefer the desktop version (note: requires compatible macOS version):

```bash
cd plate_reader_app
python3 main.py
```

**Note:** The desktop version has compatibility issues with some macOS versions. The web-based version is recommended.

### Workflow

#### Screen 1: File Upload & Configuration
1. Click "Browse for File" to select your plate reader data file
2. The application will auto-fill:
   - **Experiment date** (from filename: YYYYMMDD)
   - **Experiment name** (from filename: middle part)
   - **Operator initials** (from filename: last 2 letters)
3. Adjust the **Number of samples** if needed (default: 24)
4. Review and edit the metadata fields as needed
5. Click **"Next →"**

#### Screen 2: Bradford Verification
1. Review the **Original Grid** (as detected in the file)
2. Check the **Parsed Grid** (organized as standards + samples)
3. Adjust replicate counts if needed:
   - **Standard replicates** (default: 3)
   - **Sample replicates** (default: 3)
4. Edit **Bradford standard concentrations** if they differ from defaults
5. Click **"Next →"** to proceed (or **"Manual Selection"** if detection failed)

#### Screen 3: Luminescence Verification
1. Review the **Original Grid** (luminescence data)
2. Check the **Parsed Samples** (listed in order)
3. Click **"Next →"** to proceed (or **"Manual Selection"** if needed)

#### Screen 4: Results & Export
1. View the **Standard Curve** plot with R² value
2. Review the **Sample Results** table with:
   - Protein concentration (mg/ml)
   - Luminescence (RLU)
   - Specific luminescence (RLU per mg/ml)
3. Enter **Sample Names** in the first column (optional)
4. Click **"Export to Excel"** to save results

### Excel Output

The exported file contains two sheets:

1. **Raw Data**: Original file content
2. **Processed Results**:
   - Sample names and numbers
   - Protein concentrations
   - Luminescence values
   - Specific luminescence
   - Metadata (experiment info, processing date, R²)

## File Format Requirements

### Input File Format

The application expects tab-delimited text files or Excel files with:

1. **Bradford grid**: 8 rows × 12 columns of absorbance values
   - Organized as: Standards (columns 1-3), Samples (columns 4-12)
   - 3 replicates per sample/standard (configurable)

2. **Luminescence grid**: Smaller grid below Bradford data
   - Typically 4 rows × 6 columns (for 24 samples)
   - Read left-to-right, top-to-bottom

3. **Filename format** (optional): `YYYYMMDD_experiment_name_OP.ext`
   - Example: `20260122_reverse_transplant_NK.txt`

## Default Bradford Standards

| Standard | Concentration (mg/ml) |
|----------|-----------------------|
| 1        | 0.02                  |
| 2        | 0.05                  |
| 3        | 0.10                  |
| 4        | 0.20                  |
| 5        | 0.50                  |
| 6        | 1.00                  |
| 7        | 1.50                  |
| 8        | 2.00                  |

These can be edited on Screen 2 if your standards differ.

## Warnings and Troubleshooting

### R² Warning
- If R² < 0.95, a warning appears on the results screen
- Results may be unreliable; consider checking your standards
- The application still allows export even with low R²

### Grid Detection Failures
- If auto-detection fails, use the **"Manual Selection"** button
- This feature allows you to specify the exact cell range for grids
- (Note: Manual selection is planned for a future update)

### Common Issues

**File won't load:**
- Check file format (.txt, .xls, or .xlsx)
- Verify file encoding (the app handles UTF-16 and UTF-8)

**Wrong grid detected:**
- Use manual selection to specify correct range
- Check that your data matches the expected layout

**Parsing errors:**
- Verify replicate counts match your actual data
- Ensure numeric values are properly formatted in the file

## Project Structure

```
plate_reader_app/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── app/
│   ├── data_model.py            # Shared data model
│   └── app.py                   # Main application controller
├── screens/
│   ├── upload_screen.py         # Screen 1: File upload
│   ├── bradford_screen.py       # Screen 2: Bradford verification
│   ├── luminescence_screen.py   # Screen 3: Luminescence verification
│   └── results_screen.py        # Screen 4: Results & export
├── parsing/
│   ├── file_reader.py           # File I/O with encoding detection
│   ├── filename_parser.py       # Extract metadata from filename
│   ├── bradford_parser.py       # Bradford grid detection & parsing
│   └── luminescence_parser.py   # Luminescence grid detection & parsing
└── analysis/
    └── calculations.py          # Linear regression & calculations
```

## Future Enhancements

- ✨ Drag-and-drop file support (tkinterdnd2)
- ✨ Manual grid selection widget
- ✨ Batch processing for multiple files
- ✨ Customizable standard curve models
- ✨ Data visualization enhancements

## Testing

The application has been tested with the provided example file:
- **File**: `20260122_reverse_transplant_NK.txt`
- **Results**: Correct parsing and calculations verified
- **R²**: 0.9997 (excellent fit)

## Support

For issues or questions, please refer to the project documentation or contact the developer.

## License

Copyright © 2026. All rights reserved.
