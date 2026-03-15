# CLAUDE.md — EU Neuwagen Marktplatz Prototyp

## Projektübersicht

Ein Prototyp für einen EU-Reimport-Neuwagen-Marktplatz, der Fahrzeugdaten von
Viscaal (viscaal.de), APEG (automarkt-im-allgaeu.de) und EU-Mayer (eu-mayer.de)
aggregiert, in einer eigenen Datenbank speichert und über eine moderne
React-Oberfläche präsentiert.
Das Ziel: bessere UX als die Quellseiten, mit Preistransparenz und Ersparnis
gegenüber deutschem UVP im Mittelpunkt.

---

## Tech Stack

| Schicht       | Technologie                              |
|---------------|------------------------------------------|
| Scraping      | Python + Playwright (JS sites) + requests/BS4 (HTML sites) |
| Datenbank     | PostgreSQL (via SQLAlchemy ORM)          |
| Backend API   | Python FastAPI                           |
| Frontend      | React + Vite + TailwindCSS              |
| Scheduling    | APScheduler (täglicher Scrape-Job)       |
| Dev-Umgebung  | Docker Compose                           |

---

## Projektstruktur

```
/
├── scraper/
│   ├── viscaal.py          # Scraper für viscaal.de (Playwright)
│   ├── apeg.py             # Scraper für eu-fahrzeugboerse.de/kunden/ (Playwright)
│   ├── eu_mayer.py         # Scraper für eu-mayer.de (requests + BeautifulSoup)
│   ├── base.py             # Gemeinsame Playwright-Logik
│   ├── db.py               # Sync DB helpers (upsert_vehicle, deactivate_stale)
│   ├── test_scrape.py      # Scraper tests
│   └── scheduler.py        # Täglicher Scrape-Job (alle 3 Quellen)
├── backend/
│   ├── main.py             # FastAPI App + Routen
│   ├── models.py           # SQLAlchemy Modelle
│   ├── schemas.py          # Pydantic Schemas
│   ├── database.py         # DB-Verbindung
│   ├── crud.py             # DB-Operationen
│   └── seed.py             # Seed-Script (Viscaal API + EU-Mayer HTML scraping)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchBar.jsx
│   │   │   ├── VehicleCard.jsx
│   │   │   ├── FilterPanel.jsx
│   │   │   └── VehicleDetail.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   └── Vehicle.jsx
│   │   └── App.jsx
│   └── package.json
├── docker-compose.yml
└── CLAUDE.md
```

---

## Datenquellen & Scraping-Strategie

### Quelle 1: Viscaal (viscaal.de)

- **Typ:** Custom-Website, Inventory **JavaScript-gerendert** → Playwright zwingend
- **Listing-URL:** `https://www.viscaal.de/angebote/`
- **Einzelfahrzeug-URLs:** `https://www.viscaal.de/angebote/{slug}/`
- **Technischer Hinweis:** Die Seite lädt Fahrzeuge via JS nach dem Seitenaufruf.
  `page.wait_for_selector('.vehicle-card')` oder ähnliches Element abwarten.
- **Login erforderlich:** Nein für Consumerpreise. B2B-Preise sind hinter Login.
- **Daten verfügbar (public):**
  - Marke, Modell, Variante
  - Preis (Consumerpreis — kein UVP-Vergleich direkt)
  - Kraftstoffart, Getriebe, Leistung (kW/PS)
  - Kilometerstand, Erstzulassung
  - Verfügbarkeit (Lager / EU-Reimport)
  - Fahrzeugbilder (img src URLs)
- **Scrape-Frequenz:** 1x täglich, nachts (02:00 Uhr)
- **Rate Limiting:** Min. 2–3 Sekunden zwischen Requests, User-Agent rotieren

### Quelle 2: APEG (eu-fahrzeugboerse.de)

- **Typ:** Eigenentwickelte Börse, ebenfalls **JavaScript-gerendert** → Playwright
- **Listing-URL:** `https://eu-fahrzeugboerse.de/kunden/`
- **Technischer Hinweis:** Seite zeigt "Fahrzeuge werden geladen..." beim Abruf —
  warten bis Fahrzeugcontainer sichtbar ist
- **Login erforderlich:** Nein für Consumerbereich (`/kunden/`)
  B2B unter `/haendler/` — nicht scrapen
- **Daten verfügbar (public):**
  - Marke, Modell, Ausstattungslinie
  - Lagerpreis, ggf. UVP-Vergleich
  - Verfügbarkeit (Lager / Vorlauf / Bestellfahrzeug)
  - Kraftstoff, Getriebe, Leistung
  - Farbe, Ausstattungsmerkmale
  - Fahrzeugbilder

### Quelle 3: EU-Mayer (eu-mayer.de)

- **Typ:** Autrado-Plattform, **server-rendered HTML** → requests + BeautifulSoup (kein Playwright nötig)
- **Sitemap:** `https://www.eu-mayer.de/sitemap.xml`
- **Listing-URLs:** `https://www.eu-mayer.de/liste-{brand}-{model}-a__{code}_alle.php`
- **Detail-URLs:** `https://www.eu-mayer.de/auto-{slug}-x__{id}.php`
- **Pagination:** `?npage=1`, `?npage=2`, etc.
- **Login erforderlich:** Nein
- **Gefilterte Marken:** VW, Audi, Skoda, SEAT, Cupra, Hyundai, Kia, Dacia, Ford, MG
  (chinesische/Nischenmarken wie BAIC, Forthing, DFSK werden übersprungen)
- **Daten verfügbar (public):**
  - Marke, Modell, Variante (aus `<h1>`)
  - Preis (aus `span.Gesamtpreis`, Format: `21.000,– €`)
  - Kraftstoff, Getriebe, Leistung, Hubraum, Kategorie (aus `ul.c-vehicle__attributes`)
  - Fahrzeugnr. (aus Seitentext)
  - Bilder (`data-fancybox` Links zu `img.autrado.de` CDN)
  - Lieferzeit → Verfügbarkeit (sofort→lager, Wochen→vorlauf, Monate→bestellung)
- **Scrape-Frequenz:** 1x täglich, nachts (02:00 Uhr, via scheduler.py)
- **Rate Limiting:** 1.5 Sekunden zwischen Requests
- **Implementierung:**
  - `backend/seed.py`: `fetch_eu_mayer_vehicles()` für initiales Seeding
  - `scraper/eu_mayer.py`: Standalone-Scraper (`python eu_mayer.py --limit 5`)
  - Beide nutzen: Sitemap → Listing-Seiten paginieren → Detail-Seiten parsen

### Was NICHT gescrapt wird

- Keine B2B-/Händlerpreise (hinter Login, ToS-relevant)
- Keine persönlichen Kundendaten
- Kein automatisches Bestellen oder Formular-Ausfüllen

---

## Datenbankschema (PostgreSQL)

```sql
CREATE TABLE vehicles (
    id              SERIAL PRIMARY KEY,
    source          VARCHAR(50) NOT NULL,      -- 'viscaal' | 'apeg' | 'eu-mayer'
    source_id       VARCHAR(100) NOT NULL,     -- ID/Slug von der Quellseite
    source_url      TEXT NOT NULL,             -- Direkt-URL zum Original

    -- Fahrzeugdaten
    brand           VARCHAR(100),              -- z.B. 'Volkswagen'
    model           VARCHAR(100),              -- z.B. 'Golf'
    variant         VARCHAR(200),              -- z.B. 'Golf 8 GTI 2.0 TSI'
    trim_line       VARCHAR(100),              -- z.B. 'GTI', 'Style', 'Life'
    body_type       VARCHAR(50),               -- SUV, Kombi, Limousine etc.

    -- Motor & Technik
    fuel_type       VARCHAR(50),               -- Benzin, Diesel, Elektro etc.
    gearbox         VARCHAR(50),               -- Schaltgetriebe, Automatik
    power_kw        INTEGER,
    power_ps        INTEGER,
    engine_cc       INTEGER,

    -- Fahrzeugzustand
    mileage_km      INTEGER,
    first_reg_date  DATE,
    availability    VARCHAR(50),               -- 'lager' | 'vorlauf' | 'bestellung'
    color           VARCHAR(100),

    -- Preise
    price_eur       NUMERIC(10,2),             -- Angebotspreis
    uvp_eur         NUMERIC(10,2),             -- UVP (falls verfügbar)
    savings_eur     NUMERIC(10,2),             -- uvp - price (berechnet)
    savings_pct     NUMERIC(5,2),              -- Ersparnis in %

    -- Medien
    image_urls      TEXT[],                    -- Array von Bild-URLs

    -- Meta
    scraped_at      TIMESTAMP DEFAULT NOW(),
    last_seen_at    TIMESTAMP DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE,

    UNIQUE(source, source_id)
);

CREATE INDEX idx_vehicles_brand ON vehicles(brand);
CREATE INDEX idx_vehicles_price ON vehicles(price_eur);
CREATE INDEX idx_vehicles_availability ON vehicles(availability);
CREATE INDEX idx_vehicles_active ON vehicles(is_active);
```

---

## FastAPI Backend

### Endpunkte

```
GET  /api/vehicles
     ?brand=volkswagen
     &model=golf
     &fuel_type=benzin
     &availability=lager
     &price_min=15000
     &price_max=35000
     &source=viscaal|apeg|eu-mayer|all
     &sort=price_asc|price_desc|savings_desc|scraped_at_desc
     &page=1
     &limit=24

GET  /api/vehicles/{id}          # Fahrzeugdetail

GET  /api/filters                # Verfügbare Filteroptionen (Marken, Modelle etc.)
     → { brands: [...], fuel_types: [...], body_types: [...] }

GET  /api/stats                  # Anzahl Fahrzeuge pro Quelle, letzte Aktualisierung

POST /api/leads                  # Kaufinteresse speichern
     Body: { vehicle_id, name, email, phone, message }
```

### Wichtige FastAPI-Hinweise

- CORS für `localhost:5173` (Vite dev) und Produktions-Domain erlauben
- Pagination immer mit `total_count` im Response zurückgeben
- Fehler bei nicht gefundenem Fahrzeug: HTTP 404 mit klarer Message
- `/api/leads` Rate-Limiting: max 5 Leads pro IP pro Stunde

---

## React Frontend

### Kernseiten & Komponenten

**Home (`/`)**
- Hero-Section: Headline mit Wertversprechen ("Neue Autos bis zu 40% günstiger")
- Suchleiste: Marke → Modell → Verfügbarkeit
- Filterleiste: Preis, Kraftstoff, Getriebe, Quelle
- Fahrzeugliste: Grid aus VehicleCards, 24 pro Seite, Infinite Scroll oder Pagination
- Sortieroption: Preis ↑, Preis ↓, Größte Ersparnis zuerst

**VehicleCard**
- Bild (erstes aus image_urls)
- Marke + Modell + Variante
- Preis groß + Ersparnis-Badge ("Du sparst €4.200 / 15%") in Grün
- Quelle-Badge (Viscaal / APEG / EU-Mayer)
- Verfügbarkeit-Tag (Sofort / Vorlauf / Bestellung)
- CTA-Button: "Mehr Details"

**VehicleDetail (`/fahrzeug/:id`)**
- Bildergalerie
- Vollständige Spezifikationen
- Preisblock: Unser Preis vs. UVP, Ersparnis hervorgehoben
- "Jetzt anfragen"-Formular (Name, E-Mail, Telefon, Nachricht)
- Link zur Originalseite ("Beim Anbieter ansehen")

### UX-Prinzipien

- Preistransparenz ist das #1 Feature — Ersparnis vs. UVP immer sichtbar
- Mobile-First — viele Nutzer kommen von MyDealz auf dem Handy
- Deutsch als Standardsprache
- Ladezeit < 2s für die Hauptliste (Bilder lazy-loaded)
- Skeleton-Loading statt leerer Flächen

---

## Scraper-Implementierung

### Viscaal & APEG (Playwright — JS-rendered)

Beide Seiten rendern Fahrzeugdaten via JavaScript → Playwright zwingend.
Siehe `scraper/viscaal.py` und `scraper/apeg.py`.

**Hinweis:** Viscaal nutzt im Hintergrund die **audaris API**
(`https://api.audaris.de/v1/clients/1473/website-vehicles`). Das Seed-Script
(`backend/seed.py`) nutzt diese API direkt statt Playwright.

### EU-Mayer (requests + BeautifulSoup — server-rendered HTML)

EU-Mayer läuft auf der Autrado-Plattform mit server-gerenderten Seiten.
Kein JavaScript-Rendering nötig → `requests + BeautifulSoup + lxml`.

**Pipeline:** Sitemap XML → Listing-Seiten paginieren → Detail-Seiten parsen

**Wichtige CSS-Selektoren / HTML-Patterns:**
- Preis: `span.Gesamtpreis` (Format: `21.000,– €`)
- Specs: `ul.c-vehicle__attributes` → `<li>` mit Prefix (Kraftstoff, Getriebe, etc.)
- Bilder: `<a data-fancybox href="https://img.autrado.de/...">`
- Fahrzeugnr.: Freitext `Fahrzeugnr.: {id}`
- Lieferzeit: Freitext `Lieferzeit: {text}`

**Test:** `python scraper/eu_mayer.py --limit 5`

---

## Docker Compose Setup

```yaml
version: "3.9"
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: euautos
      POSTGRES_USER: euautos
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://euautos:dev_password@db:5432/euautos
    depends_on:
      - db
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
    environment:
      VITE_API_URL: http://localhost:8000

volumes:
  pgdata:
```

---

## Rechtliche Hinweise für den Prototyp

- Dieser Prototyp ist ausschließlich für **private Validierungszwecke** gedacht
- Keine öffentliche Veröffentlichung der gescrapten Daten ohne Lizenzvereinbarung
- Scraping nur des öffentlich zugänglichen Consumer-Bereichs (kein Login-Bypass)
- Vor Launch: Direkte Partnerschaftsanfrage an Viscaal, APEG und EU-Mayer stellen
- Ziel ist langfristig ein offizieller Datenfeed — Scraping ist nur der MVP-Weg

---

## Nächste Schritte nach dem Prototyp

1. **Partnergespräch mit Viscaal, APEG und EU-Mayer** — offiziellen Datenfeed anfragen
2. **UVP-Daten ergänzen** — z.B. aus DAT.de oder direkt von OEM-Konfiguratoren
3. **Lead-Weiterleitung** — automatische E-Mail an Dealer-Partner bei Anfrage
4. **MyDealz-Integration** — erste Deals manuell posten, Traffic messen
5. **AutoScout24-API** — Inventar auf 100+ Händler ausweiten
