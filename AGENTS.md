# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Build/Test Commands

**Docker Commands:**
- `docker-compose build` - Build all services
- `docker-compose up -d` - Run in background
- `docker-compose down` - Stop and remove containers
- `docker-compose logs api --tail=15` - View API logs

**Testing:**
- `pytest tests/` - Run all tests (requires PostgreSQL with pgvector)
- `pytest tests/api/test_search.py::test_search_semantic_query` - Run specific test
- Tests use SQLite in-memory database by default

## Critical Architecture Patterns

**Database:**
- PostgreSQL with pgvector extension for vector search
- SQLAlchemy ORM with separate session management
- Database initialization via `init_db.py` in Docker

**API Structure:**
- FastAPI with modular router organization in `src/api/routes/`
- Dependency injection for database sessions and user authentication
- CORS configured for Telegram Mini App origins

**Authentication:**
- User authentication via `X-Telegram-User-ID` header
- Admin access verification using `ADMIN_CHAT_ID` from .env
- Dependencies: `get_current_user()`, `get_admin_user()`

**Form Handling:**
- Multi-part form data requires `python-multipart` package
- File uploads handled via `Form()` and `File()` parameters
- Media files stored in `/app/media` directory in Docker

## Non-Obvious Gotchas

**Dependencies:**
- `python-multipart` is required for form handling (not included by default)
- `pgvector` PostgreSQL extension must be manually created: `CREATE EXTENSION vector;`
- OpenAI embeddings disabled in tests to avoid SQLite <=> operator errors

**Environment:**
- Parser and chat services are commented out in `docker-compose.yml`
- Bot token required for admin notifications in offers endpoint
- Database URL uses `postgresql+psycopg2` dialect

**Testing:**
- Tests mock OpenAI embeddings to prevent vector search errors
- Test database uses SQLite while production uses PostgreSQL
- Semantic search tests require specific mocking of database queries