#!/usr/bin/env python3
"""
Plate Reader Data Processor - Streamlit Web Application (v2)
"""
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from app.data_model import AppState
from streamlit_screens.styles import apply_global_styles
from streamlit_screens.upload_screen import render_upload
from streamlit_screens.builder_screen import render_builder
from streamlit_screens.samples_screen import render_samples
from streamlit_screens.results_screen import render_results

# Page config
st.set_page_config(
    page_title="Plate Reader Data Processor",
    page_icon="\U0001f9ec",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_styles()


def init_state():
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState()


init_state()

screen = st.session_state.app_state.current_screen

if screen == "upload":
    render_upload()
elif screen == "builder":
    render_builder()
elif screen == "samples":
    render_samples()
elif screen == "results":
    render_results()
else:
    st.session_state.app_state.current_screen = "upload"
    st.rerun()
