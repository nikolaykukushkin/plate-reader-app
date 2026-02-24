"""Screen 1: File upload and experiment setup."""
import os
import streamlit as st

from app.data_model import AppState
from parsing.file_reader import read_file
from parsing.filename_parser import parse_multi_experiment_filename


def render_upload():
    app: AppState = st.session_state.app_state

    st.title("Plate Reader Data Processor")
    st.caption("Upload a plate reader export file to get started.")

    uploaded_file = st.file_uploader(
        "Upload plate reader file",
        type=["txt", "xls", "xlsx"],
        help="Supports .txt (tab-delimited), .xls, and .xlsx files from SoftMax Pro and similar instruments.",
    )

    if uploaded_file is None:
        return

    # Save to temp and read
    temp_path = f"/tmp/{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        df = read_file(temp_path)
    except Exception as e:
        st.error(f"Could not read file: {e}")
        return

    if df is None:
        st.error("Failed to read file. Check that it is a valid plate reader export.")
        return

    app.file_path = temp_path
    app.raw_dataframe = df
    app.original_filename = os.path.splitext(uploaded_file.name)[0]

    st.success(f"Loaded **{uploaded_file.name}** ({df.shape[0]} rows x {df.shape[1]} cols)")

    # Auto-detect experiments from filename and pre-populate
    parsed = parse_multi_experiment_filename(uploaded_file.name)
    app.filename_experiments = parsed

    if not app.experiments:
        if parsed:
            for p in parsed:
                app.add_experiment(
                    name=p.get("name", ""),
                    date=p.get("date", ""),
                    operator=p.get("operator", ""),
                )
        else:
            app.add_experiment(name="Experiment 1")

    # Editable experiment list
    st.subheader("Experiments")

    for i, exp in enumerate(app.experiments):
        cols = st.columns([3, 2, 1, 0.5])
        with cols[0]:
            exp.name = st.text_input(
                "Name", value=exp.name, key=f"up_name_{i}",
                label_visibility="collapsed", placeholder="Experiment name",
            )
        with cols[1]:
            exp.date = st.text_input(
                "Date", value=exp.date, key=f"up_date_{i}",
                label_visibility="collapsed", placeholder="Date",
            )
        with cols[2]:
            exp.operator = st.text_input(
                "Operator", value=exp.operator, key=f"up_op_{i}",
                label_visibility="collapsed", placeholder="Initials",
            )
        with cols[3]:
            if st.button("\u2716", key=f"up_del_{i}", help="Remove"):
                app.remove_experiment(i)
                st.rerun()

    if st.button("+ Add Experiment"):
        app.add_experiment(name=f"Experiment {len(app.experiments) + 1}")
        st.rerun()

    st.markdown("---")

    if st.button("Continue to Experiment Builder \u2192", type="primary", use_container_width=True):
        app.current_screen = "builder"
        st.rerun()
