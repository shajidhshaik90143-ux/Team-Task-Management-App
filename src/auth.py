import bcrypt
import streamlit as st
from .db import get_conn

def authenticate(email, password):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE lower(email)=lower(?)", (email.strip(),)).fetchone()
    conn.close()
    if not row:
        return None
    try:
        valid = bcrypt.checkpw(password.encode(), row["password_hash"])
    except Exception:
        valid = False
    return dict(row) if valid else None

def register(name, email, password, role="Member"):
    conn = get_conn()
    try:
        ph = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        cur = conn.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
                           (name.strip(), email.strip().lower(), ph, role))
        conn.commit()
        uid = cur.lastrowid
        return uid, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()

def login_ui():
    st.markdown("""
    <div style="text-align:center;padding:40px 0 20px">
      <div style="font-size:64px">✅</div>
      <h1>Team Task Management</h1>
      <p style="color:#64748b;font-size:18px">Plan work. Collaborate. Deliver.</p>
    </div>
    """, unsafe_allow_html=True)

    login_tab, register_tab = st.tabs(["🔐 Sign In", "➕ Create Account"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
        if submitted:
            user = authenticate(email, password)
            if user:
                st.session_state.user = user
                st.session_state.page = "Dashboard"
                st.rerun()
            else:
                st.error("Invalid email or password.")

        with st.expander("Demo accounts"):
            st.code("admin@demo.com / Admin@123\nmanager@demo.com / Manager@123\ndeveloper@demo.com / Developer@123")

    with register_tab:
        with st.form("register_form"):
            name = st.text_input("Full name")
            email = st.text_input("Email address")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            role = st.selectbox("Role", ["Member", "Developer", "Designer", "QA", "Manager"])
            submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
        if submitted:
            if len(name.strip()) < 2 or "@" not in email:
                st.error("Enter a valid name and email.")
            elif len(password) < 8:
                st.error("Password must contain at least 8 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                uid, err = register(name, email, password, role)
                if err:
                    st.error("Account could not be created. Email may already exist.")
                else:
                    st.success("Account created. You can now sign in.")
