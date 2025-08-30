from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from bson import ObjectId

from app.schemas.student import StudentCreate, StudentResponse, StudentLogin
from app.schemas.organization import Token
from app.utils.auth import (
    authenticate_student, 
    create_access_token, 
    get_password_hash, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_student,
    get_current_organization
)
from app.database.mongodb import MongoDB, STUDENTS_COLLECTION, ORGANIZATIONS_COLLECTION

router = APIRouter()

@router.post("/signup", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(student: StudentCreate):
    """
    Create a new student account.
    """
    # Get the students collection
    student_collection = MongoDB.get_collection(STUDENTS_COLLECTION)
    org_collection = MongoDB.get_collection(ORGANIZATIONS_COLLECTION)
    
    # Check if student with this email already exists
    existing_student = await student_collection.find_one({"email": student.email})
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if organization exists
    organization = await org_collection.find_one({"_id": student.organization_id})
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization not found"
        )
    
    # Hash the password
    hashed_password = get_password_hash(student.password)
    
    # Create student document
    student_dict = student.dict()
    student_dict["password"] = hashed_password
    
    # Insert into database
    result = await student_collection.insert_one(student_dict)
    
    # Get the created student
    created_student = await student_collection.find_one({"_id": result.inserted_id})
    
    return created_student

@router.post("/login", response_model=Token)
async def login_student(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a student and return a JWT token.
    """
    student = await authenticate_student(form_data.username, form_data.password)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": student["email"],
            "student_id": str(student["_id"]),
            "is_organization": False
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=StudentResponse)
async def read_student_me(current_student = Depends(get_current_student)):
    """
    Get current student profile.
    """
    return current_student

@router.get("/organization/{org_id}", response_model=list[StudentResponse])
async def get_students_by_organization(
    org_id: str,
    current_organization = Depends(get_current_organization)
):
    """
    Get all students for an organization. Only accessible by the organization.
    """
    # Verify that the organization is requesting their own students
    if str(current_organization["_id"]) != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access students from other organizations"
        )
    
    # Get students for this organization
    student_collection = MongoDB.get_collection(STUDENTS_COLLECTION)
    students = await student_collection.find({"organization_id": ObjectId(org_id)}).to_list(1000)
    
    return students
