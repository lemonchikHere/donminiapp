from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .routes import search, properties, favorites, appointments
import os

app = FastAPI(
    title="Don Estate API",
    description="API for the Don Estate Telegram Mini App",
    version="1.0.0"
)

# Create media directory if it doesn't exist
if not os.path.exists("media"):
    os.makedirs("media")

app.mount("/media", StaticFiles(directory="media"), name="media")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your Mini App's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router)
app.include_router(properties.router)
app.include_router(favorites.router)
app.include_router(appointments.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Don Estate API"}
