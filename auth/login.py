import streamlit as st
from auth.database import get_user_by_email
from auth.security import verify_password

def show_login_page():
    """
    Renders the Login interface page in Streamlit.
    Validates user credentials against SQLite records, hashes them, 
    and handles session state settings upon success.
    """
    st.markdown(
        """
        <div style="text-align: center; padding: 10px 0;">
            <h1 style="color: #1E88E5; font-size: 2.3em; margin-bottom: 5px;">🎨 AI Art Critic</h1>
            <p style="opacity: 0.8; font-size: 1.05em;">Professional Art Feedback in Seconds</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center; margin-top: 0;'>Sign In</h3>", unsafe_allow_html=True)
        email = st.text_input("Email Address", placeholder="e.g. john.doe@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        submit = st.button("🚀 Log In", use_container_width=True)
        
        if submit:
            if not email.strip() or not password:
                st.error("Please enter both your email address and password.")
            else:
                # Query database for user
                user = get_user_by_email(email)
                if user and verify_password(password, user["password_hash"]):
                    # Successfully authenticated! Store user parameters in Streamlit Session State
                    st.session_state.authenticated = True
                    st.session_state.user_id = user["id"]
                    st.session_state.user_name = user["name"]
                    st.session_state.user_email = user["email"]
                    
                    # Force a refresh to load the main dashboard overview page
                    st.success(f"Welcome back, {user['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid email address or password.")

    # Footer navigation columns
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔑 Forgot Password?", use_container_width=True):
            st.session_state.auth_page = "forgot_password"
            st.rerun()
    with c2:
        if st.button("🆕 Create Account", use_container_width=True):
            st.session_state.auth_page = "signup"
            st.rerun()
