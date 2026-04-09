<p align="center">
  <img src="https://img.shields.io/badge/Dynamics%20365-0078D4?style=for-the-badge&logo=dynamics365&logoColor=white" alt="D365 F&O"/>
  <img src="https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/TypeScript_6-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS_4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind"/>
  <img src="https://img.shields.io/badge/Python_Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/>
</p>

<h1 align="center">VibeERP Intelligence</h1>
<h3 align="center">AI-Ready Procurement Command Centre for Microsoft Dynamics 365 Finance & Operations</h3>

<p align="center">
  <em>A modern, real-time procurement intelligence platform that transforms Dynamics 365 F&O data<br/>into actionable insights — enabling faster decisions, lower costs, and stronger supplier relationships.</em>
</p>

---

## The Business Challenge

Most procurement teams still operate from static spreadsheets and fragmented ERP screens. Critical questions — *Which vendors are underperforming? Where is spend concentrated? Are we on-target for our agreements?* — take hours or days to answer. This slows decision-making, erodes negotiating power, and creates blind spots across the supply chain.

**VibeERP Intelligence** solves this by providing a **single pane of glass** over your Dynamics 365 Finance & Operations procurement data, with live KPIs, vendor scorecards, spend analytics, and the ability to create purchase orders — all from one modern interface.

---

## Business Value & Estimated Impact

| Outcome | Estimated Impact | How |
|---------|-----------------|-----|
| **Procurement Cycle Reduction** | 30 – 50% faster | Direct PO creation from a unified portal eliminates multi-screen ERP navigation |
| **Spend Visibility** | 100% real-time | Category and vendor spend analysis — instantly, not after month-end reporting |
| **Vendor Risk Reduction** | Early warning | OTIF, fill-rate, and defect-rate scorecards highlight underperformers before they impact operations |
| **Agreement Compliance** | Full coverage | Purchase agreement monitoring ensures negotiated terms are actually leveraged |
| **Data-Driven Negotiations** | 5 – 15% savings | Pareto analysis and vendor benchmarking arm procurement leaders with evidence |
| **Executive Reporting** | Self-service | C-Level dashboards eliminate the reporting backlog from finance and procurement teams |

---

## Key Features

### 📊 Executive Dashboard
Real-time KPI cards (total vendors, open POs, active products, agreement count) with top vendor spend charts and recent order activity.

### 👥 Vendor Management
Searchable vendor directory with group classification, currency, and direct links to D365 records.

### 📝 Purchase Order Management
Browse all POs with status tracking. **Create new purchase orders** directly from the portal — with searchable vendor and product dropdowns, quantity input, and entity selection — pushed live into D365 F&O.

### 🤝 Purchase Agreements
Monitor active, confirmed, and effective agreements with status badge indicators and expiry tracking.

### 📦 Product Catalogue
Full released product listing with item numbers, descriptions, and product types.

### 🎯 Vendor Performance & OTIF Metrics
Scorecard for every vendor: **on-time delivery, fill rate, quality/defect rate, total spend, PO count, and agreement coverage** — colour-coded for instant interpretation.

### 📈 Procurement Analytics (7 Visualisations)
| Chart | Insight |
|-------|---------|
| Top Vendor Spend (Bar) | Where is the money going? |
| Category Spend (Donut) | Which categories dominate procurement? |
| Spend Pareto (Area) | 80/20 analysis — which vendors drive 80% of spend? |
| PO Status Distribution (Pie) | How many POs are open vs. confirmed vs. invoiced? |
| Vendor Order Volume (Grouped Bar) | Compare vendor activity side-by-side |
| Vendor Radar Comparison | Multi-dimension comparison of top 5 vendors |
| Most Procured Items (Bar) | Which products are ordered most frequently? |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER / BROWSER                           │
│                                                                 │
│   ┌───────────────────────────────────────────────────────┐     │
│   │              React 19 + TypeScript 6                  │     │
│   │         Tailwind CSS 4  •  Recharts  •  Vite          │     │
│   │                                                       │     │
│   │  Dashboard │ Vendors │ POs │ Agreements │ Analytics   │     │
│   └──────────────────────┬────────────────────────────────┘     │
└──────────────────────────┼──────────────────────────────────────┘
                           │  HTTP / REST
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Flask API Bridge (Python)                    │
│                                                                  │
│   • OAuth2 Client Credentials (Azure AD)                         │
│   • Request proxying & error handling                            │
│   • CORS-enabled for local development                           │
│   • Environment variable secrets management (.env)               │
└──────────────────────────┬───────────────────────────────────────┘
                           │  OData v4 / HTTPS
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│              Microsoft Dynamics 365 Finance & Operations         │
│                                                                  │
│   VendorsV2 • ReleasedProductsV2 • PurchaseOrderHeadersV2       │
│   PurchaseOrderLinesV2 • PurchaseAgreements • LegalEntities      │
│   InventorySitesOnHand • Warehouses • TradeAgreementJournals     │
└──────────────────────────────────────────────────────────────────┘
```

**Why a Flask bridge?** Direct browser-to-D365 calls expose OAuth client secrets and hit CORS restrictions. The Python bridge keeps credentials server-side, handles token management, and provides a clean REST API for the frontend.

---

## Screenshots

> **Add your own screenshots below.** Run the app, capture each page, and place images in a `docs/` folder.

| View | Screenshot |
|------|-----------|
| Dashboard | ![Dashboard](docs/dashboard.png) |
| Vendor Metrics | ![Vendor Metrics](docs/vendor-metrics.png) |
| Analytics | ![Analytics](docs/analytics.png) |
| Purchase Orders | ![Purchase Orders](docs/purchase-orders.png) |
| Create PO Modal | ![Create PO](docs/create-po.png) |
| Purchase Agreements | ![Agreements](docs/agreements.png) |

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | React + TypeScript | 19.2 / 6.0 |
| Styling | Tailwind CSS | 4.2 |
| Charts | Recharts | 3.0 alpha |
| Icons | Lucide React | 1.7 |
| Build | Vite | 8.0 |
| API Bridge | Python Flask | 3.x |
| Auth | Azure AD OAuth2 | Client Credentials |
| ERP | Dynamics 365 F&O | OData v4 |

---

## Getting Started

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.10+
- **Dynamics 365 F&O** environment with OData enabled
- **Azure AD App Registration** with client credentials and D365 API permissions

### 1. Clone & Install

```bash
git clone https://github.com/marcolonardo325/VibeERP-Intelligence.git
cd VibeERP-Intelligence
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Azure AD and D365 credentials:

```
TENANT_ID=your-azure-tenant-id
CLIENT_ID=your-app-registration-client-id
CLIENT_SECRET=your-client-secret
D365_URL=https://your-instance.operations.dynamics.com
```

### 3. Start the API Bridge

```bash
cd server
pip install -r requirements.txt
python bridge_scm.py
```

The bridge runs on `http://localhost:5000`.

### 4. Start the Frontend

```bash
cd vibe-erp-react
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Project Structure

```
VibeERP-Intelligence/
├── vibe-erp-react/          # React frontend
│   └── src/
│       ├── App.tsx           # Main application (all views + PO modal)
│       ├── hooks/
│       │   └── useProcurement.ts   # Data layer — fetches all D365 data
│       └── types/
│           └── d365.ts       # TypeScript interfaces for D365 entities
├── server/
│   ├── bridge_scm.py        # Flask API bridge to D365 F&O
│   └── requirements.txt     # Python dependencies
├── .env.example              # Environment variable template
└── README.md
```

---

## Security

- **No secrets in source code** — all credentials load from `.env` (git-ignored)
- **Server-side auth only** — OAuth tokens never reach the browser
- **Git history scrubbed** — any previously committed secrets have been removed via `git-filter-repo`
- **CORS restricted** — Flask bridge only accepts requests from configured origins

---

## Roadmap

- [ ] AI-powered spend anomaly detection
- [ ] Automated vendor risk scoring with ML
- [ ] Natural language PO creation via Copilot
- [ ] Power BI embedded dashboards
- [ ] Multi-entity / multi-company support
- [ ] Role-based access control

---

<p align="center">
  <strong>Built with ❤️ for modern procurement teams</strong><br/>
  <sub>Powered by Microsoft Dynamics 365 Finance & Operations</sub>
</p>
