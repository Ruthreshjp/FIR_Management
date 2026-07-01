import streamlit as st
from app.styles import CUSTOM_CSS


def load_custom_css():
    """
    Injects the AutoFIR design system.
    All CSS rules live in app/styles.py as a single constant.
    """
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
