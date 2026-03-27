# Dusty

Discover vintage, antique, and thrift shops in NYC. Track sales and never miss a deal.

## Features

- **Map-based discovery** - Browse shops on an interactive Mapbox map
- **Category filters** - Vintage, Antique, Thrift, Consignment, Clothing, Furniture, Records
- **Sale tracking** - Automatically detects sales from Instagram and shop websites
- **Shop details** - Ratings, hours, photos, and contact info from multiple sources

## Tech Stack

**Frontend**
- Next.js 15 (React 19)
- TypeScript
- Tailwind CSS
- Mapbox GL JS
- React Query

**Backend**
- FastAPI
- SQLAlchemy (async)
- SQLite (dev) / PostgreSQL (prod)

**Data Pipeline**
- Google Places API
- Yelp Fusion API
- OpenStreetMap Overpass API
- Instagram scraping
- Website scraping

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.11+
- Mapbox account (free tier works)
- Optional: Google Places API key, Yelp API key

### Setup

1. **Clone and install dependencies**

```bash
cd dusty

# Frontend
cd frontend
npm install

# Backend
cd ../api
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

2. **Configure environment**

```bash
# Copy example env files
cp .env.example .env
cp frontend/.env.example frontend/.env.local
cp api/.env.example api/.env

# Edit with your API keys
```

3. **Run the development servers**

```bash
# Terminal 1 - Backend
cd api
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

4. **Open http://localhost:3000**

### Running the Data Pipeline

**Discover shops:**
```bash
cd etl/discovery
python run.py
```

**Scrape for sales:**
```bash
cd etl/scrapers
python run.py
```

## Project Structure

```
dusty/
├── frontend/           # Next.js app
│   └── src/
│       ├── app/        # Pages and layouts
│       ├── components/ # React components
│       │   ├── map/    # Mapbox components
│       │   ├── shop/   # Shop-related components
│       │   └── ui/     # Common UI components
│       ├── lib/        # API client and utilities
│       └── types/      # TypeScript types
│
├── api/                # FastAPI backend
│   ├── core/           # Config, database
│   ├── models/         # SQLAlchemy models
│   ├── routers/        # API endpoints
│   └── services/       # Business logic
│
├── etl/                # Data pipelines
│   ├── discovery/      # Shop discovery
│   │   ├── google_places.py
│   │   ├── yelp.py
│   │   └── osm.py
│   └── scrapers/       # Sale detection
│       ├── instagram.py
│       └── website.py
│
└── config/             # Configuration files
    └── settings.yaml
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/shops` | List shops with filters |
| `GET /api/v1/shops/{id}` | Get shop details |
| `GET /api/v1/sales` | List sales with filters |
| `GET /api/v1/sales/active` | Get active sales |
| `GET /api/v1/neighborhoods` | List neighborhoods |
| `POST /api/v1/discovery/shops` | Trigger shop discovery |
| `POST /api/v1/discovery/sales` | Trigger sale scraping |

## Shop Categories

| Category | Description |
|----------|-------------|
| `vintage` | Clothing and items 20+ years old |
| `antique` | Items 100+ years old |
| `thrift` | Budget secondhand stores |
| `consignment` | High-end resale |
| `clothing` | Vintage fashion specialty |
| `furniture` | Antique furniture dealers |
| `records` | Vinyl and vintage audio |

## Sale Detection

Dusty automatically detects sales by:

1. **Instagram monitoring** - Scans posts for sale keywords like "% off", "clearance", "flash sale"
2. **Website scraping** - Checks shop homepages and sale pages for promotions
3. **Confidence scoring** - Ranks detections by confidence level

Keywords detected:
- Percentage discounts ("20% off", "up to 50%")
- Sale types ("flash sale", "sample sale", "warehouse sale")
- Time-sensitive ("today only", "ends Sunday", "limited time")

## Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a PR

## License

MIT
