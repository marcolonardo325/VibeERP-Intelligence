# TfL Live Tube Map

Real-time London Underground dashboard powered by **TfL Unified API**, **Flask**, and **Leaflet.js** — with **D365 Finance & Operations** ERP integration for fleet asset management.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![TfL API](https://img.shields.io/badge/TfL-Unified%20API-003688)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Live train positions** across all 11 Underground lines with smooth animation
- **Direction-aware interpolation** — trains move forward along correctly ordered tracks
- **Nearest-neighbour station ordering** — eliminates zig-zag track rendering
- **TfL-style arrivals board** — click any station for real-time departures
- **ERP asset management** — 313 deterministic vehicle maintenance records
- **Fleet health KPIs** — condition, alerts, overdue services at a glance
- **D365 F&O work orders** — create maintenance work orders with email notifications via Microsoft Graph API

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Browser     │◄───►│  Flask Server    │◄───►│  TfL API     │
│  Leaflet.js  │     │  (Python 3.10+) │     │  (Real-time) │
└─────────────┘     └──────┬───────────┘     └──────────────┘
                           │
                    ┌──────▼───────────┐
                    │  Microsoft Graph │
                    │  (Email - opt.)  │
                    └──────────────────┘
```

## Quick Start

```bash
# Clone
git clone https://github.com/marcolonardo325/TfL-LiveTubeMap.git
cd TfL-LiveTubeMap

# Set up Python environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure (optional)
cp .env.example .env
# Edit .env with your TfL API key and/or Graph API credentials

# Run
python live_tube_server.py
```

Open **http://localhost:5050** in your browser.

## Configuration

| Variable | Required | Description |
|---|---|---|
| `TFL_APP_KEY` | No | TfL API key for higher rate limits ([register free](https://api-portal.tfl.gov.uk)) |
| `GRAPH_TENANT_ID` | No | Azure AD tenant for work-order emails |
| `GRAPH_CLIENT_ID` | No | App registration client ID |
| `GRAPH_CLIENT_SECRET` | No | App registration client secret |
| `GRAPH_SENDER_EMAIL` | No | Mailbox to send work-order emails from |

The server works without any environment variables — TfL's API is free and public. Graph API credentials are only needed for the email feature.

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Dashboard UI |
| `/api/tracks` | GET | NN-ordered track polylines per line |
| `/api/stations` | GET | All stations with coordinates |
| `/api/colors` | GET | Line colour mapping |
| `/api/trains` | GET | Live interpolated train positions |
| `/api/arrivals/<naptanId>` | GET | Real-time arrivals for a station |
| `/api/maintenance` | GET | Full vehicle asset dataset |
| `/api/maintenance/<vehicleId>` | GET | Single vehicle detail |
| `/api/fleet-health` | GET | Aggregated fleet KPIs |
| `/api/work-order` | POST | Create D365 F&O work order |

## Tech Stack

- **Backend**: Python 3.10+, Flask, requests, python-dotenv
- **Frontend**: Leaflet.js, CARTO Voyager tiles, vanilla JS
- **Data**: TfL Unified API (real-time), deterministic ERP dataset
- **Email**: Microsoft Graph API (optional)

## License

MIT
