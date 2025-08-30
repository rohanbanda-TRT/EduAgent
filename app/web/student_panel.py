import streamlit as st
import requests
import pandas as pd
from datetime import datetime

def show_student_panel():
    """Display the student panel interface"""
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
    
    # Tabs for different sections
    tab1, tab2 = st.tabs(["Learning Materials", "My Progress"])
    
    # Tab 1: Learning Materials
    with tab1:
        st.header("Learning Materials")
        
        # Filter options
        st.subheader("Filter Materials")
        file_type = st.selectbox("File Type", ["All", "PDF", "Video"])
        
        # Get all files
        try:
            response = requests.get(
                f"http://localhost:8000/api/files/all",
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
                    st.subheader("Available Materials")
                    
                    # Display files in a grid
                    cols = st.columns(2)
                    for i, file in enumerate(files):
                        with cols[i % 2]:
                            with st.container():
                                st.markdown(f"**{file.get('filename', 'Unnamed')}**")
                                st.write(f"Type: {file.get('file_type', 'Unknown')}")
                                st.write(f"Uploaded: {file.get('uploaded_at', 'Unknown')}")
                                
                                # Download button
                                if st.button(f"View {file.get('filename', 'File')}", key=f"view_{i}"):
                                    file_id = file.get("_id")
                                    if file_id:
                                        # Redirect to file view/download endpoint
                                        file_type = file.get("file_type", "").lower()
                                        st.markdown(f"[Download File](http://localhost:8000/api/files/download/{file_type}/{file_id})")
                else:
                    st.info("No learning materials available")
            else:
                st.error(f"Error fetching materials: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Tab 2: My Progress
    with tab2:
        st.header("My Progress")
        
        # Placeholder for progress tracking
        st.info("Progress tracking feature coming soon!")
        
        # Sample progress metrics
        st.subheader("Learning Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Materials Viewed", value="0")
        with col2:
            st.metric(label="Quizzes Completed", value="0")
        with col3:
            st.metric(label="Average Score", value="0%")
        
        # Placeholder for progress chart
        st.subheader("Learning Progress")
        st.line_chart({"Progress": [0, 10, 15, 40, 25, 50, 60]})
        
        # Placeholder for recent activity
        st.subheader("Recent Activity")
        st.write("No recent activity")
