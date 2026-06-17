import streamlit as st
from auth.database import get_user_by_email, create_user
from auth.security import validate_email, validate_password_strength, hash_password

def show_signup_page():
    """
    Renders the Sign Up interface page in Streamlit.
    Enforces email validation, strength requirements, confirmation matching, 
    and checks for duplicate email records in SQLite.
    """
    st.markdown(
        """
        <div style="text-align: center; padding: 10px 0;">
            <h2 style="color: #1E88E5; margin-bottom: 5px;">🎨 Join AI Art Critic</h2>
            <p style="opacity: 0.8; font-size: 0.95em;">Create an account to get professional feedback on your artwork</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    with st.container(border=True):
        name = st.text_input("Full Name", placeholder="e.g. John Doe")
        email = st.text_input("Email Address", placeholder="e.g. john.doe@example.com")
        password = st.text_input("Password", type="password", placeholder="At least 8 characters")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Repeat your password")
        
        # Display password strength hint dynamically
        if password:
            is_strong, msg = validate_password_strength(password)
            if not is_strong:
                st.info(f"💡 Hint: {msg}")
            else:
                st.success("✔ Strong password!")

        submit = st.button("🚀 Register Account", use_container_width=True)
        
        if submit:
            if not name.strip():
                st.error("Please enter your Full Name.")
            elif not email.strip():
                st.error("Please enter your Email Address.")
            elif not validate_email(email):
                st.error("Please enter a valid email address.")
            elif not password:
                st.error("Please enter a password.")
            elif password != confirm_password:
                st.error("Passwords do not match. Please verify confirmation password.")
            else:
                is_strong, msg = validate_password_strength(password)
                if not is_strong:
                    st.error(f"Weak Password: {msg}")
                else:
                    # Check for duplicate email
                    existing_user = get_user_by_email(email)
                    if existing_user:
                        st.error("An account with this email address already exists. Please login.")
                    else:
                        # Hash password and insert user into database
                        try:
                            hashed = hash_password(password)
                            create_user(name, email, hashed)
                            st.success("🎉 Registration successful! Redirecting to login...")
                            st.session_state.auth_page = "login"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Registration failed: {e}")
                            
    st.markdown("<div style='text-align: center; margin-top: 10px;'>", unsafe_allow_html=True)
    if st.button("Already have an account? Login here", use_container_width=True):
        st.session_state.auth_page = "login"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
