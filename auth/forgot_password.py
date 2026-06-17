import streamlit as st
from auth.database import get_user_by_email, update_user_password
from auth.security import validate_password_strength, hash_password

def show_forgot_password_page():
    """
    Renders the Password Recovery/Reset interface page in Streamlit.
    Guides the user through email verification, new password validation, 
    bcrypt hashing, and committing the reset to SQLite.
    """
    st.markdown(
        """
        <div style="text-align: center; padding: 10px 0;">
            <h2 style="color: #1E88E5; margin-bottom: 5px;">🔑 Password Recovery</h2>
            <p style="opacity: 0.8; font-size: 0.95em;">Reset your password safely and regain access</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Initialize recovery workflow states
    if "reset_step" not in st.session_state:
        st.session_state.reset_step = 1
        st.session_state.reset_email = ""

    with st.container(border=True):
        if st.session_state.reset_step == 1:
            st.markdown("<h4 style='text-align: center;'>Verify Registered Email</h4>", unsafe_allow_html=True)
            email = st.text_input("Registered Email Address", placeholder="e.g. john.doe@example.com")
            submit = st.button("🔍 Verify Email Address", use_container_width=True)
            
            if submit:
                if not email.strip():
                    st.error("Please enter your email address.")
                else:
                    # Check if email is in registry
                    user = get_user_by_email(email)
                    if user:
                        st.session_state.reset_email = user["email"]
                        st.session_state.reset_step = 2
                        st.success("Email address verified! Please enter your new password below.")
                        st.rerun()
                    else:
                        st.error("Email address not found in database registry.")
                        
        elif st.session_state.reset_step == 2:
            st.markdown(f"<h4 style='text-align: center;'>Resetting Password for: <br/><code style='font-size:0.85em; color:#1E88E5;'>{st.session_state.reset_email}</code></h4>", unsafe_allow_html=True)
            
            new_password = st.text_input("New Password", type="password", placeholder="At least 8 characters")
            confirm_new_password = st.text_input("Confirm New Password", type="password", placeholder="Repeat your new password")
            
            # Dynamic password strength validation feedback
            if new_password:
                is_strong, msg = validate_password_strength(new_password)
                if not is_strong:
                    st.info(f"💡 Hint: {msg}")
                else:
                    st.success("✔ Strong password!")
                    
            submit_reset = st.button("💾 Save New Password", use_container_width=True)
            
            if submit_reset:
                if not new_password:
                    st.error("Please enter a new password.")
                elif new_password != confirm_new_password:
                    st.error("New passwords do not match. Please verify confirmation password.")
                else:
                    is_strong, msg = validate_password_strength(new_password)
                    if not is_strong:
                        st.error(f"Weak Password: {msg}")
                    else:
                        # Hash the new password and update record in users table
                        try:
                            hashed = hash_password(new_password)
                            update_user_password(st.session_state.reset_email, hashed)
                            st.success("🎉 Password reset successfully! Redirecting to login...")
                            
                            # Reset security recover states
                            st.session_state.reset_step = 1
                            st.session_state.reset_email = ""
                            st.session_state.auth_page = "login"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to reset password: {e}")
                            
            if st.button("Cancel & Start Over", use_container_width=True):
                st.session_state.reset_step = 1
                st.session_state.reset_email = ""
                st.rerun()
                
    st.markdown("<div style='text-align: center; margin-top: 10px;'>", unsafe_allow_html=True)
    if st.button("Back to Login", use_container_width=True):
        st.session_state.reset_step = 1
        st.session_state.reset_email = ""
        st.session_state.auth_page = "login"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
