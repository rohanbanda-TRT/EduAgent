"""Search routes for document retrieval."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from bson import ObjectId

from app.utils.auth import get_current_organization
from app.utils.document_processor import DocumentProcessor
from app.database.mongodb import MongoDB, FILES_COLLECTION

router = APIRouter()

# Initialize document processor
document_processor = DocumentProcessor()

@router.get("/documents")
async def search_documents(
    query: str,
    limit: int = Query(5, ge=1, le=20),
    file_type: Optional[str] = None,
    document_id: Optional[str] = None,
    current_organization = Depends(get_current_organization)
):
    """
    Search for documents based on query and filters.
    
    Args:
        query: Search query text
        limit: Maximum number of results to return (default: 5)
        file_type: Filter by file type (pdf, video)
        document_id: Filter by specific document ID
        
    Returns:
        List of document chunks matching the query
    """
    try:
        # Build filters for the vector search
        filters = {}
        
        # If document_id is provided, filter by it
        if document_id:
            filters["document_id"] = document_id
            
        # If file_type is provided, filter by source
        if file_type:
            if file_type.lower() == "pdf":
                filters["source"] = "pdf"
            elif file_type.lower() == "video":
                filters["source"] = "video"
        
        # Perform the search
        document_type = None
        if file_type:
            if file_type.lower() == "pdf":
                document_type = "pdf"
            elif file_type.lower() == "video":
                document_type = "video"
                
        results = document_processor.retrieve_documents(
            query=query,
            limit=limit,
            filters=filters,
            document_type=document_type
        )
        
        if not results:
            return {
                "status": "success",
                "message": "No results found",
                "results": []
            }
            
        # Get the document IDs from results to fetch file metadata
        document_ids = list(set([result["metadata"]["document_id"] for result in results]))
        
        # Fetch file metadata for these documents
        file_collection = MongoDB.get_collection(FILES_COLLECTION)
        files = await file_collection.find(
            {"document_id": {"$in": document_ids}, "organization_id": current_organization["_id"]}
        ).to_list(100)
        
        # Create a mapping of document_id to file metadata
        file_map = {file["document_id"]: file for file in files}
        
        # Enhance results with file metadata
        enhanced_results = []
        for result in results:
            document_id = result["metadata"]["document_id"]
            if document_id in file_map:
                file_info = file_map[document_id]
                enhanced_result = {
                    "content": result["content"],
                    "metadata": result["metadata"],
                    "score": result["score"],
                    "file_info": {
                        "id": str(file_info["_id"]),
                        "display_name": file_info["display_name"],
                        "file_type": file_info["file_type"],
                        "original_filename": file_info["original_filename"],
                        "created_at": file_info["created_at"].isoformat() if "created_at" in file_info else None
                    }
                }
                enhanced_results.append(enhanced_result)
        
        return {
            "status": "success",
            "message": f"Found {len(enhanced_results)} results",
            "results": enhanced_results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching documents: {str(e)}",
            "results": []
        }

@router.get("/documents/{document_id}")
async def get_document_chunks(
    document_id: str,
    current_organization = Depends(get_current_organization)
):
    """
    Get all chunks for a specific document.
    
    Args:
        document_id: The document ID to retrieve chunks for
        
    Returns:
        List of document chunks for the specified document
    """
    try:
        # First verify that the document belongs to this organization
        file_collection = MongoDB.get_collection(FILES_COLLECTION)
        file = await file_collection.find_one({
            "document_id": document_id,
            "organization_id": current_organization["_id"]
        })
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or you don't have access to it"
            )
        
        # Determine document type from file info
        document_type = None
        if file and "file_type" in file:
            if file["file_type"].lower() == "pdf":
                document_type = "pdf"
            elif file["file_type"].lower() == "video":
                document_type = "video"
        
        # Use an empty query with document_id filter to get all chunks
        results = document_processor.retrieve_documents(
            query="",
            limit=100,  # Higher limit to get all chunks
            filters={"document_id": document_id},
            document_type=document_type
        )
        
        # Sort results by page number or chunk_id for proper ordering
        if results and "metadata" in results[0] and "page" in results[0]["metadata"]:
            # Sort PDF results by page number
            results.sort(key=lambda x: (int(x["metadata"].get("page", 0)), int(x["metadata"].get("chunk_id", 0))))
        else:
            # Sort video results by chunk_id
            results.sort(key=lambda x: int(x["metadata"].get("chunk_id", 0)))
        
        return {
            "status": "success",
            "message": f"Found {len(results)} chunks for document {document_id}",
            "document_info": {
                "id": str(file["_id"]),
                "document_id": document_id,
                "display_name": file["display_name"],
                "file_type": file["file_type"],
                "original_filename": file["original_filename"],
                "created_at": file["created_at"].isoformat() if "created_at" in file else None,
                "total_pages": file.get("total_pages"),
                "chunks_created": file.get("chunks_created")
            },
            "results": results
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving document chunks: {str(e)}",
            "results": []
        }
