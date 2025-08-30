from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from bson import ObjectId

from app.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationLogin, Token
from app.utils.auth import (
    authenticate_organization, 
    create_access_token, 
    get_password_hash, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_organization
)
from app.database.mongodb import MongoDB, ORGANIZATIONS_COLLECTION

router = APIRouter()

@router.post("/signup", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(organization: OrganizationCreate):
    """
    Create a new organization account.
    """
    # Get the organizations collection
    org_collection = MongoDB.get_collection(ORGANIZATIONS_COLLECTION)
    
    # Check if organization with this email already exists
    existing_org = await org_collection.find_one({"email": organization.email})
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    hashed_password = get_password_hash(organization.password)
    
    # Create organization document
    org_dict = organization.dict()
    org_dict["password"] = hashed_password
    
    # Insert into database
    result = await org_collection.insert_one(org_dict)
    
    # Get the created organization
    created_org = await org_collection.find_one({"_id": result.inserted_id})
    
    return created_org

@router.post("/login", response_model=Token)
async def login_organization(login_data: OrganizationLogin):
    """
    Authenticate an organization and return a JWT token.
    """
    organization = await authenticate_organization(login_data.email, login_data.password)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": organization["email"],
            "org_id": str(organization["_id"]),
            "is_organization": True
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=OrganizationResponse)
async def read_organization_me(current_organization = Depends(get_current_organization)):
    """
    Get current organization profile.
    """
    return current_organization
