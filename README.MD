# Circuit Breaker Manager

A robust microservice monitoring system implementing the **Circuit Breaker** pattern. This project ensures system
stability by tracking external service health, managing failure states, and providing real-time status updates via
WebSockets.

## 🛠 Tech Stack

- **Language**: Python 3.12
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: PostgreSQL (SQLAlchemy 2.0 + Alembic migrations)
- **Task Queue & Caching**: Redis + [RQ](https://python-rq.org/)
- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **Containerization**: Docker & Docker Compose

## 📋 Project Structure

```text
src/
├── database/    # Models, sessions, and Alembic migrations
├── repository/  # Data access layer (CRUD operations)
├── services/    # Business logic (WS, Pub/Sub, Cache management)
├── tasks/       # Background worker logic and health checkers
├── scheduler/    # Task scheduling configuration
├── views/       # API endpoints (FastAPI routes)
└── schemas/     # Pydantic models for data validation
```

## ⚙️ Getting Started

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone <your-repository-url>
   cd circuit-breaker-manager
   ```

2. Configure environment variables:
   ```bash
   cp .env.sample .env
   # Update .env with your specific credentials
   ```

3. Spin up the infrastructure:
   ```bash
   docker-compose up --build
   ```

### Local Development (using uv)

1. Install `uv` if not already available.
2. Synchronize dependencies:
   ```bash
   uv sync
   ```
3. Run database migrations:
   ```bash
   uv run alembic upgrade head
   ```
4. Start the application:
   ```bash
   uv run main.py