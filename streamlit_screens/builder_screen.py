"""Screen 2: Experiment builder with interactive grid selection."""
import streamlit as st
import pandas as pd
import numpy as np

from app.data_model import AppState, Experiment, CellSelection, _col_letter


# ---- helpers ---------------------------------------------------------------

def _cells_to_selection(cells) -> CellSelection:
    """Convert st.dataframe selection dict/tuple list to a CellSelection rectangle."""
    if cells and isinstance(cells[0], (tuple, list)):
        rows = [c[0] for c in cells]
        cols = [c[1] for c in cells]
    else:
        rows = [c["row"] for c in cells]
        cols = [c["column"] for c in cells]
    return CellSelection(
        row_start=min(rows),
        row_end=max(rows) + 1,
        col_start=min(cols),
        col_end=max(cols) + 1,
    )


def _sel_pills(selections, label, color):
    """One-line HTML summary of selections."""
    if not selections:
        return f'<span style="color:#aaa;font-size:.82em">{label}: —</span>'
    total = sum(s.num_cells for s in selections)
    locs = " + ".join(s.label() for s in selections)
    return (
        f'<span style="background:{color};padding:1px 7px;border-radius:10px;'
        f'font-size:.78em;font-weight:500">{label}: {total}</span> '
        f'<span style="font-size:.72em;color:#666">{locs}</span>'
    )


def _get_pending(event):
    """Extract a CellSelection from the dataframe selection event, or None."""
    if not event:
        return None
    sel = event.selection if hasattr(event, "selection") else None
    if sel is None:
        return None
    cells = sel.get("cells") if isinstance(sel, dict) else getattr(sel, "cells", None)
    if cells and len(cells) > 0:
        return _cells_to_selection(cells)
    return None


# ---- main render -----------------------------------------------------------

def render_builder():
    app: AppState = st.session_state.app_state
    df = app.raw_dataframe

    if df is None:
        st.warning("No file loaded.")
        if st.button("\u2190 Back to Upload"):
            app.current_screen = "upload"
            st.rerun()
        return

    st.title("Experiment Builder")

    # ---- layout: grid (left, wide) + experiment panel (right) ----
    grid_col, panel_col = st.columns([5, 2], gap="medium")

    # ================================================================
    # RIGHT PANEL — compact experiment tiles
    # ================================================================
    with panel_col:
        # --- experiment tiles ---
        for i, exp in enumerate(app.experiments):
            is_active = i == app.active_experiment_idx
            _render_experiment_tile(app, i, exp, is_active)

        # --- add button ---
        if st.button("+ New Experiment", use_container_width=True):
            idx = app.add_experiment(name=f"Experiment {len(app.experiments) + 1}")
            app.active_experiment_idx = idx
            st.rerun()

    # ================================================================
    # LEFT PANEL — spreadsheet + assign buttons
    # ================================================================
    with grid_col:
        # Display grid with letter column headers
        display_df = df.copy()
        display_df.columns = [_col_letter(c) for c in range(len(display_df.columns))]

        event = st.dataframe(
            display_df,
            selection_mode="multi-cell",
            on_select="rerun",
            key="grid_selector",
            use_container_width=True,
            height=480,
        )

        pending = _get_pending(event)

        # --- assign buttons (always visible) ---
        has_exp = bool(app.experiments)
        active_exp = app.experiments[app.active_experiment_idx] if has_exp else None
        sel_label = f" ({pending.num_cells})" if pending else ""
        can_assign = pending is not None and active_exp is not None

        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button(
                f"Luminescence{sel_label}", type="primary",
                disabled=not can_assign, use_container_width=True,
            ):
                active_exp.luminescence_selections.append(pending)
                active_exp.clear_results()
                st.rerun()
        with b2:
            if st.button(
                f"Bradford Std{sel_label}",
                disabled=not can_assign, use_container_width=True,
            ):
                active_exp.bradford_standard_selections.append(pending)
                active_exp.clear_results()
                st.rerun()
        with b3:
            if st.button(
                f"Bradford Smp{sel_label}",
                disabled=not can_assign, use_container_width=True,
            ):
                active_exp.bradford_sample_selections.append(pending)
                active_exp.clear_results()
                st.rerun()
        with b4:
            if st.button(
                "Clear", disabled=active_exp is None, use_container_width=True,
            ):
                active_exp.luminescence_selections.clear()
                active_exp.bradford_standard_selections.clear()
                active_exp.bradford_sample_selections.clear()
                active_exp.clear_results()
                st.rerun()

        # --- selection map ---
        _render_selection_map(df, app.experiments)

    # ---- Navigation ----
    st.markdown("---")
    c_back, _, c_next = st.columns([1, 2, 1])
    with c_back:
        if st.button("\u2190 Back to Upload", use_container_width=True):
            app.current_screen = "upload"
            st.rerun()
    with c_next:
        any_lumi = any(e.num_samples > 0 for e in app.experiments)
        bradford_ok = all(e.bradford_sample_replicates_valid for e in app.experiments)
        if st.button(
            "Continue to Sample Config \u2192", type="primary",
            disabled=not any_lumi or not bradford_ok, use_container_width=True,
        ):
            for e in app.experiments:
                e.ensure_lists_sized()
            app.current_screen = "samples"
            st.rerun()
        if not any_lumi:
            st.caption("Select luminescence cells for at least one experiment.")
        if not bradford_ok:
            st.caption("Fix uneven Bradford replicate counts before continuing.")


# ---- experiment tile -------------------------------------------------------

def _render_experiment_tile(app: AppState, idx: int, exp: Experiment, is_active: bool):
    """Render a single compact experiment tile. Click anywhere to activate."""
    border_color = "#4361ee" if is_active else "#d0d0d0"
    bg = "#f0f4ff" if is_active else "#fff"
    indicator = "\u25cf" if is_active else "\u25cb"

    # Tile wrapper
    st.markdown(
        f'<div style="border:2px solid {border_color};background:{bg};'
        f'border-radius:8px;padding:10px 12px;margin-bottom:6px">',
        unsafe_allow_html=True,
    )

    # Row 1: indicator + name + delete
    c_ind, c_name, c_del = st.columns([0.3, 3.5, 0.5])
    with c_ind:
        # Clickable indicator to activate
        if st.button(indicator, key=f"act_{idx}", help="Activate this experiment"):
            app.active_experiment_idx = idx
            st.rerun()
    with c_name:
        exp.name = st.text_input(
            "n", value=exp.name, key=f"tn_{idx}",
            label_visibility="collapsed", placeholder="Name",
        )
    with c_del:
        if st.button("\u2716", key=f"td_{idx}", help="Remove"):
            app.remove_experiment(idx)
            st.rerun()

    # Row 2: date + operator (compact)
    c_d, c_o = st.columns(2)
    with c_d:
        exp.date = st.text_input(
            "d", value=exp.date, key=f"td2_{idx}",
            label_visibility="collapsed", placeholder="Date",
        )
    with c_o:
        exp.operator = st.text_input(
            "o", value=exp.operator, key=f"to_{idx}",
            label_visibility="collapsed", placeholder="Initials",
        )

    # Selection summary lines
    st.markdown(
        _sel_pills(exp.luminescence_selections, "Lumi", "#dbeafe") + "<br>"
        + _sel_pills(exp.bradford_standard_selections, "Std", "#fce7f3") + "<br>"
        + _sel_pills(exp.bradford_sample_selections, "Smp", "#e8d5f5"),
        unsafe_allow_html=True,
    )

    # Stats line
    parts = []
    if exp.num_samples > 0:
        parts.append(f"{exp.num_samples} samples")
    if exp.has_bradford:
        parts.append(f"std reps {exp.bradford_std_replicates}")
        parts.append(f"smp reps {exp.bradford_sample_replicates}")
    if parts:
        st.caption(" · ".join(parts))
    if exp.has_bradford and not exp.bradford_sample_replicates_valid:
        st.error("Uneven replicate count!")

    st.markdown("</div>", unsafe_allow_html=True)


# ---- selection map ---------------------------------------------------------

def _render_selection_map(df, experiments):
    """Compact color-coded map of which cells are assigned where."""
    if not experiments or not any(
        e.luminescence_selections or e.bradford_standard_selections or e.bradford_sample_selections
        for e in experiments
    ):
        return

    st.markdown("##### Selection Map")

    nrows, ncols = df.shape
    tag_grid = [[""] * ncols for _ in range(nrows)]

    colors = ["#dbeafe", "#fce7f3", "#d1fae5", "#fef3c7", "#e0e7ff", "#fde68a"]

    for ei, exp in enumerate(experiments):
        color = colors[ei % len(colors)]
        short = exp.name[:6] if exp.name else f"E{ei+1}"
        for sel in exp.luminescence_selections:
            for r in range(sel.row_start, min(sel.row_end, nrows)):
                for c in range(sel.col_start, min(sel.col_end, ncols)):
                    tag_grid[r][c] = f'<span style="background:{color};padding:0 4px;border-radius:3px;font-size:.68em">{short} L</span>'
        for sel in exp.bradford_standard_selections:
            for r in range(sel.row_start, min(sel.row_end, nrows)):
                for c in range(sel.col_start, min(sel.col_end, ncols)):
                    tag_grid[r][c] = f'<span style="background:{color};padding:0 4px;border-radius:3px;font-size:.68em">{short} S</span>'
        for sel in exp.bradford_sample_selections:
            for r in range(sel.row_start, min(sel.row_end, nrows)):
                for c in range(sel.col_start, min(sel.col_end, ncols)):
                    tag_grid[r][c] = f'<span style="background:{color};padding:0 4px;border-radius:3px;font-size:.68em">{short} B</span>'

    used_rows = [r for r in range(nrows) if any(tag_grid[r])]
    used_cols = [c for c in range(ncols) if any(tag_grid[r][c] for r in range(nrows))]
    if not used_rows or not used_cols:
        return

    html = '<div style="overflow-x:auto"><table style="border-collapse:collapse;font-size:.78em">'
    html += "<tr><th></th>"
    for c in used_cols:
        html += f"<th style='padding:1px 5px'>{_col_letter(c)}</th>"
    html += "</tr>"
    for r in used_rows:
        html += f"<tr><td style='padding:1px 5px;color:#999'>{r+1}</td>"
        for c in used_cols:
            html += f"<td style='padding:1px 3px;text-align:center'>{tag_grid[r][c]}</td>"
        html += "</tr>"
    html += "</table></div>"
    st.markdown(html, unsafe_allow_html=True)
