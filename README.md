# Gestionale Tesoreria

Gestionale di tesoreria aziendale e cash management.

## Prerequisiti

- **macOS** con Homebrew
- **PostgreSQL 16** (`brew install postgresql@16`)
- **Python 3.14+**
- **Node.js 20+** e npm

## Setup

### 1. Database

```bash
# Avvia PostgreSQL 16 su porta 5433
/opt/homebrew/opt/postgresql@16/bin/pg_ctl -D /opt/homebrew/var/postgresql@16 -o "-p 5433" -l /opt/homebrew/var/log/postgresql@16.log start

# Crea il database
/opt/homebrew/opt/postgresql@16/bin/createdb -p 5433 tesoreria_dev
```

### 2. File .env

Crea `.env` nella root del progetto:

```env
DATABASE_URL=postgresql://nicolascarpa@localhost:5433/tesoreria_dev
SECRET_KEY=<genera con: python3 -c "import secrets; print(secrets.token_hex(32))">
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 3. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Alembic
cd backend
alembic upgrade head
```

### 4. Frontend

```bash
cd frontend
npm install
```

### 5. Avvio

```bash
./start-dev.sh
```

Oppure avvia manualmente:

```bash
# Terminale 1 — Backend
source .venv/bin/activate
cd backend
uvicorn app.main:app --reload --port 8000

# Terminale 2 — Frontend
cd frontend
npm run dev
```

## URLs

| Servizio | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1 |
| Swagger UI | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

## Struttura

```
├── backend/          # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── core/     # config, database, security
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/v1/
│   │   └── services/
│   ├── alembic/
│   └── tests/
├── frontend/         # Next.js + shadcn/ui
│   └── src/
│       ├── app/
│       ├── components/
│       ├── lib/
│       ├── stores/
│       └── types/
├── .env              # Config (non committare)
└── start-dev.sh      # Avvia tutto
```
