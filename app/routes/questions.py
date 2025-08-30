"""API routes for suggested questions."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from bson import ObjectId

from app.utils.auth import get_current_organization
from app.database.mongodb import MongoDB, SUGGESTED_QUESTIONS_COLLECTION, FILES_COLLECTION
from app.schemas.suggested_question import SuggestedQuestionsResponse

router = APIRouter()

@router.get("/video/{document_id}", response_model=SuggestedQuestionsResponse)
async def get_suggested_questions(
    document_id: str,
    current_organization = Depends(get_current_organization)
):
    """
    Get suggested questions for a video document.
    
    Args:
        document_id: The document ID to retrieve questions for
        
    Returns:
        Suggested questions for the video document
    """
    try:
        # First verify that the document belongs to this organization
        file_collection = MongoDB.get_collection(FILES_COLLECTION)
        file = await file_collection.find_one({
            "document_id": document_id,
            "organization_id": current_organization["_id"],
            "file_type": "video"  # Ensure it's a video file
        })
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video document not found or you don't have access to it"
            )
        
        # Get suggested questions from the collection
        questions_collection = MongoDB.get_collection(SUGGESTED_QUESTIONS_COLLECTION)
        questions_doc = await questions_collection.find_one({
            "document_id": document_id,
            "organization_id": str(current_organization["_id"])
        })
        
        if not questions_doc:
            # If no questions found, return empty segments
            return {
                "document_id": document_id,
                "file_id": str(file["_id"]),
                "filename": file["original_filename"],
                "display_name": file["display_name"],
                "segments": []
            }
        
        # Convert ObjectId to string for JSON serialization
        questions_doc["_id"] = str(questions_doc["_id"])
        questions_doc["file_id"] = str(questions_doc["file_id"])
        
        # Format the response
        return {
            "document_id": questions_doc["document_id"],
            "file_id": questions_doc["file_id"],
            "filename": questions_doc["filename"],
            "display_name": questions_doc["display_name"],
            "segments": questions_doc["segments"]
        }
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving suggested questions: {str(e)}"
        )

@router.get("/file/{file_id}", response_model=SuggestedQuestionsResponse)
async def get_suggested_questions_by_file_id(
    file_id: str,
    current_organization = Depends(get_current_organization)
):
    """
    Get suggested questions for a video by file ID.
    
    Args:
        file_id: The file ID to retrieve questions for
        
    Returns:
        Suggested questions for the video
    """
    try:
        # First verify that the file belongs to this organization
        file_collection = MongoDB.get_collection(FILES_COLLECTION)
        file = await file_collection.find_one({
            "_id": ObjectId(file_id),
            "organization_id": current_organization["_id"],
            "file_type": "video"  # Ensure it's a video file
        })
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video file not found or you don't have access to it"
            )
        
        # Get suggested questions from the collection
        questions_collection = MongoDB.get_collection(SUGGESTED_QUESTIONS_COLLECTION)
        questions_doc = await questions_collection.find_one({
            "file_id": file_id,
            "organization_id": str(current_organization["_id"])
        })
        
        if not questions_doc:
            # If no questions found, return empty segments
            return {
                "document_id": file["document_id"],
                "file_id": file_id,
                "filename": file["original_filename"],
                "display_name": file["display_name"],
                "segments": []
            }
        
        # Convert ObjectId to string for JSON serialization
        questions_doc["_id"] = str(questions_doc["_id"])
        
        # Format the response
        return {
            "document_id": questions_doc["document_id"],
            "file_id": questions_doc["file_id"],
            "filename": questions_doc["filename"],
            "display_name": questions_doc["display_name"],
            "segments": questions_doc["segments"]
        }
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving suggested questions: {str(e)}"
        )
