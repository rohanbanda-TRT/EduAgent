import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

def show_admin_panel():
    """Display the admin (organization) panel interface"""
    st.title("Organization Dashboard")
    
    # Get token from session state
    token = st.session_state.token
    headers = {"Authorization": f"Bearer {token}"}
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Students", "Files", "Analytics"])
    
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
                            response = requests.post(
                                f"http://localhost:8000/api/student/register",
                                headers=headers,
                                json={
                                    "student_id": student_id,
                                    "name": name,
                                    "email": email,
                                    "grade": grade,
                                    "password": password
                                }
                            )
                            
                            if response.status_code == 200:
                                st.success("Student added successfully!")
                            else:
                                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        # List all students
        st.subheader("All Students")
        try:
            response = requests.get(
                f"http://localhost:8000/api/student/all",
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
                            "Grade": student.get("grade", ""),
                            "Created At": student.get("created_at", "")
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
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "mp4"] if file_type == "Video" else ["pdf"])
        
        if uploaded_file is not None:
            if st.button("Upload File"):
                try:
                    files = {"file": uploaded_file}
                    response = requests.post(
                        f"http://localhost:8000/api/files/upload/{file_type.lower()}",
                        headers={"Authorization": f"Bearer {token}"},
                        files=files
                    )
                    
                    if response.status_code == 200:
                        st.success("File uploaded successfully!")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # List all files
        st.subheader("All Files")
        try:
            response = requests.get(
                f"http://localhost:8000/api/files/all",
                headers=headers
            )
            
            if response.status_code == 200:
                files = response.json()
                if files:
                    # Convert to DataFrame for better display
                    files_data = []
                    for file in files:
                        files_data.append({
                            "File Name": file.get("filename", ""),
                            "File Type": file.get("file_type", ""),
                            "Uploaded By": file.get("uploaded_by", ""),
                            "Uploaded At": file.get("uploaded_at", "")
                        })
                    
                    df = pd.DataFrame(files_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No files found")
            else:
                st.error(f"Error fetching files: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Tab 3: Analytics
    with tab3:
        st.header("Analytics")
        
        # Placeholder for analytics
        st.subheader("Student Activity")
        st.info("Analytics feature coming soon!")
        
        # Sample metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Students", value="0")
        with col2:
            st.metric(label="Total Files", value="0")
        with col3:
            st.metric(label="Active Students", value="0")
