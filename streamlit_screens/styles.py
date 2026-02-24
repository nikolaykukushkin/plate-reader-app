"""Global CSS styles for the Streamlit app."""
import streamlit as st


def apply_global_styles():
    st.markdown("""
    <style>
    /* --- Base typography & palette --- */
    :root {
        --primary:   #4361ee;
        --primary-l: #e8ecff;
        --accent:    #7209b7;
        --accent-l:  #f3e5f5;
        --success:   #06d6a0;
        --warn:      #ffd166;
        --danger:    #ef476f;
        --bg:        #f8f9fa;
        --card-bg:   #ffffff;
        --border:    #e0e0e0;
        --text:      #212529;
        --text-dim:  #6c757d;
    }

    /* Slightly warm background */
    .stApp {
        background: var(--bg);
    }

    /* Card-like containers */
    div[data-testid="stExpander"],
    .exp-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 10px;
    }

    /* Selection badges */
    .sel-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.82em;
        font-weight: 500;
        margin: 2px 2px;
    }
    .badge-lumi     { background: #dbeafe; color: #1e40af; }
    .badge-std      { background: #fce7f3; color: #9d174d; }
    .badge-bradford { background: var(--accent-l); color: var(--accent); }
    .badge-none     { background: #f1f5f9; color: var(--text-dim); }

    /* Tighter table rows in data_editor */
    div[data-testid="stDataEditor"] td {
        padding: 2px 8px !important;
    }

    /* Hide hamburger & footer for cleaner look */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }

    /* Progress bar accent */
    .stProgress > div > div > div { background-color: var(--primary); }

    /* Nav buttons */
    .nav-row { display: flex; gap: 8px; justify-content: space-between; }

    /* --- Synth tile LEDs --- */
    .tile-leds {
        margin: -4px 0 6px 2px;
        line-height: 1;
    }
    .led {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        vertical-align: middle;
        margin: 0 1px;
    }
    .led-label {
        font-size: .65em;
        vertical-align: middle;
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        margin-right: 6px;
    }
    .led-lumi    { background: #60a5fa; box-shadow: 0 0 5px #60a5fa; }
    .led-std     { background: #f472b6; box-shadow: 0 0 5px #f472b6; }
    .led-smp     { background: #a78bfa; box-shadow: 0 0 5px #a78bfa; }
    .led-off     { background: #ccc; }

    /* --- Active detail panel --- */
    .detail-panel {
        background: #f0f2f6;
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 10px 14px 6px 14px;
    }
    </style>
    """, unsafe_allow_html=True)
