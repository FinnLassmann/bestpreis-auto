# Bestpreis Auto — EU Neuwagen Marktplatz

Aggregiert Neuwagen-Angebote von Viscaal, APEG und EU-Mayer in einer modernen Suchoberfläche.

## Dev Setup

### Voraussetzungen

- Docker + Docker Compose
- Node.js 18+ (für Frontend ohne Docker)
- Python 3.11+ (für Backend ohne Docker)

### Option 1: Alles mit Docker Compose

```bash
docker compose up
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432

### Option 2: Einzeln starten (ohne Docker)

#### 1. Datenbank starten

```bash
docker compose up db
```

#### 2. Backend

```bash
cd backend
pip install -r requirements.txt

# DB mit Fahrzeugdaten befüllen
python seed.py

# API starten
uvicorn main:app --reload --port 8000
```

API läuft auf http://localhost:8000

#### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend läuft auf http://localhost:5173

### Umgebungsvariablen

Siehe `.env.example`. Für lokale Entwicklung ohne Docker:

```bash
export DATABASE_URL=postgresql+asyncpg://euautos:dev_password@localhost:5432/euautos
export DATABASE_URL_SYNC=postgresql://euautos:dev_password@localhost:5432/euautos
export VITE_API_URL=http://localhost:8000
```
