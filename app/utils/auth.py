from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

from app.schemas.organization import TokenData as OrgTokenData
from app.schemas.student import TokenData as StudentTokenData
from app.database.mongodb import MongoDB, ORGANIZATIONS_COLLECTION, STUDENTS_COLLECTION

# Load environment variables
load_dotenv()

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-jwt")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme for JWT authentication
oauth2_scheme = HTTPBearer()

def verify_password(plain_password, hashed_password):
    """Verify password against hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash a password."""
    return pwd_context.hash(password)

async def authenticate_organization(email: str, password: str):
    """Authenticate an organization."""
    org_collection = MongoDB.get_collection(ORGANIZATIONS_COLLECTION)
    organization = await org_collection.find_one({"email": email})
    
    if not organization:
        return False
    
    if not verify_password(password, organization["password"]):
        return False
    
    return organization

async def authenticate_student(identifier: str, password: str):
    """Authenticate a student using student_id or email."""
    student_collection = MongoDB.get_collection(STUDENTS_COLLECTION)
    
    # Try to find student by student_id first
    student = await student_collection.find_one({"student_id": identifier})
    
    # If not found by student_id, try email
    if not student and "@" in identifier:  # Simple check if it looks like an email
        student = await student_collection.find_one({"email": identifier})
    
    if not student:
        return False
    
    if not verify_password(password, student["password"]):
        return False
    
    return student

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        is_organization: bool = payload.get("is_organization", False)
        
        if email is None:
            raise credentials_exception
        
        if is_organization:
            token_data = OrgTokenData(email=email, is_organization=True, org_id=payload.get("org_id"))
            collection = MongoDB.get_collection(ORGANIZATIONS_COLLECTION)
            user = await collection.find_one({"email": email})
            if user is None:
                raise credentials_exception
            return {"user": user, "is_organization": True}
        else:
            student_id = payload.get("student_id")
            token_data = StudentTokenData(student_id=student_id, is_organization=False, org_id=payload.get("org_id"))
            collection = MongoDB.get_collection(STUDENTS_COLLECTION)
            user = await collection.find_one({"student_id": student_id})
            if user is None:
                raise credentials_exception
            return {"user": user, "is_organization": False}
    
    except JWTError:
        raise credentials_exception

async def get_current_organization(current_user = Depends(get_current_user)):
    """Get current organization from JWT token."""
    if not current_user["is_organization"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Organization access required.",
        )
    return current_user["user"]

async def get_current_student(current_user = Depends(get_current_user)):
    """Get current student from JWT token."""
    if current_user["is_organization"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Student access required.",
        )
    return current_user["user"]
