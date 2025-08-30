from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

# Import routes
from app.routes import organization, student, files, search, questions
from app.database.mongodb import MongoDB

# Define security scheme for Swagger UI
security_scheme = HTTPBearer()

def get_token(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    return credentials.credentials

app = FastAPI(
    title="EduAgent API",
    description="API for educational platform with organization and student authentication",
    version="0.1.0",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "useBasicAuthenticationWithAccessCodeGrant": True
    }
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_db_client():
    await MongoDB.connect_to_mongodb()

@app.on_event("shutdown")
async def shutdown_db_client():
    await MongoDB.close_mongodb_connection()

# Include routers
app.include_router(organization.router, prefix="/api/organization", tags=["Organization"])
app.include_router(student.router, prefix="/api/student", tags=["Student"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(questions.router, prefix="/api/questions", tags=["Questions"])

@app.get("/")
async def root():
    return {"message": "Welcome to EduAgent API"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
