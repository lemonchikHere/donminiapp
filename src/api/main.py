"""
Main application file for the FastAPI backend.

This file initializes the FastAPI application, configures middleware (like CORS),
and includes all the API routers from the `src/api/routes` directory.
It serves as the entry point for the API service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routes import search, properties, favorites, appointments, map, searches, config, offers # chat temporarily disabled

app = FastAPI(
    title="Don Estate API",
    description="API for the Don Estate Telegram Mini App, providing endpoints "
                "for searching, viewing, and managing real estate properties.",
    version="1.0.0"
)

# Configure CORS (Cross-Origin Resource Sharing) middleware to allow
# requests from any origin. In a production environment, this should be
# restricted to the specific origin of the frontend application.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API routers defined in other modules.
app.include_router(search.router)
app.include_router(properties.router)
app.include_router(favorites.router)
app.include_router(appointments.router)
app.include_router(map.router)
# app.include_router(chat.router)
app.include_router(searches.router)
app.include_router(config.router)
app.include_router(offers.router)

# Serve Frontend
app.mount("/", StaticFiles(directory="static", html = True), name="static")

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint for the API.

    Provides a simple welcome message to indicate that the API is running.
    """
    return {"message": "Welcome to Don Estate API"}
