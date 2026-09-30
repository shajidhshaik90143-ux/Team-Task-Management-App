import streamlit as st
from src.db import init_db, seed_demo
from src.auth import login_ui
from src.ui import render_sidebar, render_dashboard, render_tasks, render_kanban, render_team, render_analytics, render_activity

st.set_page_config(page_title="Team Task Management", page_icon="✅", layout="wide", initial_sidebar_state="expanded")

init_db()
seed_demo()

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    login_ui()
    st.stop()

render_sidebar()

page = st.session_state.get("page", "Dashboard")
if page == "Dashboard":
    render_dashboard()
elif page == "Tasks":
    render_tasks()
elif page == "Kanban Board":
    render_kanban()
elif page == "Team":
    render_team()
elif page == "Analytics":
    render_analytics()
elif page == "Activity":
    render_activity()
