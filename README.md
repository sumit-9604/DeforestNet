# DeforestNet – AI-Powered Deforestation Detection & Reporting Agent



**Aligned with UN Sustainable Development Goals: SDG 13 (Climate Action) & SDG 15 (Life on Land)**



---



## 1. Executive Summary



DeforestNet is an autonomous AI agent that combines free, open-access satellite imagery with a Large Language Model (LLM) reasoning layer to detect, verify, and report illegal deforestation and logging activity in near real-time. The agent continuously monitors defined forest regions, cross-references detected changes against protected-area boundaries and historical patterns, and automatically generates structured, evidence-backed reports for forest departments, NGOs, and conservation authorities — reducing the manual effort, delay, and cost currently involved in catching illegal logging before permanent damage occurs.



---



## 2. Problem Statement



Illegal deforestation is one of the leading drivers of biodiversity loss and climate change, contributing roughly 10% of global greenhouse gas emissions. Despite satellite monitoring technology existing for years, most forest departments and NGOs — especially in developing countries — lack the technical capacity, budget, or staff to:



- Continuously monitor large forest areas manually

- Distinguish natural forest loss (fire, disease) from illegal human-driven logging

- Cross-reference alerts against legal boundaries and land-use permits

- Generate timely, evidence-ready reports that can be acted upon by authorities before loggers move on



**As a result:**

- Illegal logging often goes undetected for weeks or months

- By the time action is taken, the damage is irreversible

- NGOs and understaffed forest departments are overwhelmed by raw, unfiltered alert data with no context or prioritization



**Core Problem:** There is a gap between *raw satellite detection data* (which already exists and is free) and *actionable, prioritized, human-readable intelligence* that authorities can actually act on quickly.



DeforestNet closes this gap using an AI reasoning layer on top of existing satellite alert systems.



---



## 3. Objectives



1. Automatically detect forest cover loss using satellite data with minimal latency (weekly or faster).

2. Differentiate high-risk illegal logging patterns from natural/permitted land-use change using contextual reasoning.

3. Auto-generate structured, evidence-based reports (with maps, coordinates, timestamps, and risk scoring).

4. Route reports to the correct authority/NGO automatically based on jurisdiction.

5. Provide a public-facing dashboard for transparency and community reporting.



---



## 4. SDG Alignment



| Goal | Target | How DeforestNet Contributes |

|------|--------|------------------------------|

| **SDG 15 – Life on Land** | 15.2 – Promote sustainable management of forests, halt deforestation | Direct detection and reporting of illegal logging activity |

| **SDG 13 – Climate Action** | 13.3 – Improve education, awareness, and institutional capacity on climate mitigation | Provides authorities with actionable climate-relevant data and reduces carbon-emitting deforestation |

| **SDG 16 (secondary)** | 16.6 – Effective, accountable institutions | Report trail creates accountability and an auditable evidence chain |



---



## 5. Data Sources & Satellite Imagery (All Free/Open Access)



| Source | Type | Resolution | Update Frequency | Cost | Use in DeforestNet |

|--------|------|------------|-------------------|------|----------------------|

| **Global Forest Watch (GFW) – GLAD & RADD Alerts** | Pre-processed deforestation alert API | 10–30m pixel alerts | Weekly (GLAD), near-daily (RADD) | Free | Primary detection signal — no need to process raw imagery |

| **Sentinel-2 (ESA Copernicus)** | Raw multispectral satellite imagery | 10m | Every 5 days | Free | Before/after visual verification, NDVI vegetation index calculation |

| **Planet NICFI (Norway's Forest Initiative)** | High-res tropical forest imagery | 4.7m | Monthly | Free (registration required) | High-resolution visual evidence for reports |

| **Landsat 8/9 (USGS)** | Raw satellite imagery | 30m | 16 days | Free | Long-term historical trend comparison |

| **Hansen Global Forest Change Dataset** | Labeled ground-truth tree cover loss | 30m, annual | Yearly | Free | Model validation / training reference |

| **Google Earth Engine** | Cloud processing platform | N/A | N/A | Free (research/nonprofit) | Unified access + pre-processing (cloud masking, compositing) for all above |

| **Protected Planet (WDPA)** | Protected area boundary database | Vector/GeoJSON | Static/updated periodically | Free | Determines if alert falls inside a legally protected zone |



**Conclusion: Yes — sufficient free datasets and satellite imagery exist for this project.** No paid data source is required to build a fully functional prototype.



---



## 6. System Architecture



### 6.1 High-Level Architecture Diagram (described)



```

 ┌─────────────────────┐

 │   Data Ingestion     │  ← GFW API, Sentinel-2, Planet NICFI, Landsat

 │       Layer          │

 └──────────┬───────────┘

            │

            ▼

 ┌─────────────────────┐

 │  Change Detection    │  ← NDVI comparison, alert clustering,

 │      Engine          │     before/after image diffing

 └──────────┬───────────┘

            │

            ▼

 ┌─────────────────────┐

 │  Context Enrichment  │  ← Protected area check, land-permit lookup,

 │       Module         │     historical pattern check

 └──────────┬───────────┘

            │

            ▼

 ┌─────────────────────┐

 │   LLM Reasoning       │  ← Risk scoring, natural-language report

 │      Layer            │     generation, anomaly explanation

 └──────────┬───────────┘

            │

            ▼

 ┌─────────────────────┐

 │  Report & Evidence    │  ← PDF/JSON report with maps, coordinates,

 │     Generator         │     images, risk level, recommended action

 └──────────┬───────────┘

            │

            ▼

 ┌─────────────────────┐

 │  Routing & Delivery   │  ← Auto-email/API push to forest dept/NGO,

 │       Module          │     public dashboard update

 └─────────────────────┘

```



### 6.2 Data Flow Summary



1. Agent runs on a schedule (e.g., daily cron job) for defined regions of interest (ROIs).

2. Pulls latest alerts from GFW API for those ROIs.

3. For flagged coordinates, pulls before/after Sentinel-2 or Planet imagery.

4. Computes vegetation index (NDVI) difference to confirm real forest loss vs. false positive (cloud shadow, seasonal change).

5. Cross-checks coordinates against protected area boundaries (WDPA) and any locally maintained permit database.

6. Passes structured data (location, area lost, time window, protection status, historical alert frequency in the area) to the LLM reasoning layer.

7. LLM generates: risk classification (Low/Medium/High/Critical), a plain-language incident summary, and a recommended action.

8. System compiles a report (PDF + JSON) with map snapshot, before/after images, and metadata.

9. Report is auto-routed via email/API to the relevant forest department or NGO, and logged to a public dashboard.



---



## 7. Component Description



### 7.1 Data Ingestion Layer

- **Function:** Connects to external APIs to fetch alerts and imagery.

- **Tech:** Python (`requests`, `sentinelhub-py`, `earthengine-api`, GFW REST API client)

- **Output:** Raw alert coordinates + raw/processed satellite tiles



### 7.2 Change Detection Engine

- **Function:** Confirms genuine forest cover loss using NDVI (Normalized Difference Vegetation Index) comparison between two time periods; filters out noise (clouds, seasonal variation).

- **Tech:** NumPy, rasterio, OpenCV for image diffing

- **Output:** Confirmed change polygons with area (hectares) lost



### 7.3 Context Enrichment Module

- **Function:** Adds legal/geographic context — is this area protected? Is there a history of repeated alerts here (indicating an active illegal logging operation vs. a one-off)?

- **Tech:** GeoPandas, WDPA shapefiles, spatial join operations

- **Output:** Enriched alert object (location + legal status + historical frequency)



### 7.4 LLM Reasoning Layer (Core Intelligence)

- **Function:** Takes structured enriched data and reasons about severity, likely intent (illegal vs legal clearing), and drafts a human-readable report. This is the "agent" decision-making core.

- **Tech:** Claude API (via `/v1/messages` endpoint) with a structured system prompt instructing it to output risk scoring and report text in JSON format for downstream use.

- **Output:** Risk level, narrative summary, recommended action, urgency flag



### 7.5 Report & Evidence Generator

- **Function:** Compiles all data into a shareable, exportable report — PDF with embedded before/after map images, GPS coordinates, timestamps, and a clear evidence trail (so the report can be used administratively/legally).

- **Tech:** Python (`reportlab` or `python-docx`), map rendering via `folium` or `matplotlib`

- **Output:** PDF/DOCX report + JSON metadata



### 7.6 Routing & Delivery Module

- **Function:** Sends the report to the correct jurisdiction's authority/NGO contact based on the location of the alert; updates a public dashboard for transparency.

- **Tech:** Email API (SMTP/SendGrid), simple REST endpoint, dashboard (React/Next.js or Streamlit)

- **Output:** Delivered report + dashboard entry



---



## 8. API Documentation (Data Sources Used)



### 8.1 Global Forest Watch (GFW) API

- **Base URL:** `https://data-api.globalforestwatch.org/`

- **Auth:** Free API key via developer registration

- **Key Endpoint Example:** `/dataset/gfw_integrated_alerts/latest/query`

- **Request Method:** GET/POST with SQL-like query parameters (geometry, date range)

- **Response:** JSON array of alert points with lat/lon, confidence level, and date detected



### 8.2 Sentinel Hub / Copernicus Data Space

- **Base URL:** `https://services.sentinel-hub.com/` or `https://dataspace.copernicus.eu/`

- **Auth:** Free account + OAuth2 token

- **Key Endpoint:** Process API for custom NDVI band calculation on a given bounding box + date range

- **Response:** GeoTIFF/PNG image or raw band values



### 8.3 Planet NICFI API

- **Base URL:** `https://api.planet.com/basemaps/v1/mosaics`

- **Auth:** Free API key (requires NICFI program approval)

- **Key Endpoint:** Mosaic tile service for monthly tropical basemaps

- **Response:** Tile images (XYZ tile format) for given coordinates/month



### 8.4 Google Earth Engine

- **Access:** Python/JS client library (`earthengine-api`)

- **Auth:** Free Google account + Earth Engine registration

- **Function used:** `ee.ImageCollection('COPERNICUS/S2_SR')` filtered by date/region for NDVI computation



### 8.5 Protected Planet (WDPA)

- **Base URL:** `https://www.protectedplanet.net/`

- **Access:** Downloadable shapefile/GeoJSON (no live API call needed) — loaded locally for spatial joins



### 8.6 Claude API (LLM Reasoning Layer)

- **Base URL:** `https://api.anthropic.com/v1/messages`

- **Auth:** API key

- **Function:** Send structured JSON of enriched alert data → receive structured risk assessment + report narrative in response



---



## 9. Technology Stack Summary



| Layer | Technology |

|-------|------------|

| Data Ingestion | Python, GFW API, Sentinel Hub API, Planet API |

| Geospatial Processing | GeoPandas, rasterio, Shapely |

| Image Processing | OpenCV, NumPy |

| AI Reasoning | Claude API (LLM) |

| Report Generation | ReportLab / python-docx, Folium |

| Backend | Python (FastAPI/Flask) |

| Frontend Dashboard | React.js or Streamlit |

| Scheduling | Cron job / Airflow |

| Notification | SMTP / SendGrid API |

| Storage | PostgreSQL + PostGIS (for spatial data), or simple JSON/CSV for prototype |



---



## 10. Evaluation Metrics



| Metric | Purpose |

|--------|---------|

| Detection latency | Time between actual logging event and alert generation |

| False positive rate | % of alerts that are not genuine deforestation (cloud, seasonal) |

| Risk classification accuracy | Compared against known historical illegal logging cases |

| Report turnaround time | Time from detection to report delivery |

| Area monitored (km²) | Scale of coverage |

| Authority response rate | % of reports acted upon (real-world pilot metric) |



---



## 11. Expected Impact



- Reduces detection-to-action time from **weeks/months to days**

- Gives resource-constrained forest departments and NGOs a force-multiplier — no need for large monitoring teams

- Creates an auditable evidence trail that can support legal action against illegal logging operations

- Scalable to any forest region globally using only free data sources

- Supports data-driven climate policy and carbon-credit verification efforts



---



## 12. Limitations & Future Scope



**Current Limitations:**

- Cloud cover can delay optical satellite detection (mitigated by using radar-based RADD alerts as backup)

- Resolution limits (10m Sentinel-2) may miss very small-scale illegal clearing

- Requires initial manual setup of regions of interest and authority contact mapping



**Future Enhancements:**

- Integrate SAR (Synthetic Aperture Radar) data (e.g., Sentinel-1) for all-weather, cloud-penetrating detection

- Add drone/citizen-reported imagery as a supplementary detection layer

- Train a custom computer vision model on labeled Hansen dataset for improved precision

- Multi-language report generation for local authority accessibility

- Blockchain-based evidence logging for tamper-proof legal admissibility



---

## 13. Local Development & Setup

### 13.1 Prerequisites
- Python 3.9+
- Node.js (v18+) and npm

### 13.2 Environment Setup
Create a `.env` file inside the `backend/` directory based on the following configuration:
```env
# Operations Mode (Set to False to use live satellite imagery instead of simulated fallback)
SIMULATION_MODE=False

# Sentinel Hub API Credentials
SENTINEL_HUB_CLIENT_ID=your_client_id
SENTINEL_HUB_CLIENT_SECRET=your_client_secret

# Planet API Key
PLANET_API_KEY=your_planet_api_key

# Global Forest Watch (GFW) API Key
GFW_API_KEY=your_gfw_api_key

# LLM Reasoning Configuration
LLM_PROVIDER=gemini # Choose 'gemini', 'claude', or 'mock'
GEMINI_API_KEY=your_gemini_api_key
```

### 13.3 Running the Backend
1. Initialize the virtual environment and activate it:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install the Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Run the FastAPI development server:
   ```bash
   uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend API documentation will be available at `http://127.0.0.1:8000/docs`.

### 13.4 Running the Frontend
1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install the JavaScript packages:
   ```bash
   npm install
   ```
3. Launch the Vite development server:
   ```bash
   npm run dev
   ```
   The dashboard will be active at `http://localhost:3000`.

### 13.5 Robust Fallback Design
If the configured LLM API (such as the Gemini free-tier) hits quota rate limits (HTTP `429`), the planner automatically switches execution to a rule-based state machine (`_decide_mock_state_machine` in [planner.py](file:///Users/stone/DeforestNet/backend/agent/planner.py)) to ensure continuous verification and report generation.

---

## 14. Conclusion

DeforestNet demonstrates how freely available satellite data, combined with an LLM-powered reasoning layer, can close the critical gap between raw environmental monitoring data and actionable, authority-ready intelligence. By automating detection, verification, and reporting, the agent directly supports SDG 13 (Climate Action) and SDG 15 (Life on Land), offering a scalable, low-cost solution deployable in any forest region worldwide — entirely using free and open-access data sources.



---



*Prepared as a project submission document for DeforestNet – AI-Powered Deforestation Detection & Reporting Agent.*



