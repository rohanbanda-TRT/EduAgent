from typing import Optional, Literal, Any, Annotated
from pydantic import BaseModel, ConfigDict, Field
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue
from bson import ObjectId
from datetime import datetime

class ObjectIdAnnotation:
    @classmethod
    def validate_object_id(cls, v: Any, handler) -> ObjectId:
        if isinstance(v, ObjectId):
            return v
        s = handler(v)
        if ObjectId.is_valid(s):
            return ObjectId(s)
        else:
            raise ValueError(f"Invalid ObjectId: {s}")
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, _handler) -> core_schema.CoreSchema:
        assert source_type is ObjectId
        return core_schema.no_info_wrap_validator_function(
            cls.validate_object_id,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )
    
    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler) -> JsonSchemaValue:
        return handler(core_schema.str_schema())


# Define PyObjectId as an annotated ObjectId
PyObjectId = Annotated[ObjectId, ObjectIdAnnotation]

class FileBase(BaseModel):
    original_filename: str  # Original filename as uploaded
    display_name: Optional[str] = None  # Optional display name
    file_type: Literal["pdf", "video"]
    content_type: str
    organization_id: PyObjectId
    description: Optional[str] = None
    tags: Optional[list[str]] = None  # Optional tags for categorization
    
class FileCreate(FileBase):
    pass

class FileResponse(FileBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    file_path: str
    storage_filename: str  # System-generated filename for storage
    file_size: int
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    uploaded_by: Optional[str] = None  # Name of the person who uploaded
    document_id: Optional[str] = None  # UUID for document processing
    processing_status: Optional[str] = None  # Status of document processing (success, error, warning)
    processing_message: Optional[str] = None  # Message from document processing
    chunks_created: Optional[int] = None  # Number of chunks created during processing
    total_pages: Optional[int] = None  # Total pages for PDF documents

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
