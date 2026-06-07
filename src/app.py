import os
import streamlit as st

def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable '{name}' not found")
    return value

APP_NAME = get_required_env("APP_NAME")
APP_VERSION = get_required_env("APP_VERSION")
APP_ENV = get_required_env("APP_ENV")
DATA_PATH = get_required_env("DATA_PATH")

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🦚",
)

st.title(f"{APP_NAME} - {APP_ENV}")
st.write("The Dockerized Streamlit App is running successfully!")
st.subheader("Application Details")
st.write(f"App Name: {APP_NAME}")
st.write(f"App Version: {APP_VERSION}")
st.write(f"App Environment: {APP_ENV}")
st.write(f"Data Path: {DATA_PATH}")

if os.path.exists(DATA_PATH):
    st.success(f"CSV data file found at: {DATA_PATH}")
else:    
    st.error(f"CSV data file not found at: {DATA_PATH}")