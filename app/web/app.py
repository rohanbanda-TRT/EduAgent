import streamlit as st
import requests
import json
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="EduAgent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_BASE_URL = "http://localhost:8000/api"

# Initialize session state variables
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "token" not in st.session_state:
    st.session_state.token = None
if "user_data" not in st.session_state:
    st.session_state.user_data = None

def login(user_type, identifier, password):
    """Handle login for both organization and student"""
    endpoint = f"{API_BASE_URL}/{user_type}/login"
    
    if user_type == "organization":
        payload = {"email": identifier, "password": password}
    else:  # student
        payload = {"identifier": identifier, "password": password}
    
    try:
        response = requests.post(endpoint, json=payload)
        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.user_type = user_type
            st.session_state.token = data["access_token"]
            
            # Get user data
            if user_type == "organization":
                org_response = requests.get(
                    f"{API_BASE_URL}/organization/me",
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                if org_response.status_code == 200:
                    st.session_state.user_data = org_response.json()
            else:
                student_response = requests.get(
                    f"{API_BASE_URL}/student/me",
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                if student_response.status_code == 200:
                    st.session_state.user_data = student_response.json()
            
            return True
        else:
            st.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return False

def logout():
    """Clear session state and log out user"""
    st.session_state.authenticated = False
    st.session_state.user_type = None
    st.session_state.token = None
    st.session_state.user_data = None

def show_login_page():
    """Display login interface"""
    st.title("EduAgent Login")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Organization Login")
        org_email = st.text_input("Email", key="org_email")
        org_password = st.text_input("Password", type="password", key="org_password")
        if st.button("Login as Organization"):
            if login("organization", org_email, org_password):
                st.rerun()
    
    with col2:
        st.subheader("Student Login")
        student_id = st.text_input("Student ID or Email", key="student_id")
        student_password = st.text_input("Password", type="password", key="student_password")
        if st.button("Login as Student"):
            if login("student", student_id, student_password):
                st.rerun()

def main():
    """Main application logic"""
    # Sidebar with logout option if authenticated
    if st.session_state.authenticated:
        with st.sidebar:
            st.write(f"Logged in as: {st.session_state.user_data.get('name', 'User')}")
            st.write(f"Type: {st.session_state.user_type.capitalize()}")
            if st.button("Logout"):
                logout()
                st.rerun()
    
    # Main content
    if not st.session_state.authenticated:
        show_login_page()
    else:
        if st.session_state.user_type == "organization":
            from app.web.admin_panel import show_admin_panel
            show_admin_panel()
        else:  # student
            from app.web.student_panel import show_student_panel
            show_student_panel()

if __name__ == "__main__":
    main()
