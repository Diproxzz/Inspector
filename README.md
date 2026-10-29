# Automated QC Inspection Report Builder

Automated Quality Control (QC) Image-to-Excel A4 Inspection Report Builder built with FastAPI, PostgreSQL, and a Tailwind CSS / Vanilla JS frontend.

## Features

- **Sequential Image Classification**:
  - Ground-truth trained machine learning model (trained on 800+ real QC inspection photos) classifying images across 11 standard QC inspection sections.
  - Automatic article number, size, and orientation/rotation detection.
  - Real-time progress updates with 1-by-1 live image preview.
- **A4 Review & Layout Canvas**:
  - Interactive web canvas for reviewing and reorganizing categorized images.
  - Human-in-the-Loop (HITL) overrides for categories, captions, rotations, and exclusions.
  - Strict 2-per-row image layout for multi-image sections; collective labels for non-product sections and individual captions for Product & Reference Sample views.
- **Lossless Image Compression**:
  - 220-PPI print fidelity with proportional resizing (no awkward white-space letterboxing and zero cropping of critical product markings, CE stamps, or labels).
- **Exact A4 Excel Export & PDF Print Readiness**:
  - Generates strictly formatted `.xlsx` workbooks via `openpyxl`.
  - Manual page break pagination (`PAGE_BUDGET = 42`) preventing split sections.
  - Clean A4 conversion with 0 blank pages on PDF export.

## Inspection Sections

1. Shipping Marks View
2. Export Carton View
3. Open carton View
4. Bundle View
5. Product View (`# XXXX - XXX - X/X`)
6. Reference Sample View (`# XXXX - XXX `)
7. Gloves Marking View
8. Barcode
9. Leaflet (Front & Back View)
10. Inside Label Front and Back View
11. Rest of the images

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 15+ running locally with database `inspector_qc`:
  ```sql
  CREATE DATABASE inspector_qc;
  ```

### Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the server:
   - On Windows, double-click `start_server.bat` or run:
     ```bash
     python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
     ```
   - Open your browser at [http://localhost:8000](http://localhost:8000).

3. To stop the server cleanly:
   - Click the **"Close Server"** button in the UI navigation bar, or run `stop_server.bat`.

## Deployment

### Option 1: Docker & Docker Compose (Recommended for Any VPS or Local Server)

You can spin up both the FastAPI application and PostgreSQL database with a single command:

```bash
docker compose up -d --build
```

The application will be accessible at `http://<your-server-ip>:8000`.

To view logs or stop:
```bash
docker compose logs -f
docker compose down
```

---

### Option 2: Deploy to Render (Cloud)

1. Go to [Render Dashboard](https://dashboard.render.com).
2. **Create PostgreSQL Database**:
   - Click **New +** -> **PostgreSQL**.
   - Note the **Internal Database URL**.
3. **Create Web Service**:
   - Click **New +** -> **Web Service** -> Connect your GitHub repo (`Diproxzz/Inspector`).
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Under **Environment Variables**, add:
     - `DATABASE_URL`: *(Paste the Internal Database URL from step 2)*
4. Click **Deploy Web Service**.

---

### Option 3: Deploy to Railway

1. Go to [Railway.app](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub repo** -> Select `Inspector`.
3. Click **+ New** -> **Database** -> **PostgreSQL**.
4. In your Web Service settings under **Variables**, set:
   - `DATABASE_URL`: `${{Postgres.DATABASE_URL}}`
5. Railway will automatically detect the `Dockerfile` or `requirements.txt` and deploy.

---

### Option 4: Linux VPS (Ubuntu / Debian with systemd & Nginx)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Diproxzz/Inspector.git
   cd Inspector
   ```

2. **Set up virtual environment & install requirements**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure systemd service (`/etc/systemd/system/inspector.service`)**:
   ```ini
   [Unit]
   Description=Inspector QC FastAPI Service
   After=network.target postgresql.service

   [Service]
   User=www-data
   WorkingDirectory=/var/www/Inspector
   Environment="PATH=/var/www/Inspector/venv/bin"
   Environment="DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/inspector_qc"
   ExecStart=/var/www/Inspector/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000

   [Install]
   WantedBy=multi-user.target
   ```

4. **Enable & Start**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable inspector
   sudo systemctl start inspector
   ```

5. Reverse-proxy via Nginx on port 80/443.

```
Inspector/
├── backend/
│   ├── classifier.py          # Dual-engine sequential classifier (ML model + VLM fallback)
│   ├── compressor.py          # 220-PPI lossless JPEG compressor
│   ├── database.py            # Async PostgreSQL models and connection pool
│   ├── image_formatter.py     # Aspect-ratio preserving image resizer and frame builder
│   ├── main.py                # FastAPI REST API, progress SSE, and lifecycle handlers
│   ├── trained_classifier.pkl # Pre-trained Random Forest model
│   └── xlsx_builder.py        # A4 page-break and cell layout generator
├── frontend/
│   └── index.html             # Responsive Tailwind UI (Upload, Sequential Progress, Canvas)
├── feature_extractor.py       # Visual and color feature extraction pipeline
├── train_classifier.py        # Model training script for ground-truth inspection sets
├── requirements.txt           # Python package dependencies
├── start_server.bat           # Quick launcher script
└── stop_server.bat            # Clean shutdown script
```
