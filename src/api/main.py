from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routes import (
    search,
    properties,
    favorites,
    appointments,
    map,
    searches,
    config,
    offers,
)  # chat temporarily disabled

app = FastAPI(
    title="Don Estate API",
    description="API for the Don Estate Telegram Mini App",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your Mini App's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
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
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")
