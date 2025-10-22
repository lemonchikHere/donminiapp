# Don Estate Backend

This repository contains the backend services for the **Don Estate** Telegram Mini App, a real estate platform for an agency in Donetsk. The system is designed to parse property listings from a Telegram channel, process and store them in a database, and provide a comprehensive API for a frontend client.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
  - [Prerequisites](#prerequisites)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Running Tests](#running-tests)

## Features

- **Telegram Channel Parser**: A Telethon-based script that automatically parses new property listings from a specified Telegram channel.
- **Data Extraction**: Uses regular expressions to extract key property details (price, area, rooms, etc.) from unstructured text.
- **Geocoding**: Integrates with the Yandex Maps API to convert property addresses into geographic coordinates.
- **Vector Embeddings**: Generates vector embeddings for property descriptions using OpenAI's `text-embedding-3-small` model for semantic search.
- **FastAPI Backend**: A robust asynchronous API built with FastAPI to serve data to the frontend.
- **Database**: Utilizes PostgreSQL with the `pgvector` extension for efficient geospatial and vector similarity queries.
- **Dockerized Environment**: The entire application stack is containerized with Docker and managed via `docker-compose` for easy setup and deployment.

## Technology Stack

- **Backend**: Python, FastAPI
- **Telegram Parser**: Telethon
- **Database**: PostgreSQL, SQLAlchemy, pgvector
- **Vector Embeddings**: OpenAI API
- **Geocoding**: Yandex Maps API
- **Containerization**: Docker, Docker Compose
- **Testing**: Pytest

## System Architecture

The application consists of three main services orchestrated by `docker-compose`:

1.  **Postgres (`postgres`)**: The database service, using an image with the `pgvector` extension pre-installed.
2.  **Parser (`parser`)**: A standalone Python script that connects to Telegram via Telethon, parses messages, and saves them to the database.
3.  **API (`api`)**: The FastAPI application that provides RESTful endpoints for the frontend to interact with the property data.

## Project Structure

```
.
├── src/
│   ├── api/                # FastAPI application code
│   │   ├── routes/         # API endpoint routers
│   │   ├── dependencies.py # FastAPI dependencies (e.g., user auth)
│   │   └── main.py         # Main FastAPI app initialization
│   ├── models/             # SQLAlchemy ORM models
│   ├── parser/             # Telegram channel parser code
│   │   ├── data_extractor.py # Logic for extracting data from text
│   │   ├── media_handler.py  # Logic for downloading media
│   │   └── telegram_parser.py# Main parser script
│   ├── services/           # Business logic services (e.g., geocoding)
│   ├── config.py           # Application configuration settings
│   └── database.py         # Database session management
├── tests/                  # Pytest tests for the application
├── .env.example            # Example environment variables file
├── app.js                  # Frontend JavaScript (React)
├── docker-compose.yml      # Docker Compose configuration
├── index.html              # Frontend HTML entry point
└── requirements.txt        # Python dependencies
```

## Setup and Installation

### Prerequisites

-   Docker and Docker Compose installed on your local machine.
-   A Telegram account with API credentials. You can get these from [my.telegram.org](https://my.telegram.org).

### Configuration

1.  **Copy the example environment file**:
    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file** and fill in the required values:
    -   `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`: Your Telegram API credentials.
    -   `TELEGRAM_CHANNEL`: The username or ID of the channel to parse (e.g., `@donetsk_estate`).
    -   `DB_PASSWORD`: A secure password for the PostgreSQL database.
    -   `OPENAI_API_KEY`: Your API key from OpenAI.
    -   `YANDEX_API_KEY`: Your API key for the Yandex Maps Geocoding API.
    -   `ADMIN_CHAT_ID`: The Telegram chat ID for receiving admin notifications (e.g., for new appointment requests).

### Running the Application

1.  **Build and start the services** using Docker Compose:
    ```bash
    docker-compose up --build
    ```
    This command will build the images for the `parser` and `api` services and start all containers.

2.  **First Run**: The first time you run the `parser`, Telethon will ask you to enter your phone number, the code you receive on Telegram, and your two-factor authentication password if you have one set up. After you authenticate, a `.session` file will be created to keep you logged in.

The API will be available at `http://localhost:8000`.

## API Endpoints

The main API endpoints are documented via Swagger UI, which is available at `http://localhost:8000/docs` when the API service is running.

-   `POST /api/search`: Search for properties with filters and semantic query.
-   `GET /api/properties/{property_id}`: Get details for a single property.
-   `GET /api/properties/similar/{property_id}`: Find properties similar to a given one.
-   `GET /api/favorites/`: Get the current user's favorite properties.
-   `POST /api/favorites/`: Add a property to favorites.
-   `DELETE /api/favorites/{property_id}`: Remove a property from favorites.
-   `POST /api/appointments/`: Create a viewing appointment.
-   `GET /api/map/properties`: Get all properties with coordinates for map display.

## Running Tests

To run the test suite, you can execute `pytest` inside the running `api` container.

1.  Find the container ID for the API service:
    ```bash
    docker-compose ps
    ```

2.  Run pytest inside the container:
    ```bash
    docker-compose exec api pytest
    ```
