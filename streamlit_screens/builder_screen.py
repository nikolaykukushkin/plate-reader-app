"""Screen 2: Experiment builder with interactive grid selection."""
import streamlit as st
import pandas as pd
import numpy as np

from app.data_model import AppState, Experiment, CellSelection, _col_letter


# ---- helpers ---------------------------------------------------------------

def _col_index(name) -> int:
    """Convert a column name back to a 0-based integer index.

    Handles int pass-through, spreadsheet letters ('A'->0, 'Z'->25, 'AA'->26),
    and any other string by returning 0 as fallback.
    """
    if isinstance(name, int):
        return name
    if isinstance(name, str) and name.isalpha():
        result = 0
        for ch in name.upper():
            result = result * 26 + (ord(ch) - ord('A') + 1)
        return result - 1
    try:
        return int(name)
    except (ValueError, TypeError):
        return 0


def _cells_to_selection(cells) -> CellSelection:
    """Convert st.dataframe selection dict/tuple list to a CellSelection rectangle."""
    if cells and isinstance(cells[0], (tuple, list)):
        rows = [c[0] for c in cells]
        cols = [_col_index(c[1]) for c in cells]
    else:
        rows = [c["row"] for c in cells]
        cols = [_col_index(c["column"]) for c in cells]
    return CellSelection(
        row_start=min(rows), row_end=max(rows) + 1,
        col_start=min(cols), col_end=max(cols) + 1,
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


def _led_html(on, label, css_class):
    """Return HTML for one LED dot + label."""
    cls = css_class if on else "led-off"
    color = {"led-lumi": "#60a5fa", "led-std": "#f472b6", "led-smp": "#a78bfa"}.get(css_class, "#ccc")
    label_color = color if on else "#bbb"
    return (
        f'<span class="led {cls}"></span>'
        f'<span class="led-label" style="color:{label_color}">{label}</span>'
    )


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

    st.markdown("### Experiment Builder")

    grid_col, panel_col = st.columns([5, 2], gap="medium")

    # ================================================================
    # RIGHT PANEL — tiles + active detail
    # ================================================================
    with panel_col:
        for i, exp in enumerate(app.experiments):
            _render_tile(app, i, exp, i == app.active_experiment_idx)

        if st.button("+ New Experiment", use_container_width=True):
            idx = app.add_experiment(name=f"Experiment {len(app.experiments) + 1}")
            app.active_experiment_idx = idx
            st.rerun()

        if app.experiments:
            st.markdown("---")
            _render_active_detail(app)

    # ================================================================
    # LEFT PANEL — spreadsheet + assign buttons
    # ================================================================
    with grid_col:
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

        # --- assign buttons ---
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


# ---- tile ------------------------------------------------------------------

def _render_tile(app: AppState, idx: int, exp: Experiment, is_active: bool):
    """Fixed-size compact tile. The button IS the tile — click to activate."""
    name = exp.name or f"Experiment {idx + 1}"

    # Button = the entire clickable tile surface
    c_btn, c_del = st.columns([6, 1])
    with c_btn:
        if st.button(
            name[:22],
            key=f"tile_{idx}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            app.active_experiment_idx = idx
            st.rerun()
    with c_del:
        if st.button("\u2716", key=f"del_{idx}"):
            app.remove_experiment(idx)
            st.rerun()

    # LED status dots
    leds = (
        _led_html(bool(exp.luminescence_selections), "L", "led-lumi")
        + _led_html(bool(exp.bradford_standard_selections), "S", "led-std")
        + _led_html(bool(exp.bradford_sample_selections), "B", "led-smp")
    )
    st.markdown(f'<div class="tile-leds">{leds}</div>', unsafe_allow_html=True)


# ---- active experiment detail ----------------------------------------------

def _render_active_detail(app: AppState):
    """Compact editing panel for the currently active experiment."""
    idx = app.active_experiment_idx
    exp = app.experiments[idx]

    st.markdown('<div class="detail-panel">', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        exp.name = st.text_input(
            "Name", value=exp.name, key=f"an_{idx}",
            label_visibility="collapsed", placeholder="Name",
        )
    with c2:
        exp.date = st.text_input(
            "Date", value=exp.date, key=f"ad_{idx}",
            label_visibility="collapsed", placeholder="Date",
        )
    with c3:
        exp.operator = st.text_input(
            "Op", value=exp.operator, key=f"ao_{idx}",
            label_visibility="collapsed", placeholder="Op",
        )

    # Selection badges
    badges = []
    for sels, label, cls in [
        (exp.luminescence_selections, "Lumi", "badge-lumi"),
        (exp.bradford_standard_selections, "Std", "badge-std"),
        (exp.bradford_sample_selections, "Smp", "badge-bradford"),
    ]:
        if sels:
            n = sum(s.num_cells for s in sels)
            locs = " + ".join(s.label() for s in sels)
            badges.append(
                f'<span class="sel-badge {cls}">{label}: {n}</span> '
                f'<span style="font-size:.7em;color:#888">{locs}</span>'
            )
    if badges:
        st.markdown("<br>".join(badges), unsafe_allow_html=True)
    else:
        st.markdown(
            '<span class="sel-badge badge-none">No selections yet</span>',
            unsafe_allow_html=True,
        )

    # Stats
    parts = []
    if exp.num_samples > 0:
        parts.append(f"{exp.num_samples} samples")
    if exp.has_bradford:
        parts.append(f"std\u00d7{exp.bradford_std_replicates}")
        parts.append(f"smp\u00d7{exp.bradford_sample_replicates}")
    if parts:
        st.caption(" \u00b7 ".join(parts))
    if exp.has_bradford and not exp.bradford_sample_replicates_valid:
        st.error("Uneven replicate count!")

    st.markdown('</div>', unsafe_allow_html=True)


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
