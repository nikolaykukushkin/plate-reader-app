"""Screen 4: Results display and Excel export."""
import io
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from app.data_model import AppState, Experiment
from analysis.calculations import extract_and_calculate, format_equation


def render_results():
    app: AppState = st.session_state.app_state

    st.title("Results")

    if not app.experiments:
        st.warning("No experiments defined.")
        if st.button("\u2190 Back"):
            app.current_screen = "samples"
            st.rerun()
        return

    # Run calculations for each experiment
    for exp in app.experiments:
        if exp.luminescence_values is None and exp.num_samples > 0:
            try:
                extract_and_calculate(exp, app.raw_dataframe)
            except Exception as e:
                st.error(f"Error calculating results for **{exp.name}**: {e}")

    # Tabs per experiment
    tab_names = [e.name or f"Experiment {i+1}" for i, e in enumerate(app.experiments)]
    tabs = st.tabs(tab_names)

    for idx, tab in enumerate(tabs):
        exp = app.experiments[idx]
        with tab:
            _render_experiment_results(exp)

    # Export
    st.markdown("---")
    st.subheader("Export")

    c_back, _, c_export = st.columns([1, 2, 1])
    with c_back:
        if st.button("\u2190 Back to Sample Config", use_container_width=True):
            # Clear cached results so they recalculate with updated config
            for exp in app.experiments:
                exp.clear_results()
            app.current_screen = "samples"
            st.rerun()

    with c_export:
        excel_bytes = _build_excel(app)
        if excel_bytes:
            fname = f"{app.original_filename or 'results'}_processed.xlsx"
            st.download_button(
                "Download Excel",
                data=excel_bytes,
                file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )


def _render_experiment_results(exp: Experiment):
    if exp.num_samples == 0:
        st.info("No data for this experiment.")
        return

    lumi = exp.luminescence_values
    if lumi is None:
        st.warning("Results not yet calculated.")
        return

    # --- Standard curve (if Bradford) ---
    if exp.has_bradford and exp.standard_curve_params:
        params = exp.standard_curve_params
        r2 = params["r_squared"]

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.errorbar(
            params["std_concentrations"],
            params["std_absorbances_mean"],
            yerr=params["std_absorbances_sem"],
            fmt="o", markersize=7, capsize=4, capthick=1.5,
            color="#4361ee", label="Standards",
        )
        x_fit = np.linspace(0, max(params["std_concentrations"]), 100)
        y_fit = params["slope"] * x_fit + params["intercept"]
        ax.plot(x_fit, y_fit, "-", linewidth=2, color="#ef476f", label="Linear fit")

        ax.set_xlabel("BSA Concentration (mg/ml)")
        ax.set_ylabel("Absorbance")
        ax.set_title("Bradford Standard Curve")
        ax.legend(frameon=False)
        ax.grid(True, alpha=0.2)

        eq = format_equation(params["slope"], params["intercept"])
        ax.text(
            0.05, 0.95, f"{eq}\nR\u00b2 = {r2:.4f}",
            transform=ax.transAxes, va="top",
            bbox=dict(boxstyle="round", facecolor="#fff9e6", alpha=0.8),
            fontsize=10,
        )
        st.pyplot(fig)
        plt.close(fig)

        if r2 < 0.95:
            st.warning(f"R\u00b2 = {r2:.4f} is below 0.95 — results may be unreliable.")
        else:
            st.success(f"R\u00b2 = {r2:.4f}")

    # --- Results table ---
    n = exp.num_samples
    data = {
        "Sample Name": [exp.sample_names[i] if exp.sample_names[i] else f"Sample {i+1}" for i in range(n)],
        "#": list(range(1, n + 1)),
        "Luminescence (RLU)": [f"{v:.0f}" for v in lumi],
    }

    if exp.has_bradford and exp.protein_concentrations is not None:
        pc = exp.protein_concentrations
        sl = exp.specific_luminescence
        data["Protein (mg/ml)"] = [f"{v:.4f}" if not np.isnan(v) else "—" for v in pc]
        data["Specific (RLU/mg)"] = [f"{v:.0f}" if not np.isnan(v) else "—" for v in sl]

    results_df = pd.DataFrame(data)
    st.dataframe(results_df, use_container_width=True, hide_index=True, height=min(35 * n + 40, 600))


def _build_excel(app: AppState) -> bytes:
    """Build a multi-sheet Excel file with all experiment results."""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Raw data sheet
        if app.raw_dataframe is not None:
            app.raw_dataframe.to_excel(writer, sheet_name="Raw Data", index=False, header=False)

        # One sheet per experiment
        for i, exp in enumerate(app.experiments):
            if exp.num_samples == 0:
                continue
            sheet_name = (exp.name or f"Experiment {i+1}")[:31]  # Excel 31-char limit
            n = exp.num_samples
            lumi = exp.luminescence_values

            data = {
                "Sample": [exp.sample_names[j] if exp.sample_names[j] else f"Sample {j+1}" for j in range(n)],
                "Sample #": list(range(1, n + 1)),
                "Luminescence (RLU)": lumi.tolist() if lumi is not None else [None] * n,
            }

            if exp.has_bradford and exp.protein_concentrations is not None:
                data["Protein Concentration (mg/ml)"] = exp.protein_concentrations.tolist()
                data["Specific Luminescence (RLU per mg/ml)"] = exp.specific_luminescence.tolist()

            exp_df = pd.DataFrame(data)
            exp_df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Metadata below the data
            ws = writer.sheets[sheet_name]
            row_off = len(exp_df) + 3
            ws.cell(row=row_off, column=1, value="Metadata:")
            row_off += 1
            meta = {
                "Experiment Name": exp.name,
                "Date": exp.date,
                "Operator": exp.operator,
                "Processing Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            if exp.standard_curve_params:
                meta["R\u00b2"] = f"{exp.standard_curve_params['r_squared']:.6f}"
                meta["Equation"] = format_equation(
                    exp.standard_curve_params["slope"],
                    exp.standard_curve_params["intercept"],
                )
            for k, v in meta.items():
                ws.cell(row=row_off, column=1, value=k)
                ws.cell(row=row_off, column=2, value=str(v))
                row_off += 1

    output.seek(0)
    return output.getvalue()
