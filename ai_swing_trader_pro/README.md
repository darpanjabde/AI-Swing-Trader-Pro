# AI Swing Trader Pro

An AI-assisted swing trading platform, built with **Clean Architecture** and **SOLID** principles.

> **Sprint 2** — this release lays the architectural foundation: configuration, logging,
> and database plumbing. **No Kite Connect integration or trading logic is implemented yet.**
> That arrives in a future sprint.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Folder Structure](#folder-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [Running Tests](#running-tests)
- [Design Principles](#design-principles)
- [Roadmap](#roadmap)

---

## Architecture Overview

The project follows **Clean Architecture**, organized as concentric layers where
dependencies only point inward:

```
┌─────────────────────────────────────────────┐
│  interfaces      (CLI / API / Kite adapters) │  ← Sprint 3+
│  ┌─────────────────────────────────────────┐ │
│  │  application   (use cases)               │ │  ← Sprint 3+
│  │  ┌───────────────────────────────────┐   │ │
│  │  │  domain      (entities, rules)     │   │ │  ← Sprint 3+
│  │  └───────────────────────────────────┘   │ │
│  └─────────────────────────────────────────┘ │
│  infrastructure  (SQLAlchemy, external APIs) │  ← Sprint 2 (DB only)
│  core            (config, logging, errors)   │  ← Sprint 2
└─────────────────────────────────────────────┘
```

- **`core`** — cross-cutting concerns with no business logic: settings, logging, exceptions.
- **`domain`** — pure business entities and rules. Zero framework dependencies. Empty scaffold for now.
- **`application`** — use-case orchestration. Depends only on domain interfaces. Empty scaffold for now.
- **`infrastructure`** — concrete implementations (SQLAlchemy today; Kite Connect later).
- **`interfaces`** — outermost adapters (CLI, REST API, broker gateways). Empty scaffold for now.

This layering means the domain and application layers will never import SQLAlchemy or
a broker SDK directly — they'll depend on abstractions that `infrastructure` implements,
per the **Dependency Inversion Principle**.

---

## Folder Structure

```
ai_swing_trader_pro/
├── pyproject.toml
├── .gitignore
├── .env.example
├── README.md
├── src/
│   └── ai_swing_trader_pro/
│       ├── __init__.py              # package version
│       ├── main.py                  # application entry point / bootstrap
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py            # Pydantic Settings (app, DB, logging)
│       │   ├── logger.py            # Loguru configuration
│       │   └── exceptions.py        # shared exception hierarchy
│       ├── domain/
│       │   ├── __init__.py          # (placeholder — Sprint 3+)
│       │   └── entities/
│       │       └── __init__.py
│       ├── application/
│       │   └── __init__.py          # (placeholder — Sprint 3+)
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   └── database/
│       │       ├── __init__.py
│       │       ├── base.py          # declarative Base + naming convention
│       │       └── session.py       # engine, sessionmaker, session_scope
│       └── interfaces/
│           └── __init__.py          # (placeholder — Sprint 3+, e.g. Kite Connect)
└── tests/
    ├── __init__.py
    ├── conftest.py                  # shared fixtures (isolated settings/DB)
    ├── test_config.py
    ├── test_logger.py
    ├── test_database.py
    └── test_main.py
```

---

## Requirements

- Python **3.12**
- pip (or [uv](https://github.com/astral-sh/uv) / [poetry](https://python-poetry.org/) if you prefer)

Runtime dependencies (declared in `pyproject.toml`):

| Package             | Purpose                                   |
|---------------------|--------------------------------------------|
| `pydantic`          | Data validation                            |
| `pydantic-settings` | Environment-driven configuration           |
| `loguru`            | Structured, rotating application logging   |
| `sqlalchemy`        | ORM / database engine & session management |
| `python-dotenv`     | `.env` file loading support                |

Dev dependencies: `pytest`, `pytest-cov`, `mypy`, `ruff`.

---

## Installation

```bash
# 1. Clone and enter the project
cd ai_swing_trader_pro

# 2. Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install the package in editable mode with dev dependencies
pip install -e ".[dev]"

# 4. Create your local environment file
cp .env.example .env
```

---

## Configuration

All configuration is environment-driven via **Pydantic Settings** (`src/ai_swing_trader_pro/core/config.py`),
loaded from `.env` at the project root. See `.env.example` for the full list of variables.

| Variable          | Default                                | Description                          |
|-------------------|-----------------------------------------|---------------------------------------|
| `APP_NAME`        | `AI Swing Trader Pro`                   | Application display name              |
| `ENVIRONMENT`     | `development`                           | `development` / `staging` / `production` / `test` |
| `DEBUG`           | `true`                                   | Enables verbose tracebacks in logs    |
| `SECRET_KEY`      | `change-me-in-.env`                     | Generic app secret (broker keys come later) |
| `DB_URL`          | `sqlite:///./ai_swing_trader_pro.db`    | SQLAlchemy connection string          |
| `DB_ECHO`         | `false`                                  | Echo raw SQL to logs                  |
| `DB_POOL_SIZE`    | `5`                                      | Connection pool size (non-SQLite)     |
| `LOG_LEVEL`       | `INFO`                                  | `TRACE` … `CRITICAL`                  |
| `LOG_DIRECTORY`   | `./logs`                                 | Where rotating log files are written  |
| `LOG_ROTATION`    | `10 MB`                                  | Rotation policy                       |
| `LOG_RETENTION`   | `14 days`                                | How long rotated logs are kept        |

Access settings anywhere via:

```python
from ai_swing_trader_pro.core.config import get_settings

settings = get_settings()
print(settings.app_name, settings.database.url)
```

---

## Running the App

```bash
python -m ai_swing_trader_pro.main
# or, after installation:
ai-swing-trader-pro
```

On startup, this:
1. Loads and validates configuration.
2. Configures Loguru (console + rotating file sink under `logs/`).
3. Creates the SQLAlchemy engine and ensures the schema exists (no tables yet — that's Sprint 3+).
4. Logs a success message confirming the app booted cleanly.

---

## Running Tests

```bash
pytest
```

This runs the full unit test suite with coverage reporting (configured in `pyproject.toml`),
covering configuration, logging, database session handling, and the bootstrap sequence.
Tests use isolated in-memory SQLite databases and temporary log directories, so they never
touch your real `.env` or `ai_swing_trader_pro.db`.

Optional static checks:

```bash
ruff check .
mypy .
```

---

## Design Principles

- **Single Responsibility** — `config.py` only loads config, `logger.py` only configures logging,
  `session.py` only manages DB connections.
- **Open/Closed** — `Database.create_all()` and `Base.metadata` are ready to accept new ORM models
  in future sprints without modifying existing code.
- **Liskov Substitution** — `TimestampMixin` and `Base` compose cleanly via multiple inheritance
  for any future entity.
- **Interface Segregation** — `base.py` and `session.py` are split so model modules don't need to
  import engine/session machinery.
- **Dependency Inversion** — higher layers (`domain`, `application`) will depend on abstractions,
  not on SQLAlchemy or broker SDKs directly.

---

## Roadmap

| Sprint | Scope                                                              |
|--------|----------------------------------------------------------------------|
| 1      | Project ideation & requirements                                      |
| **2**  | **Clean architecture scaffold, config, logging, DB setup (this repo)** |
| 3      | Domain entities (Instrument, Order, Position) + ORM models            |
| 4      | Kite Connect integration                                              |
| 5      | Trading strategy engine                                               |
| 6      | Backtesting & AI signal generation                                    |

---

*This README documents Sprint 2 only. Trading functionality, broker integration, and
strategy logic are intentionally out of scope until later sprints.*
