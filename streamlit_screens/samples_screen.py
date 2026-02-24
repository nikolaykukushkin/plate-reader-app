"""Screen 3: Sample names, standard concentrations, and Bradford toggles."""
import streamlit as st
import pandas as pd
import numpy as np

from app.data_model import AppState, Experiment


def render_samples():
    app: AppState = st.session_state.app_state

    st.title("Sample Configuration")
    st.caption("Name your samples and configure Bradford standards. You can paste columns from Excel.")

    if not app.experiments:
        st.warning("No experiments defined.")
        if st.button("\u2190 Back"):
            app.current_screen = "builder"
            st.rerun()
        return

    # Tabs for each experiment
    tab_names = [e.name or f"Experiment {i+1}" for i, e in enumerate(app.experiments)]
    tabs = st.tabs(tab_names)

    for idx, tab in enumerate(tabs):
        exp = app.experiments[idx]
        exp.ensure_lists_sized()

        with tab:
            _render_experiment_config(idx, exp)

    # Navigation
    st.markdown("---")
    c_back, _, c_next = st.columns([1, 2, 1])
    with c_back:
        if st.button("\u2190 Back to Builder", use_container_width=True):
            app.current_screen = "builder"
            st.rerun()
    with c_next:
        if st.button("Calculate Results \u2192", type="primary", use_container_width=True):
            app.current_screen = "results"
            st.rerun()


def _stable_df(session_key, build_fn, n_rows):
    """Return a stable DataFrame stored in session state.

    Initializes from *build_fn()* the first time, or when the expected
    row count changes (e.g. user went back and changed selections).
    Passing the same object to st.data_editor across reruns prevents
    Streamlit from resetting the widget's pending edits.
    """
    if (session_key not in st.session_state
            or len(st.session_state[session_key]) != n_rows):
        st.session_state[session_key] = build_fn()
    return st.session_state[session_key]


def _render_experiment_config(idx: int, exp: Experiment):
    n = exp.num_samples
    if n == 0:
        st.info("No luminescence data selected for this experiment.")
        return

    st.markdown(f"**{n} samples** &nbsp; | &nbsp; Date: {exp.date or '\u2014'} &nbsp; | &nbsp; Operator: {exp.operator or '\u2014'}")

    col_left, col_right = st.columns(2, gap="large")

    # ---- Sample names (left) ----
    with col_left:
        st.markdown("##### Sample Names")
        st.caption("Paste a column from Excel or type names directly.")

        names_base = _stable_df(
            f"_names_base_{idx}",
            lambda: pd.DataFrame({
                "#": list(range(1, n + 1)),
                "Sample Name": [s if s else "" for s in exp.sample_names[:n]],
            }),
            n,
        )

        edited_names = st.data_editor(
            names_base,
            num_rows="fixed",
            use_container_width=True,
            hide_index=True,
            disabled=["#"],
            key=f"sample_names_{idx}",
            height=min(35 * n + 40, 500),
        )
        # Sync edits back to model (does not mutate names_base)
        for i, name in enumerate(edited_names["Sample Name"]):
            exp.sample_names[i] = str(name) if name else ""

    # ---- Bradford configuration (right) ----
    with col_right:
        if exp.has_bradford:
            st.markdown("##### Bradford Standard Concentrations (mg/ml)")
            st.caption("Paste a column of 8 values or edit directly.")

            conc_base = _stable_df(
                f"_conc_base_{idx}",
                lambda: pd.DataFrame({
                    "Standard": [f"Std {i+1}" for i in range(8)],
                    "Concentration": list(exp.standard_concentrations),
                }),
                8,
            )

            edited_conc = st.data_editor(
                conc_base,
                num_rows="fixed",
                use_container_width=True,
                hide_index=True,
                disabled=["Standard"],
                key=f"std_conc_{idx}",
                column_config={
                    "Concentration": st.column_config.NumberColumn(
                        format="%.3f", min_value=0.0, step=0.001,
                    ),
                },
            )
            exp.standard_concentrations = edited_conc["Concentration"].tolist()

            st.markdown(f"Standard replicates: **{exp.bradford_std_replicates}** &nbsp;|&nbsp; Sample replicates: **{exp.bradford_sample_replicates}**")

            # Per-sample Bradford toggle
            st.markdown("##### Bradford Normalization per Sample")
            st.caption("Uncheck to exclude specific samples from Bradford normalization.")

            # Toggles are checkboxes — not affected by paste issues,
            # so rebuilding each run is fine and keeps sample names current.
            toggle_df = pd.DataFrame({
                "#": list(range(1, n + 1)),
                "Sample": [exp.sample_names[i] or f"Sample {i+1}" for i in range(n)],
                "Normalize": exp.bradford_enabled[:n],
            })
            edited_toggle = st.data_editor(
                toggle_df,
                num_rows="fixed",
                use_container_width=True,
                hide_index=True,
                disabled=["#", "Sample"],
                key=f"bradford_toggle_{idx}",
                height=min(35 * n + 40, 400),
            )
            for i, val in enumerate(edited_toggle["Normalize"]):
                exp.bradford_enabled[i] = bool(val)
        else:
            st.info("No Bradford data for this experiment. Only raw luminescence will be reported.")
