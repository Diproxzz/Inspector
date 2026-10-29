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

## Project Structure

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
