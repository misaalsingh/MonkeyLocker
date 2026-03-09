# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from services.db_connection import init_db
import models.users, models.events, models.rooms, models.images, models.imageuser  # noqa: F401 — must import before init_db
from routers import auth, users, events, rooms, images

# Initialize database

# Create FastAPI app
app = FastAPI(title="Face Classroom API", version="1.0.0")

# CORS
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# Serve uploaded images (if using local storage)
if os.path.exists("./uploaded_images"):
    app.mount("/images", StaticFiles(directory="uploaded_images"), name="images")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/monkey/users", tags=["Users"])
app.include_router(events.router, prefix='/monkey/events', tags=["Events"])
app.include_router(rooms.router, prefix="/api/rooms", tags=["Rooms"])
app.include_router(images.router, prefix="/api", tags=["Images"])

@app.get("/")
def root():
    return {"message": "Face Classroom API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)