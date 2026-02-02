#!/usr/bin/env python3
"""
Plate Reader Data Processor - Streamlit Web Application
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import io
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.data_model import DataModel
from parsing.file_reader import read_file, save_to_excel
from parsing.filename_parser import parse_filename
from parsing.bradford_parser import detect_bradford_grid, parse_bradford_grid
from parsing.luminescence_parser import detect_luminescence_grid, parse_luminescence_grid
from analysis.calculations import calculate_protein_concentrations, format_equation


# Page configuration
st.set_page_config(
    page_title="Plate Reader Data Processor",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def init_session_state():
    """Initialize session state variables."""
    if 'data_model' not in st.session_state:
        st.session_state.data_model = DataModel()
    if 'current_screen' not in st.session_state:
        st.session_state.current_screen = 'upload'
    if 'bradford_detection_done' not in st.session_state:
        st.session_state.bradford_detection_done = False
    if 'luminescence_detection_done' not in st.session_state:
        st.session_state.luminescence_detection_done = False
    if 'calculations_done' not in st.session_state:
        st.session_state.calculations_done = False
    if 'original_filename' not in st.session_state:
        st.session_state.original_filename = None


def navigate_to(screen):
    """Navigate to a different screen."""
    st.session_state.current_screen = screen


def screen_upload():
    """Screen 1: File Upload & Configuration."""
    st.title("🧬 Plate Reader Data Processor")
    st.markdown("---")

    st.header("📁 File Upload & Configuration")

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload your plate reader data file",
        type=['txt', 'xls', 'xlsx'],
        help="Select a .txt, .xls, or .xlsx file from your plate reader"
    )

    if uploaded_file is not None:
        try:
            # Save uploaded file temporarily with proper extension
            file_ext = os.path.splitext(uploaded_file.name)[1]
            temp_path = f"/tmp/{uploaded_file.name}"
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            # Store original filename (without extension) for later use
            st.session_state.original_filename = os.path.splitext(uploaded_file.name)[0]

            # Read the file
            df = read_file(temp_path)
            if df is None:
                st.error(f"Failed to read file. Please check the file format. Extension: {file_ext}")
                st.info("Supported formats: .txt (tab-delimited), .xls, .xlsx")
                return

            # Store in data model
            st.session_state.data_model.file_path = temp_path
            st.session_state.data_model.raw_dataframe = df

            # Parse filename for metadata
            metadata = parse_filename(uploaded_file.name)

            st.success(f"✅ File loaded successfully: {uploaded_file.name}")

            # Configuration form
            st.subheader("Experiment Configuration")

            col1, col2 = st.columns(2)

            with col1:
                num_samples = st.number_input(
                    "Number of samples",
                    min_value=1,
                    max_value=96,
                    value=24,
                    help="Total number of samples in your experiment"
                )

                experiment_date = st.text_input(
                    "Experiment date",
                    value=metadata.get('date', ''),
                    help="Date in YYYY-MM-DD format"
                )

            with col2:
                experiment_name = st.text_input(
                    "Experiment name",
                    value=metadata.get('name', ''),
                    help="Name or description of your experiment"
                )

                operator_initials = st.text_input(
                    "Operator initials",
                    value=metadata.get('operator', ''),
                    help="Your initials"
                )

            # Store configuration
            st.session_state.data_model.num_samples = num_samples
            st.session_state.data_model.experiment_date = experiment_date
            st.session_state.data_model.experiment_name = experiment_name
            st.session_state.data_model.operator_initials = operator_initials
            st.session_state.data_model.set_sample_names_size(num_samples)

            st.markdown("---")

            if st.button("Next: Bradford Configuration →", type="primary", use_container_width=True):
                navigate_to('bradford')
                st.rerun()

        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
    else:
        st.info("👆 Please upload a file to get started")


def screen_bradford():
    """Screen 2: Bradford Verification & Configuration."""
    st.title("🧬 Plate Reader Data Processor")
    st.markdown("---")

    st.header("🔬 Bradford Assay Configuration")

    # Auto-detect on first visit
    if not st.session_state.bradford_detection_done:
        with st.spinner("Detecting Bradford grid..."):
            try:
                result = detect_bradford_grid(st.session_state.data_model.raw_dataframe)
                if result is None:
                    st.error("⚠️ Could not auto-detect Bradford grid. Manual selection would be needed.")
                    return

                grid, bounds = result
                st.session_state.data_model.bradford_raw_grid = grid
                st.session_state.data_model.bradford_raw_bounds = bounds
                st.session_state.bradford_detection_done = True
            except Exception as e:
                st.error(f"Error detecting Bradford grid: {str(e)}")
                return

    # Configuration controls
    st.subheader("Configuration")

    col1, col2 = st.columns(2)

    with col1:
        std_replicates = st.selectbox(
            "Standard replicates",
            options=[1, 2, 3],
            index=2,
            help="Number of replicates for each standard"
        )

    with col2:
        sample_replicates = st.selectbox(
            "Sample replicates",
            options=[1, 2, 3],
            index=2,
            help="Number of replicates for each sample"
        )

    # Parse Bradford grid
    try:
        standards, samples = parse_bradford_grid(
            st.session_state.data_model.bradford_raw_grid,
            st.session_state.data_model.num_samples,
            std_replicates,
            sample_replicates
        )

        st.session_state.data_model.bradford_standards = standards
        st.session_state.data_model.bradford_samples = samples
        st.session_state.data_model.standard_replicates = std_replicates
        st.session_state.data_model.sample_replicates = sample_replicates
    except Exception as e:
        st.error(f"Error parsing Bradford grid: {str(e)}")
        return

    # Display grids side by side
    st.subheader("Grid Verification")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Original Grid**")
        grid = st.session_state.data_model.bradford_raw_grid
        st.dataframe(
            pd.DataFrame(grid),
            use_container_width=True,
            height=300
        )

    with col2:
        st.markdown("**Parsed Grid**")

        # Create parsed grid display
        parsed_data = []

        # Standards
        for i, std_row in enumerate(standards):
            conc = st.session_state.data_model.standard_concentrations[i]
            row_dict = {'Label': f'Std {i+1} ({conc} mg/ml)'}
            for j, val in enumerate(std_row):
                row_dict[f'Rep{j+1}'] = f"{val:.4f}"
            row_dict['Mean'] = f"{np.mean(std_row):.4f}"
            parsed_data.append(row_dict)

        # Samples
        for i, sample_row in enumerate(samples):
            row_dict = {'Label': f'Sample {i+1}'}
            for j, val in enumerate(sample_row):
                row_dict[f'Rep{j+1}'] = f"{val:.4f}"
            row_dict['Mean'] = f"{np.mean(sample_row):.4f}"
            parsed_data.append(row_dict)

        st.dataframe(
            pd.DataFrame(parsed_data),
            use_container_width=True,
            height=300
        )

    # Bradford standards configuration
    st.subheader("Bradford Standard Concentrations (mg/ml)")

    cols = st.columns(4)
    standard_values = []

    for i in range(8):
        with cols[i % 4]:
            val = st.number_input(
                f"Standard {i+1}",
                min_value=0.0,
                value=st.session_state.data_model.standard_concentrations[i],
                step=0.01,
                format="%.3f",
                key=f"std_conc_{i}"
            )
            standard_values.append(val)

    st.session_state.data_model.standard_concentrations = standard_values

    # Navigation buttons
    st.markdown("---")
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back to Upload", use_container_width=True):
            navigate_to('upload')
            st.rerun()

    with col2:
        if st.button("Next: Luminescence →", type="primary", use_container_width=True):
            navigate_to('luminescence')
            st.rerun()


def screen_luminescence():
    """Screen 3: Luminescence Verification."""
    st.title("🧬 Plate Reader Data Processor")
    st.markdown("---")

    st.header("✨ Luminescence Assay Verification")

    # Auto-detect on first visit
    if not st.session_state.luminescence_detection_done:
        with st.spinner("Detecting luminescence grid..."):
            try:
                result = detect_luminescence_grid(
                    st.session_state.data_model.raw_dataframe,
                    st.session_state.data_model.num_samples,
                    st.session_state.data_model.bradford_raw_bounds
                )

                if result is None:
                    st.error("⚠️ Could not auto-detect luminescence grid.")
                    return

                lumi_grid, lumi_bounds = result
                st.session_state.data_model.luminescence_raw_grid = lumi_grid
                st.session_state.data_model.luminescence_raw_bounds = lumi_bounds

                # Parse luminescence
                lumi_samples = parse_luminescence_grid(
                    lumi_grid,
                    st.session_state.data_model.num_samples
                )
                st.session_state.data_model.luminescence_samples = lumi_samples
                st.session_state.luminescence_detection_done = True

            except Exception as e:
                st.error(f"Error detecting luminescence grid: {str(e)}")
                return

    # Display grids side by side
    st.subheader("Grid Verification")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Original Grid**")
        grid = st.session_state.data_model.luminescence_raw_grid
        st.dataframe(
            pd.DataFrame(grid).applymap(lambda x: f"{x:.0f}"),
            use_container_width=True,
            height=400
        )

    with col2:
        st.markdown("**Parsed Samples**")

        samples = st.session_state.data_model.luminescence_samples
        parsed_data = {
            'Sample': [f"Sample {i+1}" for i in range(len(samples))],
            'Luminescence (RLU)': [f"{val:.0f}" for val in samples]
        }

        st.dataframe(
            pd.DataFrame(parsed_data),
            use_container_width=True,
            height=400,
            hide_index=True
        )

    # Navigation buttons
    st.markdown("---")
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back to Bradford", use_container_width=True):
            navigate_to('bradford')
            st.rerun()

    with col2:
        if st.button("Next: Results →", type="primary", use_container_width=True):
            navigate_to('results')
            st.rerun()


def screen_results():
    """Screen 4: Results & Export."""
    st.title("🧬 Plate Reader Data Processor")
    st.markdown("---")

    st.header("📊 Results & Export")

    # Calculate results on first visit
    if not st.session_state.calculations_done:
        with st.spinner("Calculating protein concentrations..."):
            try:
                protein_conc, specific_lumi, curve_params = calculate_protein_concentrations(
                    st.session_state.data_model.bradford_samples,
                    st.session_state.data_model.bradford_standards,
                    np.array(st.session_state.data_model.standard_concentrations),
                    st.session_state.data_model.luminescence_samples
                )

                st.session_state.data_model.protein_concentrations = protein_conc
                st.session_state.data_model.specific_luminescence = specific_lumi
                st.session_state.data_model.standard_curve_params = curve_params
                st.session_state.calculations_done = True

            except Exception as e:
                st.error(f"Error calculating results: {str(e)}")
                return

    # Standard curve plot
    st.subheader("Standard Curve")

    params = st.session_state.data_model.standard_curve_params

    fig, ax = plt.subplots(figsize=(10, 5))

    # Plot standards with error bars
    ax.errorbar(
        params['std_concentrations'],
        params['std_absorbances_mean'],
        yerr=params['std_absorbances_sem'],
        fmt='o',
        markersize=8,
        capsize=5,
        capthick=2,
        label='Standards'
    )

    # Plot regression line
    x_fit = np.linspace(0, max(params['std_concentrations']), 100)
    y_fit = params['slope'] * x_fit + params['intercept']
    ax.plot(x_fit, y_fit, 'r-', linewidth=2, label='Linear fit')

    ax.set_xlabel('BSA Concentration (mg/ml)', fontsize=12)
    ax.set_ylabel('Absorbance', fontsize=12)
    ax.set_title('Bradford Standard Curve', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Add equation and R²
    equation = format_equation(params['slope'], params['intercept'])
    r_squared = params['r_squared']
    ax.text(0.05, 0.95, f"{equation}\nR² = {r_squared:.4f}",
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontsize=10)

    st.pyplot(fig)

    # Warning if R² is poor
    if r_squared < 0.95:
        st.warning(f"⚠️ Warning: R² = {r_squared:.4f} is below 0.95. Results may be unreliable.")
    else:
        st.success(f"✅ Excellent fit: R² = {r_squared:.4f}")

    # Results table
    st.subheader("Sample Results")

    # Create editable dataframe
    protein_concs = st.session_state.data_model.protein_concentrations
    lumi_samples = st.session_state.data_model.luminescence_samples
    specific_lumi = st.session_state.data_model.specific_luminescence

    results_data = {
        'Sample Name': [st.session_state.data_model.get_sample_name(i)
                        for i in range(st.session_state.data_model.num_samples)],
        'Sample #': list(range(1, st.session_state.data_model.num_samples + 1)),
        'Protein (mg/ml)': [f"{val:.4f}" for val in protein_concs],
        'Luminescence (RLU)': [f"{val:.0f}" for val in lumi_samples],
        'Specific (RLU/mg)': [f"{val:.0f}" for val in specific_lumi]
    }

    results_df = pd.DataFrame(results_data)

    # Display editable table with a unique key
    edited_df = st.data_editor(
        results_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Sample Name": st.column_config.TextColumn(
                "Sample Name",
                help="Edit to name your samples (changes save automatically)",
                max_chars=50,
            )
        },
        height=400,
        key="sample_results_editor"
    )

    # Store edited sample names immediately
    for i, name in enumerate(edited_df['Sample Name']):
        st.session_state.data_model.sample_names[i] = name if name else ""

    # Export button
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back to Luminescence", use_container_width=True):
            navigate_to('luminescence')
            st.rerun()

    with col2:
        if st.button("📥 Export to Excel", type="primary", use_container_width=True):
            # Create Excel file in memory
            try:
                # Prepare raw data sheet
                raw_df = st.session_state.data_model.raw_dataframe.copy()

                # Prepare processed results sheet
                export_data = {
                    'Sample': [st.session_state.data_model.get_sample_name(i) if st.session_state.data_model.sample_names[i]
                              else f"Sample {i+1}" for i in range(st.session_state.data_model.num_samples)],
                    'Sample #': list(range(1, st.session_state.data_model.num_samples + 1)),
                    'Protein Concentration (mg/ml)': protein_concs,
                    'Luminescence (RLU)': lumi_samples,
                    'Specific Luminescence (RLU per mg/ml)': specific_lumi
                }
                export_df = pd.DataFrame(export_data)

                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    raw_df.to_excel(writer, sheet_name='Raw Data', index=False, header=False)
                    export_df.to_excel(writer, sheet_name='Processed Results', index=False)

                    # Add metadata
                    worksheet = writer.sheets['Processed Results']
                    row_offset = len(export_df) + 3

                    metadata = {
                        'Experiment Date': st.session_state.data_model.experiment_date,
                        'Experiment Name': st.session_state.data_model.experiment_name,
                        'Operator': st.session_state.data_model.operator_initials,
                        'Processing Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'R²': f"{params['r_squared']:.6f}",
                        'Regression Equation': equation
                    }

                    worksheet.cell(row=row_offset, column=1, value="Metadata:")
                    row_offset += 1

                    for key, value in metadata.items():
                        worksheet.cell(row=row_offset, column=1, value=key)
                        worksheet.cell(row=row_offset, column=2, value=str(value))
                        row_offset += 1

                output.seek(0)

                # Generate filename based on original input filename
                if st.session_state.original_filename:
                    filename = f"{st.session_state.original_filename}_results.xlsx"
                else:
                    # Fallback to constructed name
                    filename = f"{st.session_state.data_model.experiment_name}_{st.session_state.data_model.experiment_date}_results.xlsx"
                    filename = filename.replace(" ", "_").replace(":", "-")

                # Download button
                st.download_button(
                    label="💾 Download Excel File",
                    data=output,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

                st.success(f"✅ Excel file ready! Click the button above to download.")
                st.info(f"📄 Filename: **{filename}**\n\n💡 Your browser will save it to your Downloads folder.")

            except Exception as e:
                st.error(f"Error creating Excel file: {str(e)}")


def main():
    """Main application."""
    init_session_state()

    # Display current screen
    if st.session_state.current_screen == 'upload':
        screen_upload()
    elif st.session_state.current_screen == 'bradford':
        screen_bradford()
    elif st.session_state.current_screen == 'luminescence':
        screen_luminescence()
    elif st.session_state.current_screen == 'results':
        screen_results()


if __name__ == '__main__':
    main()
