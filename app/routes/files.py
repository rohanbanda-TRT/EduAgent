from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional, List
import os
import shutil
from datetime import datetime
from bson import ObjectId
import uuid

from app.schemas.file import FileCreate, FileResponse
from app.utils.auth import get_current_organization
from app.database.mongodb import MongoDB, FILES_COLLECTION

router = APIRouter()

# Define allowed file types
ALLOWED_PDF_TYPES = ["application/pdf"]
ALLOWED_VIDEO_TYPES = [
    "video/mp4", 
    "video/mpeg", 
    "video/quicktime", 
    "video/x-msvideo", 
    "video/x-ms-wmv"
]

# Create upload directories if they don't exist
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
PDF_DIR = os.path.join(UPLOAD_DIR, "pdfs")
VIDEO_DIR = os.path.join(UPLOAD_DIR, "videos")

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

@router.post("/upload/pdf", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: UploadFile = File(...),
    display_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated tags
    current_organization = Depends(get_current_organization)
):
    """
    Upload a PDF file. Only accessible by organizations.
    """
    # Check file type
    if file.content_type not in ALLOWED_PDF_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Must be one of: {', '.join(ALLOWED_PDF_TYPES)}"
        )
    
    # Generate unique filename for storage
    file_extension = os.path.splitext(file.filename)[1]
    storage_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(PDF_DIR, storage_filename)
    
    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Process tags if provided
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    # Create file document
    file_data = {
        "original_filename": file.filename,
        "display_name": display_name or file.filename,
        "file_type": "pdf",
        "content_type": file.content_type,
        "organization_id": current_organization["_id"],
        "description": description,
        "tags": tag_list,
        "file_path": file_path,
        "storage_filename": storage_filename,
        "file_size": file_size,
        "uploaded_by": current_organization["name"],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # Insert into database
    file_collection = MongoDB.get_collection(FILES_COLLECTION)
    result = await file_collection.insert_one(file_data)
    
    # Get the created file record
    created_file = await file_collection.find_one({"_id": result.inserted_id})
    
    return created_file

@router.post("/upload/video", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    display_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated tags
    current_organization = Depends(get_current_organization)
):
    """
    Upload a video file. Only accessible by organizations.
    """
    # Check file type
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Must be one of: {', '.join(ALLOWED_VIDEO_TYPES)}"
        )
    
    # Generate unique filename for storage
    file_extension = os.path.splitext(file.filename)[1]
    storage_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(VIDEO_DIR, storage_filename)
    
    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Process tags if provided
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    # Create file document
    file_data = {
        "original_filename": file.filename,
        "display_name": display_name or file.filename,
        "file_type": "video",
        "content_type": file.content_type,
        "organization_id": current_organization["_id"],
        "description": description,
        "tags": tag_list,
        "file_path": file_path,
        "storage_filename": storage_filename,
        "file_size": file_size,
        "uploaded_by": current_organization["name"],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # Insert into database
    file_collection = MongoDB.get_collection(FILES_COLLECTION)
    result = await file_collection.insert_one(file_data)
    
    # Get the created file record
    created_file = await file_collection.find_one({"_id": result.inserted_id})
    
    return created_file

@router.get("/organization/{org_id}", response_model=List[FileResponse])
async def get_files_by_organization(
    org_id: str,
    current_organization = Depends(get_current_organization)
):
    """
    Get all files for an organization. Only accessible by the organization.
    """
    # Verify that the organization is requesting their own files
    if str(current_organization["_id"]) != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access files from other organizations"
        )
    
    # Get files for this organization
    file_collection = MongoDB.get_collection(FILES_COLLECTION)
    files = await file_collection.find({"organization_id": ObjectId(org_id)}).to_list(1000)
    
    return files

@router.get("/{file_id}", response_model=FileResponse)
async def get_file_by_id(
    file_id: str,
    current_organization = Depends(get_current_organization)
):
    """
    Get a specific file by ID. Only accessible by the organization that owns the file.
    """
    # Get the file
    file_collection = MongoDB.get_collection(FILES_COLLECTION)
    file = await file_collection.find_one({"_id": ObjectId(file_id)})
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Verify that the organization owns the file
    if str(file["organization_id"]) != str(current_organization["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this file"
        )
    
    return file
