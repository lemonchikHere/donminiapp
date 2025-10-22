from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import search, properties, favorites, appointments, map, chat, searches, config, offers

app = FastAPI(
    title="Don Estate API",
    description="API for the Don Estate Telegram Mini App",
    version="1.0.0"
)

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
app.include_router(map.router)
app.include_router(chat.router)
app.include_router(searches.router)
app.include_router(config.router)
app.include_router(offers.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Don Estate API"}
