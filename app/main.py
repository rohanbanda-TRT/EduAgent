from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import routes
from app.routes import organization, student, files
from app.database.mongodb import MongoDB

app = FastAPI(
    title="EduAgent API",
    description="API for educational platform with organization and student authentication",
    version="0.1.0"
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

@app.get("/")
async def root():
    return {"message": "Welcome to EduAgent API"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
