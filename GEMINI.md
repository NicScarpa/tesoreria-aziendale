# GEMINI.md — Sibill Replica Project Context

This document provides a comprehensive overview of the `sibill-re` project, designed to serve as instructional context for AI interactions.

## Project Overview

**Sibill-RE** is a treasury management and cash flow monitoring application built as a high-fidelity replica of the [Sibill](https://sibill.com) SaaS platform. The project is the result of an extensive reverse engineering effort, documented in the `docs/` directory, aimed at recreating the features, data model, and user experience of the original application.

### Core Objectives
- **Cash Management:** Monitor bank accounts, balances, and historical movements.
- **Cash Flow Forecasting:** Predictive analysis of future liquidity based on expected payments and historical data.
- **Bank Reconciliation:** Automated and manual matching of bank movements with invoices or expected transactions.
- **Invoice & Payment Tracking:** Management of deadlines, payments (SEPA/CBI), and integrations with the "Cassetto Fiscale" (Italian Revenue Agency).

## Technology Stack

### Backend (Python/FastAPI)
- **Framework:** FastAPI
- **Database:** PostgreSQL (v16+) with SQLAlchemy (asyncio)
- **Migrations:** Alembic
- **Authentication:** OAuth2 with JWT/Cookie-based session management.
- **Task Scheduling:** Likely via background tasks (FastAPI) or dedicated workers.

### Frontend (TypeScript/Next.js)
- **Framework:** Next.js 16 (App Router), React 19
- **Styling:** Tailwind CSS 4, shadcn/ui
- **State Management:** Zustand
- **Forms:** React Hook Form + Zod
- **Charts:** Recharts
- **Icons:** Lucide React

## Architecture

The project follows a monorepo-style structure:
- `/backend`: FastAPI application containing business logic, models, and API routes.
- `/frontend`: Next.js application for the user interface.
- `/docs`: Extensive technical documentation (reverse engineering findings, API maps, data models).
- `/assets`: Raw data collected during analysis (API traces, HAR files, screenshots).
- `/execution`: Utility scripts for data extraction and automation.

## Building and Running

### Prerequisites
- macOS (Homebrew recommended)
- PostgreSQL 16 (running on port **5433**)
- Python 3.14+
- Node.js 20+

### Setup Commands
1. **Database Initialization:**
   ```bash
   brew install postgresql@16
   pg_ctl -D /opt/homebrew/var/postgresql@16 -o "-p 5433" start
   createdb -p 5433 tesoreria_dev
   ```

2. **Environment Configuration:**
   Create a `.env` file in the root with `DATABASE_URL`, `SECRET_KEY`, and `FERNET_KEY`.

3. **Backend Setup:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   cd backend && alembic upgrade head
   ```

4. **Frontend Setup:**
   ```bash
   cd frontend && npm install
   ```

### Running the Application
Use the provided orchestration script:
```bash
./start-dev.sh
```
- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- **Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

## Development Conventions

- **API Design:** RESTful principles, JSON:API compliant (following Sibill's pattern).
- **Backend structure:** Modular routers in `backend/app/api/v1/`. Services layer for business logic.
- **Frontend structure:** Component-based architecture using shadcn/ui primitives.
- **Reverse Engineering Docs:** Always refer to `docs/` before implementing new features to ensure alignment with the target application's logic.

## Key Files
- `start-dev.sh`: Main entry point for development.
- `backend/app/main.py`: FastAPI entry point.
- `frontend/src/app/page.tsx`: Next.js main dashboard.
- `docs/03-data-model.md`: Detailed ER diagram and entity descriptions.
- `docs/04-api-reference.md`: Mapped endpoints from the original application.
- `tasks/prd.json`: Backlog and product requirements for the replica.
