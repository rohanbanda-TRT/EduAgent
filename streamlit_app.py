import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="EduAgent",
    page_icon="📚",
    layout="wide"
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
if "login_type" not in st.session_state:
    st.session_state.login_type = None

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
    st.session_state.login_type = None

def select_login_type(type_selected):
    """Set the login type in session state"""
    st.session_state.login_type = type_selected

def show_login_selector():
    """Display login type selection"""
    st.title("EduAgent Login")
    st.write("Select your login type:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Organization Login", use_container_width=True):
            select_login_type("organization")
    
    with col2:
        if st.button("Student Login", use_container_width=True):
            select_login_type("student")

def show_login_form():
    """Display login form based on selected type"""
    if st.session_state.login_type == "organization":
        st.subheader("Organization Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if login("organization", email, password):
                st.rerun()
        
        if st.button("Back"):
            st.session_state.login_type = None
            st.rerun()
    
    elif st.session_state.login_type == "student":
        st.subheader("Student Login")
        identifier = st.text_input("Student ID or Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if login("student", identifier, password):
                st.rerun()
        
        if st.button("Back"):
            st.session_state.login_type = None
            st.rerun()

def show_organization_dashboard():
    """Display organization dashboard"""
    st.title("Organization Dashboard")
    
    # Get token from session state
    token = st.session_state.token
    headers = {"Authorization": f"Bearer {token}"}
    
    # Tabs for different sections
    tab1, tab2 = st.tabs(["Students", "Files"])
    
    # Tab 1: Students Management
    with tab1:
        st.header("Students Management")
        
        # Add new student form
        with st.expander("Add New Student"):
            with st.form("add_student_form"):
                student_id = st.text_input("Student ID")
                name = st.text_input("Name")
                email = st.text_input("Email")
                grade = st.text_input("Grade")
                password = st.text_input("Password", type="password")
                
                submit_button = st.form_submit_button("Add Student")
                
                if submit_button:
                    if not student_id or not name or not password:
                        st.error("Student ID, Name, and Password are required")
                    else:
                        try:
                            # Use the new register endpoint that handles organization_id automatically
                            response = requests.post(
                                f"{API_BASE_URL}/student/register",
                                headers=headers,
                                json={
                                    "student_id": student_id,
                                    "name": name,
                                    "email": email,
                                    "grade": grade,
                                    "password": password
                                }
                            )
                            
                            if response.status_code in [200, 201]:
                                st.success("Student added successfully!")
                                # Refresh the page to show the new student
                                st.rerun()
                            else:
                                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        # List all students
        st.subheader("All Students")
        try:
            response = requests.get(
                f"{API_BASE_URL}/student/all",
                headers=headers
            )
            
            if response.status_code == 200:
                students = response.json()
                if students:
                    # Convert to DataFrame for better display
                    students_data = []
                    for student in students:
                        students_data.append({
                            "Student ID": student.get("student_id", ""),
                            "Name": student.get("name", ""),
                            "Email": student.get("email", ""),
                            "Grade": student.get("grade", "")
                        })
                    
                    df = pd.DataFrame(students_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No students found")
            else:
                st.error(f"Error fetching students: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Tab 2: Files Management
    with tab2:
        st.header("Files Management")
        
        # Upload new file
        st.subheader("Upload New File")
        file_type = st.selectbox("File Type", ["PDF", "Video"])
        uploaded_file = st.file_uploader("Choose a file", type=["mp4"] if file_type == "Video" else ["pdf"])
        
        if uploaded_file is not None:
            if st.button("Upload File"):
                try:
                    # Create a multipart form request with the file and metadata
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), 
                             "application/pdf" if file_type == "PDF" else "video/mp4")}
                    
                    response = requests.post(
                        f"{API_BASE_URL}/files/upload/{file_type.lower()}",
                        headers={"Authorization": f"Bearer {token}"},
                        files=files
                    )
                    
                    if response.status_code in [200, 201]:
                        st.success("File uploaded successfully!")
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # List all files
        st.subheader("All Files")
        try:
            response = requests.get(
                f"{API_BASE_URL}/files/all",
                headers=headers
            )
            
            if response.status_code == 200:
                files = response.json()
                if files:
                    # Convert to DataFrame for better display
                    files_data = []
                    for file in files:
                        files_data.append({
                            "File Name": file.get("display_name", file.get("original_filename", "")),
                            "File Type": file.get("file_type", "").upper(),
                            "Uploaded At": file.get("created_at", "").split("T")[0] if file.get("created_at") else ""
                        })
                    
                    df = pd.DataFrame(files_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No files found")
            else:
                st.error(f"Error fetching files: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

def show_student_dashboard():
    """Display student dashboard"""
    st.title("Student Dashboard")
    
    # Get token from session state
    token = st.session_state.token
    headers = {"Authorization": f"Bearer {token}"}
    user_data = st.session_state.user_data
    
    # Display student information
    st.subheader("My Information")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Name:** {user_data.get('name', 'N/A')}")
        st.write(f"**Student ID:** {user_data.get('student_id', 'N/A')}")
    with col2:
        st.write(f"**Email:** {user_data.get('email', 'N/A')}")
        st.write(f"**Grade:** {user_data.get('grade', 'N/A')}")
    
    # Learning Materials
    st.header("Learning Materials")
    
    # Filter options
    file_type = st.selectbox("File Type", ["All", "PDF", "Video"])
    
    # Get all files
    try:
        response = requests.get(
            f"{API_BASE_URL}/files/all",
            headers=headers
        )
        
        if response.status_code == 200:
            all_files = response.json()
            
            # Filter by type if needed
            if file_type != "All":
                files = [f for f in all_files if f.get("file_type", "").lower() == file_type.lower()]
            else:
                files = all_files
            
            if files:
                # Display files in a grid
                for i in range(0, len(files), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(files):
                            file = files[i + j]
                            with cols[j]:
                                with st.container():
                                    st.markdown(f"**{file.get('display_name', file.get('original_filename', 'Unnamed'))}**")
                                    st.write(f"Type: {file.get('file_type', 'Unknown').upper()}")
                                    st.write(f"Uploaded: {file.get('created_at', 'Unknown').split('T')[0] if file.get('created_at') else 'Unknown'}")
                                    
                                    # Download button
                                    file_id = file.get("_id")
                                    if file_id:
                                        file_type = file.get("file_type", "").lower()
                                        st.markdown(f"[Download File](http://localhost:8000/api/files/download/{file_type}/{file_id})")
            else:
                st.info("No learning materials available")
        else:
            st.error(f"Error fetching materials: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

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
        if st.session_state.login_type is None:
            show_login_selector()
        else:
            show_login_form()
    else:
        if st.session_state.user_type == "organization":
            show_organization_dashboard()
        else:  # student
            show_student_dashboard()

if __name__ == "__main__":
    main()
