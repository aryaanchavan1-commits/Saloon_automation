import bcrypt
import streamlit as st
from database import SessionLocal, User

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def authenticate_user(username: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and verify_password(password, user.password_hash):
            return user
        return None
    finally:
        db.close()

def get_user_role(username: str) -> str:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        return user.role if user else "staff"
    finally:
        db.close()

def user_exists(username: str) -> bool:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.username == username).first() is not None
    finally:
        db.close()

def create_user(username: str, password: str, role: str = "admin"):
    db = SessionLocal()
    try:
        if user_exists(username):
            return False
        hashed = hash_password(password)
        db.add(User(username=username, password_hash=hashed, role=role))
        db.commit()
        return True
    finally:
        db.close()

def change_password(username: str, new_password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.password_hash = hash_password(new_password)
            db.commit()
            return True
        return False
    finally:
        db.close()

def login_page():
    st.markdown("""
    <div class="auth-screen">
        <div class="auth-card">
            <div class="auth-header">
                <div class="logo-icon">💈</div>
                <h1>Saloon Pro</h1>
                <p>Premium Management System</p>
            </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Register"])

    with tab1:
        with st.form("login_form"):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign In", width='stretch', type="primary")
                if submitted:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.session_state["role"] = user.role
                        st.rerun()
                    else:
                        st.error("Invalid username or password")

    with tab2:
        with st.form("register_form"):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                new_user = st.text_input("New Username", placeholder="Choose a username")
                new_pass = st.text_input("New Password", type="password", placeholder="Choose a password")
                confirm_pass = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
                reg_submit = st.form_submit_button("Register", width='stretch', type="primary")
                if reg_submit:
                    if not new_user or not new_pass:
                        st.warning("Please fill all fields")
                    elif new_pass != confirm_pass:
                        st.warning("Passwords do not match")
                    elif user_exists(new_user):
                        st.warning("Username already exists")
                    elif len(new_pass) < 4:
                        st.warning("Password must be at least 4 characters")
                    else:
                        if create_user(new_user, new_pass):
                            st.success("Account created! Sign in above.")
                            st.rerun()
                        else:
                            st.error("Failed to create account")

    st.markdown("</div></div>", unsafe_allow_html=True)

def check_auth():
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        login_page()
        st.stop()
