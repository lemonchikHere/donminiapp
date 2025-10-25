from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routes import search, properties, favorites, appointments, map, searches, config, offers # chat temporarily disabled

# Imports for rate limiting
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware

# 1. Define the key function for rate limiting
def get_request_identifier(request: Request) -> str:
    """
    Identify the user by the 'x-telegram-user-id' header, falling back to the client's host IP.
    """
    telegram_user_id = request.headers.get("x-telegram-user-id")
    return telegram_user_id or request.client.host

# 2. Create the limiter instance
limiter = Limiter(key_func=get_request_identifier, default_limits=["100/minute"])

app = FastAPI(
    title="Don Estate API",
    description="API for the Don Estate Telegram Mini App",
    version="1.0.0"
)

# 3. Add limiter to app state and add the middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


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
app.mount("/media", StaticFiles(directory="media"), name="media")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')
