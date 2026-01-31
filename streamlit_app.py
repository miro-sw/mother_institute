"""Minimal Streamlit frontend that calls the Django DRF endpoint at /institute/api/info/.

Usage (local):
  pip install -r requirements.txt
  # run django on :8000
  python manage.py runserver 8000
  # run streamlit
  streamlit run streamlit_app.py --server.port 8501

On Streamlit Cloud: set secret `API_URL` to the public Django API URL.
"""
import os
import streamlit as st
import requests

API = st.secrets.get("API_URL") or os.environ.get("API_URL") or "http://localhost:8000/institute/api/info/"

st.title("Mother Institute — Streamlit UI (Prototype)")
st.markdown("This is a lightweight Streamlit frontend that calls a small Django API endpoint.")

st.write("**API endpoint used:**", API)

try:
    resp = requests.get(API, timeout=6)
    resp.raise_for_status()
    data = resp.json()
    st.success("API reachable — returned JSON")
    st.json(data)
except requests.RequestException as e:
    st.error(f"Could not reach API: {e}")
    st.stop()

# Simple interactive example
if data:
    st.subheader("Quick info")
    st.write(f"App: {data.get('app')}")
    st.write(f"Status: {data.get('status')}")
    st.write(f"Version: {data.get('version')}")
    st.button("Ping")
