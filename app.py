import streamlit as st
from neurisk.neurisk_ui import render_neurisk_tab

st.set_page_config(page_title="NeuroRisk GRC", layout="wide")

render_neurisk_tab()