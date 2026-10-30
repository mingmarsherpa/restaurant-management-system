# Restaurant API

A full-stack restaurant ordering and management system.

The project provides a FastAPI backend and a React frontend for managing
menus, tables, QR-based customer ordering, kitchen orders, and bills.

## Screenshots

### Admin dashboard

![Admin dashboard](Screenshot/admin_dashboard.png)

### Customer ordering

![Customer ordering](Screenshot/customer_dashboard.jpg)

### Kitchen dashboard

![Kitchen dashboard](Screenshot/kitchen_dashboard.png)

### Sign in

![Sign in](Screenshot/signin.png)

## Features

- Staff sign-in with JWT authentication.
- Admin and kitchen staff roles.
- Menu management for dishes, options, and option groups.
- Restaurant table management with QR codes.
- Customer ordering from a table QR code.
- Kitchen order tracking and status updates.
- Bill management and payment confirmation.
- Pagination for menu data.
- Interactive API documentation with FastAPI.

## Tech stack

### Backend

- Python 3.14
- FastAPI
- SQLAlchemy 2.x
- PostgreSQL
- Alembic
- asyncpg

### Frontend

- React
- TypeScript
- Vite

## Getting started

### 1. Configure the database

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/restaurant
JWT_SECRET_KEY=change-this-secret
```

Set a strong `JWT_SECRET_KEY` when running outside local development.

### 2. Install backend dependencies

```bash
uv sync
```

### 3. Run database migrations

```bash
uv run alembic upgrade head
```

### 4. Create a staff user

Review the seed script and run:

```bash
uv run seed-user
```

### 5. Start the backend

```bash
uv run uvicorn restaurant_api.main:app --reload
```

The API runs at `http://localhost:8000`.

API documentation is available at
[`http://localhost:8000/docs`](http://localhost:8000/docs).

### 6. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

## Application pages

- `/login` — staff sign-in.
- `/admin` — admin workspace for menus, tables, orders, and bills.
- `/kitchen` — kitchen dashboard for active orders.
- `/order?table=<qr-token>` — customer ordering page.

## Useful commands

```bash
# Backend checks
uv run python -m compileall src
uv run alembic check
uv run pytest

# Frontend checks
cd frontend
npm run lint
npm run build
```

## Project structure

```text
restaurant-api/
├── src/restaurant_api/   FastAPI application
├── alembic/              Database migrations
├── frontend/             React application
├── Screenshot/           Project screenshots
└── README.md
```

Prices are stored as integer paisa values, and order items keep a snapshot of
their names and prices so past orders remain accurate after menu changes.
