# From Static Dashboards to Living Operations: How We Built a Real-Time Digital Twin of the London Underground in a Weekend

**And what it means for the future of enterprise asset management**

---

*You're looking at a live map. Not a screenshot. Not a slide deck. An actual, real-time map of every train on the London Underground — 230+ vehicles, 272 stations, 11 lines — updating every second, with each train smoothly animating between stations.*

*Click any station and a departure board appears, identical to the ones on the platform. Click any train and you see its full maintenance history: condition scores, brake status, HVAC readings, open work orders. One more click and a formatted work order is created in Dynamics 365 Finance & Operations, with an email notification sent to the maintenance team via Microsoft Graph.*

*This entire system — frontend, backend, data pipeline, ERP integration — was built in a weekend. Two files. Three dependencies.*

*That's the point.*

---

## The Problem We Keep Solving Badly

Every enterprise I've worked with has the same challenge: **operational data exists in real time, but decisions are made on yesterday's report.**

Fleet managers open Excel exports at 9 AM to review maintenance schedules generated the night before. Supply chain leaders look at Power BI dashboards refreshed hourly. Operations teams toggle between four different systems to correlate an asset's location with its service history.

The data is there. The latency is the problem.

And latency isn't just about refresh rates. It's about cognitive latency — the gap between *seeing* something and *doing* something about it. When your maintenance engineer has to leave the monitoring screen, open the ERP, search for the asset, fill out a form, and submit a work order, you've introduced 15 minutes of friction between a decision and an action.

**That friction has a cost.** Unplanned downtime. Missed SLAs. Parts ordered too late. Assets running past their service windows because nobody noticed until the weekly review.

## What We Built — and Why It Matters

This proof of concept is deliberately simple. It uses the **London Underground** as a stand-in for any large-scale fleet operation — rail, logistics, energy, manufacturing — and demonstrates what happens when you collapse the distance between monitoring, analysis, and action into a single pane of glass.

### The Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (Single Page)                 │
│  ┌──────────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │  Live Map     │  │  KPIs    │  │  Arrivals Board   │  │
│  │  (Leaflet.js) │  │  Panel   │  │  (TfL-style)      │  │
│  └──────┬───────┘  └────┬─────┘  └─────────┬─────────┘  │
│         │               │                   │            │
│         └───────────────┼───────────────────┘            │
│                    REST API (1s poll)                     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│               Flask Server (Python)                      │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  TfL Unified  │  │  Maintenance │  │  Graph API   │  │
│  │  API Client   │  │  Engine      │  │  (Email)     │  │
│  │  (10s refresh)│  │  (313 assets)│  │  (Work Order)│  │
│  └───────┬───────┘  └──────────────┘  └──────────────┘  │
└──────────┼──────────────────────────────────────────────┘
           │
┌──────────▼──────────┐
│  TfL Unified API    │
│  (Public, Real-Time)│
│  api.tfl.gov.uk     │
└─────────────────────┘
```

There are exactly **three runtime dependencies**: Flask, Requests, and python-dotenv. No Kafka. No Redis. No Kubernetes. No Terraform. The entire server is a single Python file. The entire frontend is a single HTML file.

This is intentional. We are not demonstrating infrastructure. We are demonstrating a **pattern**.

### What Happens Under the Hood

**Every 10 seconds**, the server calls TfL's Arrivals API and receives the predicted arrival time of every vehicle on every line. We deduplicate by vehicle ID, keeping only the nearest prediction.

**Every second**, the frontend requests the latest positions. The server takes the raw predictions, calculates how much time has elapsed since the last TfL update, and **interpolates** each vehicle's position between its previous station and its target station — accounting for direction of travel.

The result: trains move smoothly and realistically across the map, even though the source data only updates every 10 seconds. The user sees 60fps animation built on 0.1 Hz data. This is the same principle used in multiplayer gaming and GPS navigation — **client-side prediction over server-side truth**.

**Station ordering** uses a nearest-neighbour algorithm to chain stops geographically. This eliminates the zig-zag rendering that plagues naive approaches to line mapping and produces clean, accurate track polylines without any hardcoded geometry.

### The ERP Layer

Each of the 313 vehicles carries a **deterministic maintenance profile** — condition scores, component status, service history, open work orders — generated using seeded random functions tied to the vehicle ID. The same vehicle always produces the same asset record.

This simulates what a real D365 Finance & Operations integration would provide: a rolling stock master record enriched with IoT telemetry, maintenance logs, and procurement data.

From the dashboard, a fleet manager can:

1. **See** a train's real-time position on the map
2. **Click** it to inspect its full maintenance profile
3. **Decide** it needs attention
4. **Create a work order** with one click — generating a structured record and sending a formatted HTML email to the maintenance team via Microsoft Graph

Steps 1 through 4 happen in the same window, in under 5 seconds.

## Why This Matters for the C-Suite

### 1. Mean Time to Action (MTTA) Is the New KPI

We talk endlessly about Mean Time to Detect (MTTD) and Mean Time to Repair (MTTR). But the bottleneck in most organisations isn't detection or repair — it's the decision in between. The time it takes for someone to see a problem, locate the right system, and initiate the right process.

This POC reduces MTTA to **under 5 seconds** for any vehicle in a 230+ unit fleet.

Scale that. What if your logistics coordinator could see a truck approaching a depot with a declining brake condition score and create a maintenance reservation before it arrives? What if your plant manager could click a machine on a floor plan and submit a parts request to the ERP without switching applications?

### 2. From Prototype to Production in Days, Not Quarters

The TfL Unified API is **free and public**. The server runs on any machine with Python. The frontend is static HTML. There is no cloud infrastructure required for the POC — no App Service, no database, no message queue.

In a production scenario, you'd add authentication, HTTPS, and probably a managed database. But the prototype-to-production gap is measured in days, not quarters. This is not a PowerPoint architecture diagram that requires six months of infrastructure work. It's running code.

### 3. Composability Over Monoliths

This system is **six files**. It connects to two external APIs (TfL for real-time data, Microsoft Graph for email) and exposes nine REST endpoints. Any of those endpoints can be consumed by other systems — Power BI, a mobile app, a Teams bot, another microservice.

The value of this architecture isn't in the dashboard itself. It's in the **principle of composable operational intelligence**: real-time data sources, lightweight middleware, domain-specific UIs, and ERP integration as an API call rather than a module.

### 4. Digital Twin Thinking, Without the Complexity

The term "digital twin" has been corrupted by vendors selling heavyweight platforms that take years to implement. What we built here is, functionally, a digital twin: a real-time, interactive virtual representation of a physical system (the Tube network) that reflects current state and enables operational actions.

It proves that the **concept** is sound and achievable with minimal investment. The question for your organisation is not "should we build a digital twin?" but "what data do we already have that we're not using in real time?"

## Where This Goes Next

This POC was built for a conference demo, but the pattern applies directly to:

- **Rail & Transit**: Fleet management across rolling stock, with predictive maintenance triggered by condition thresholds
- **Logistics & Distribution**: Live vehicle tracking with integrated route optimisation and warehouse management
- **Manufacturing**: Production floor visualisation with real-time OEE and automated work order generation
- **Energy & Utilities**: Grid or pipeline monitoring with asset health overlays and incident response workflows
- **Facilities Management**: Building operations with HVAC, elevator, and lighting systems mapped to maintenance schedules

The implementation path is the same in each case:

1. **Identify your TfL** — the real-time data source you already have (IoT platform, SCADA, telematics provider, API)
2. **Map it to your ERP** — connect asset records in D365 F&O (or SAP, or Oracle) to the live telemetry
3. **Build the decision surface** — the single UI where monitoring, analysis, and action converge
4. **Measure MTTA** — track how fast your team goes from observation to action, and optimise ruthlessly

## The Technical Details (For Your CTO)

| Component | Technology | Why |
|---|---|---|
| Real-time data | TfL Unified API (REST, 10s poll) | Free, reliable, well-documented. Stand-in for any IoT/telematics API |
| Backend | Python + Flask (single file, 500 lines) | Fast to build, easy to extend, runs anywhere |
| Frontend | Leaflet.js + vanilla JS (single file) | No build step, no framework lock-in, 60fps animation |
| Asset data | Deterministic seeded generation (JSON) | Simulates D365 F&O master data without requiring a live ERP instance |
| Work orders | REST POST → local JSON + Graph API email | Best-effort email; always persists locally. Production would write to D365 OData |
| Auth / secrets | python-dotenv (.env file) | Secrets never in code, easy to swap for Azure Key Vault in production |
| Deployment | `python live_tube_server.py` | One command. No containers, no orchestration, no cloud required for demo |

**GitHub**: [github.com/marcolonardo325/TfL-LiveTubeMap](https://github.com/marcolonardo325/TfL-LiveTubeMap)

## The Takeaway

We have entered an era where building a real-time operational dashboard, complete with fleet tracking, asset management, and ERP integration, is a **weekend project** for a single developer.

The technology is not the constraint. The data is not the constraint. The constraint is the imagination to connect what we already have into systems that let people **see, decide, and act** — all in the same breath.

If your operations team is still toggling between five tabs to answer one question, the gap between where you are and where this POC sits is not a technology gap. It's a design gap.

And it's smaller than you think.

---

*Marco Lonardo is a consultant specialising in Dynamics 365 Finance & Operations and enterprise integration. This proof of concept was built live as part of a conference demonstration on real-time operational intelligence.*

*The full source code is available at [github.com/marcolonardo325/TfL-LiveTubeMap](https://github.com/marcolonardo325/TfL-LiveTubeMap).*
