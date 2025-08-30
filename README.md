# EduAgent API

A FastAPI-based backend for an educational platform with organization and student authentication, and file upload capabilities.

## Project Structure

```
app/
├── database/
│   └── mongodb.py         # MongoDB connection utility
├── routes/
│   ├── organization.py    # Organization authentication endpoints
│   ├── student.py         # Student authentication endpoints
│   └── files.py           # File upload endpoints
├── schemas/
│   ├── organization.py    # Organization data models
│   ├── student.py         # Student data models
│   └── file.py            # File data models
├── utils/
│   └── auth.py            # Authentication utilities
└── main.py                # FastAPI application entry point
```

## Features

- Organization authentication (signup/login)
- Student authentication (signup/login)
- PDF and video file uploads (organization only)
- MongoDB integration for data storage

## Setup Instructions

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file based on `.env.example`:
   ```
   cp .env.example .env
   ```
5. Update the `.env` file with your MongoDB connection details and JWT secret key
6. Make sure MongoDB is running
7. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Organization

- `POST /api/organization/signup`: Create a new organization account
- `POST /api/organization/login`: Login as an organization
- `GET /api/organization/me`: Get current organization profile

### Student

- `POST /api/student/signup`: Create a new student account
- `POST /api/student/login`: Login as a student
- `GET /api/student/me`: Get current student profile
- `GET /api/student/organization/{org_id}`: Get all students for an organization

### Files

- `POST /api/files/upload/pdf`: Upload a PDF file (organization only)
- `POST /api/files/upload/video`: Upload a video file (organization only)
- `GET /api/files/organization/{org_id}`: Get all files for an organization
- `GET /api/files/{file_id}`: Get a specific file by ID

## Authentication

The API uses JWT tokens for authentication. To access protected endpoints:

1. Login using the appropriate endpoint
2. Use the returned token in the Authorization header:
   ```
   Authorization: Bearer <your_token>
   ```
