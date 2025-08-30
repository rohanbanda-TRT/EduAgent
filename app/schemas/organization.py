from typing import Optional, Any, Annotated
from pydantic import BaseModel, Field, EmailStr, ConfigDict
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

class OrganizationBase(BaseModel):
    name: str
    email: str
    description: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    password: str

class OrganizationLogin(BaseModel):
    email: str
    password: str

class OrganizationResponse(OrganizationBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    org_id: Optional[str] = None
    is_organization: bool = True
