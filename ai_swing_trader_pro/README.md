# AI Swing Trader Pro

An AI-assisted swing trading platform, built with **Clean Architecture** and **SOLID** principles.

> **Sprint 2** laid the architectural foundation: configuration, logging, and database plumbing.
> **Sprint 3.1** (this release) adds the **Kite Connect authentication layer** — a
> `MarketDataProvider` interface and its Kite implementation, covering login/session setup and
> connection verification only. **Instrument download, historical data, live quotes, strategy
> logic, and the scanner are still not implemented.**

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Folder Structure](#folder-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [Running Tests](#running-tests)
- [Kite Connect Authentication (Sprint 3.1)](#kite-connect-authentication-sprint-31)
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
│       │   ├── __init__.py          # (entities placeholder — Sprint 3.2+)
│       │   ├── exceptions.py        # market-data-provider exception hierarchy
│       │   ├── entities/
│       │   │   └── __init__.py
│       │   └── interfaces/
│       │       ├── __init__.py
│       │       └── market_data_provider.py   # abstract MarketDataProvider port
│       ├── application/
│       │   └── __init__.py          # (placeholder — Sprint 3.2+)
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── database/
│       │   │   ├── __init__.py
│       │   │   ├── base.py          # declarative Base + naming convention
│       │   │   └── session.py       # engine, sessionmaker, session_scope
│       │   └── market_data/
│       │       ├── __init__.py
│       │       ├── kite_client.py   # thin wrapper around the kiteconnect SDK
│       │       └── kite_provider.py # KiteMarketDataProvider (auth + verification)
│       └── interfaces/
│           └── __init__.py          # (placeholder — Sprint 3.2+, e.g. CLI/API)
└── tests/
    ├── __init__.py
    ├── conftest.py                  # shared fixtures (isolated settings/DB)
    ├── test_config.py
    ├── test_logger.py
    ├── test_database.py
    ├── test_main.py
    ├── test_kite_client.py
    └── test_kite_provider.py
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
| `kiteconnect`       | Official Zerodha Kite Connect SDK          |

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
| `KITE_API_KEY`    | *(none)*                                 | Kite Connect API key (**required** to authenticate) |
| `KITE_API_SECRET` | *(none)*                                 | Kite Connect API secret (**required** to authenticate) |
| `KITE_ACCESS_TOKEN` | *(none)*                               | Optional cached access token (skips interactive login; expires daily) |
| `KITE_REDIRECT_URL` | *(none)*                               | OAuth redirect URL registered with Kite Connect (optional) |
| `KITE_REQUEST_TIMEOUT` | `7`                                  | Seconds to wait for Kite API responses |

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

## Kite Connect Authentication (Sprint 3.1)

This sprint adds the broker authentication layer, following the same dependency-inversion
pattern used for the database in Sprint 2:

- **`domain/interfaces/market_data_provider.py`** — an abstract `MarketDataProvider` port
  (`get_login_url`, `authenticate`, `verify_connection`, `is_authenticated`). Pure standard
  library; no broker SDK dependency.
- **`domain/exceptions.py`** — `InvalidCredentialsError`, `AuthenticationError`,
  `SessionNotInitializedError`, `ConnectionVerificationError` — all rooted in `AppError`, so
  broker-SDK-specific exceptions never leak past the infrastructure layer.
- **`infrastructure/market_data/kite_client.py`** — a thin, dependency-injectable wrapper
  around `kiteconnect.KiteConnect`. Knows nothing about domain exceptions or logging.
- **`infrastructure/market_data/kite_provider.py`** — `KiteMarketDataProvider`, the concrete
  `MarketDataProvider` implementation. Validates credentials, translates SDK errors into domain
  exceptions, and logs every authentication step via Loguru.

### Authentication flow

Kite Connect uses a request-token OAuth-style flow:

```python
from ai_swing_trader_pro.infrastructure.market_data import KiteMarketDataProvider

provider = KiteMarketDataProvider()  # raises InvalidCredentialsError if KITE_API_KEY/SECRET are missing

# 1. Send the user to Kite's login page:
login_url = provider.get_login_url()

# 2. After login, Kite redirects back with a `request_token` query param.
#    Exchange it for an access token:
provider.authenticate(request_token="the-request-token-from-the-redirect")

# 3. Confirm the session is actually usable against the live API:
assert provider.verify_connection() is True
```

If `KITE_ACCESS_TOKEN` is already set in `.env` (e.g. from an earlier session the same day),
`provider.authenticate()` can be called with no arguments and will reuse it — Kite access
tokens are valid until the next trading day's reset, so this only works within that window.

**Out of scope for Sprint 3.1** (by design): instrument download, historical candle data,
live quotes, strategy logic, and the scanner. These build on top of this authentication layer
in later sprints.

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
- **Dependency Inversion** — higher layers (`domain`, `application`) depend on abstractions
  (`MarketDataProvider`), not on SQLAlchemy or the `kiteconnect` SDK directly.
- **Testability via injection** — both `KiteClient` (via `sdk_client=`) and
  `KiteMarketDataProvider` (via `client=`) accept their collaborators as constructor
  arguments, so unit tests substitute mocks without touching real credentials or the network.

---

## Roadmap

| Sprint   | Scope                                                              |
|----------|----------------------------------------------------------------------|
| 1        | Project ideation & requirements                                      |
| 2        | Clean architecture scaffold, config, logging, DB setup                |
| **3.1**  | **Kite Connect authentication layer (this repo)**                     |
| 3.2      | Domain entities (Instrument, Order, Position) + ORM models             |
| 3.3      | Instrument download, historical data, live quotes                      |
| 4        | Trading strategy engine + scanner                                      |
| 5        | Backtesting & AI signal generation                                     |

---

*This README documents Sprints 2 and 3.1. Instrument download, historical data, live quotes,
strategy logic, and the scanner are intentionally out of scope until later sprints.*
