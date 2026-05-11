# Real-Time Tube Tracking Digital Twin with TfL, Flask and D365 F&O

## Turning a public transport API into a live operational command centre — and a one-click ERP work order

---

## Introduction

In most enterprises, the gap between *seeing* a problem and *acting* on it is measured in screens, not seconds. An operator spots an anomaly on a monitoring dashboard, switches to the ERP, searches for the asset, fills in a form, and — fifteen minutes later — a work order finally exists.

That latency is the real cost. Not the data, not the infrastructure: the *cognitive distance* between observation and action.

In this article I'll walk through a proof of concept that collapses that distance to a single click. We're tracking every train on the **London Underground** in real time — 230+ vehicles, 272 stations, 11 lines — and wiring each moving asset directly into **Dynamics 365 Finance & Operations** as a maintainable enterprise asset. Click a train, see its condition profile, raise a work order, fire an email via Microsoft Graph. All in the same window, in under five seconds.

The system was built in a weekend. Two files. Three Python dependencies. No cloud infrastructure required to run the demo.

**One Blueprint, Infinite Industries**
While the demo uses the Tube as a stand-in, the same pattern applies to logistics fleets, manufacturing lines, energy grids, rail rolling stock, or any operation where physical assets emit telemetry and an ERP holds the master record.

---

## Architecture — from public API to ERP work order

The end-to-end flow has five components, each kept deliberately thin so the *pattern* — not the plumbing — is what stands out.

```
┌──────────────────────────────────────────────────────────────┐
│                  Browser (single HTML file)                  │
│   Live Map · KPIs · Arrivals Board · Asset Inspector         │
└─────────────────────────┬────────────────────────────────────┘
                          │  REST poll @ 1 Hz
┌─────────────────────────▼────────────────────────────────────┐
│              Flask Server (single Python file)               │
│   ┌────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│   │ TfL Client │  │ Maintenance  │  │ D365 F&O + Graph   │   │
│   │ (10s poll) │  │ Engine (313) │  │ Integration Layer  │   │
│   └─────┬──────┘  └──────────────┘  └─────────┬──────────┘   │
└─────────┼──────────────────────────────────────┼─────────────┘
          │                                      │
   ┌──────▼───────┐                ┌─────────────▼──────────────┐
   │ TfL Unified  │                │  D365 F&O OData            │
   │ API (public) │                │  Microsoft Graph (mail)    │
   └──────────────┘                └────────────────────────────┘
```

The pipeline breaks down into five phases:

1. Real-time vehicle telemetry from the **TfL Unified API**
2. **Server-side interpolation** to turn 0.1 Hz polling into 60 fps motion
3. An in-memory **maintenance engine** simulating the D365 F&O asset master
4. A **single-page operational UI** (Leaflet + vanilla JS)
5. **One-click work order creation** in D365 F&O with a Graph-powered email

Let's walk through each.

---

## Phase 1: Real-Time Vehicle Telemetry (TfL Unified API)

This is the digital heartbeat of the system. The [TfL Unified API](https://api.tfl.gov.uk/) is free, public, and returns the predicted arrival of every vehicle at every station every few seconds — effectively a positional feed for the entire network.

A background thread in the Flask server polls the `Arrivals` endpoint for each line on a **10-second cycle**. We deduplicate by vehicle ID, keeping only the nearest predicted stop. The result is a snapshot of "where every train is *heading next*" — not where it is right now.

```python
TFL_API_BASE = "https://api.tfl.gov.uk"
REFRESH_S    = 10

def fetch_live_trains():
    for line_id in LINE_IDS:
        url = f"{TFL_API_BASE}/Line/{line_id}/Arrivals"
        data = http_requests.get(url, params={"app_key": TFL_APP_KEY}).json()
        for arrival in data:
            vid = arrival["vehicleId"]
            if vid not in trains or arrival["timeToStation"] < trains[vid]["tts"]:
                trains[vid] = build_train_record(arrival)
```

This is the equivalent of an Azure IoT Hub or telematics ingestion layer in a production system — except TfL has done the hard work for us.

---

## Phase 2: Server-Side Interpolation (the "60fps trick")

A 10-second poll produces a jerky map. So between TfL refreshes, the server **interpolates** each train's position along its line geometry using:

- The previous station's coordinates
- The next station's coordinates
- The elapsed time since the last TfL update
- A nominal inter-station travel time (~120s)

```python
def interpolate_position(train, now):
    elapsed = now - train["last_update"]
    progress = min(elapsed / INTERSTATION_S, 1.0)
    return lerp(train["from_coord"], train["to_coord"], progress)
```

Direction is preserved by inspecting station ordering on each line, and the line itself is laid out using a **nearest-neighbour chaining algorithm** — eliminating the zig-zag artefacts that plague naive line plotting.

The frontend polls `/api/trains` once a second and the browser renders smooth movement at 60 fps. This is the same client-side prediction pattern used in multiplayer gaming and GPS navigation: **smooth UX built on infrequent ground truth**.

---

## Phase 3: The Maintenance Engine (Simulating D365 F&O Asset Master)

For each of the 313 vehicles, we generate a **deterministic maintenance profile** — seeded by vehicle ID, so the same train always returns the same record. This stands in for what a live D365 F&O integration would expose: enterprise asset records enriched with IoT telemetry, condition scores, and open work orders.

```python
def asset_record(vid):
    rng = random.Random(int(hashlib.md5(vid.encode()).hexdigest(), 16))
    return {
        "asset_id"        : f"TUBE-{vid}",
        "condition_score" : rng.randint(45, 99),
        "brake_status"    : rng.choice(["OK", "Wear", "Critical"]),
        "hvac_temp_c"     : round(rng.uniform(18, 31), 1),
        "engine_hours"    : rng.randint(800, 4200),
        "open_wo_count"   : rng.choices([0,1,2,3], weights=[7,2,1,1])[0],
        "last_service"    : (datetime.utcnow() - timedelta(days=rng.randint(0,180))).date().isoformat()
    }
```

In a production deployment, this function would be a single OData call to D365 F&O's `EntAssetObjectTable` entity — exactly the same shape Marco demonstrated in the [Fabric + D365 F&O Digital Twin article](https://medium.com/@lonardomark/real-time-asset-tracking-digital-twin-with-microsoft-fabric-and-d365-f-o-5349ab96a5d5).

The clustering logic is intentionally similar to the KQL clustering used in the Fabric pattern: condition thresholds, hours-to-service warnings, and a composite health flag — except here the logic runs in Python rather than Kusto, suiting an edge-style deployment that doesn't require a Fabric capacity.

---

## Phase 4: The Operational UI (Leaflet + vanilla JS)

The frontend is a single HTML file with three panels:

- A **live map** rendered with [Leaflet.js](https://leafletjs.com/), with one marker per train and one marker per station
- An **arrivals board** that mirrors the platform-style displays inside Tube stations (click any station to open it)
- An **asset inspector** that opens when you click a train, showing condition score, component status, service history, and open work orders

All of this is served from nine REST endpoints exposed by the Flask backend:

```python
@app.route("/api/trains")           # live train positions
@app.route("/api/stations")         # station catalogue
@app.route("/api/tracks")           # line geometry
@app.route("/api/arrivals/<id>")    # platform-style board
@app.route("/api/maintenance/<vid>")# asset record for one train
@app.route("/api/fleet-health")     # KPIs across the fleet
@app.route("/api/line-status")      # disruptions / service status
@app.route("/api/work-order", methods=["POST"])  # create WO + send email
```

No build step. No framework. The page loads in well under a second.

---

## Phase 5: One-Click Work Orders (D365 F&O + Microsoft Graph)

This is where the "see → act" loop closes.

When the operator clicks **"Create Work Order"** in the asset inspector, the frontend POSTs the asset payload to `/api/work-order`. The server then does two things in sequence:

1. **Builds a structured work order record** matching the shape D365 F&O expects on its `EntAssetWorkOrderTable` entity (asset ID, fault description, priority, requested completion date, requesting worker)
2. **Sends a formatted HTML notification** to the maintenance team via the **Microsoft Graph `sendMail` API**, using a service principal token from the same Azure AD tenant that hosts D365 F&O

```python
@app.route("/api/work-order", methods=["POST"])
def create_work_order():
    payload = request.json
    wo = build_d365_workorder(payload)              # OData-ready record
    persist_local(wo)                               # always saved
    if GRAPH_ENABLED:
        send_graph_email(wo, GRAPH_SENDER_EMAIL)    # best-effort email
    return jsonify({"status": "created", "wo_id": wo["id"]})
```

Authentication uses **OAuth client-credentials** against `login.microsoftonline.com` with the `D365_URL/.default` scope for D365 and `https://graph.microsoft.com/.default` for Graph. Secrets stay in a local `.env` (`python-dotenv`) — trivially swappable for Azure Key Vault in production.

The result: a fault observed on the map at 09:31:04 becomes an open work order in D365 at 09:31:09, with the maintenance lead's inbox pinging at 09:31:11.

---

## Hands-on set up

The whole thing runs locally with three commands.

**1. Register a free TfL API key** at the [TfL API Portal](https://api.tfl.gov.uk/) (optional — the system works without it, just rate-limited).

**2. Create an Azure AD App Registration** with:
- API permission: `Dynamics ERP > Connector.FullAccess` (application)
- API permission: `Microsoft Graph > Mail.Send` (application)
- Grant admin consent

**3. Drop a `.env` next to the server**:

```bash
TFL_APP_KEY=<your tfl key>

TENANT_ID=<your aad tenant>
CLIENT_ID=<your app reg client id>
CLIENT_SECRET=<your app reg secret>
D365_URL=https://<env>.operations.dynamics.com

GRAPH_TENANT_ID=<same tenant>
GRAPH_CLIENT_ID=<app reg client id>
GRAPH_CLIENT_SECRET=<app reg secret>
GRAPH_SENDER_EMAIL=maintenance@yourtenant.onmicrosoft.com
```

**4. Install and run**:

```bash
pip install flask requests python-dotenv
python live_tube_server.py
```

Open `http://localhost:5050` and the live map renders within ten seconds.

---

## Conclusion

In this article, we have demonstrated how a free public API, a single Python file, and a thin browser frontend can be combined into a working **digital twin** of a real-world transport network — and wired straight into Dynamics 365 Finance & Operations as an actionable enterprise asset surface.

The architecture is intentionally minimalist. It runs without Fabric, without Kafka, without Kubernetes — *and that's the point*. It demonstrates the **pattern**: collapse the distance between telemetry, decision, and ERP action until it fits inside a single click.

**Future Enhancements & Next Steps**

- **Microsoft Fabric Real-Time Intelligence**: route the TfL stream into an EventStream → Eventhouse, replacing the in-memory Python state with a queryable KQL database (the architecture used in the [Fabric + D365 F&O](https://medium.com/@lonardomark/real-time-asset-tracking-digital-twin-with-microsoft-fabric-and-d365-f-o-5349ab96a5d5) and [Sydney Ferries](https://medium.com/@francescogiorgio.fava/real-time-ferry-tracking-in-sydney-harbour-with-microsoft-fabric-07bb2784ca50) articles)
- **Fabric Activator**: trigger automated reflexes (Teams alerts, work-order creation) on threshold breaches
- **Predictive Maintenance ML**: layer an ML model on the condition-score stream to anticipate failures before they trigger thresholds
- **Power BI Executive View**: a composite-mode report blending real-time fleet health with historical maintenance cost trends
- **Conversational Agent**: a Copilot Studio agent on top of the Fabric stream answering natural-language questions like *"which trains are due for service in the next 48 hours?"*

If your operations team is still toggling between five tabs to answer one question, the gap is not a technology gap. It's a design gap — and it's smaller than you think.

The full source is on GitHub: [github.com/marcolonardo325/TfL-LiveTubeMap](https://github.com/marcolonardo325/TfL-LiveTubeMap).

Please let me know your thoughts in the comments!

---

*Marco Lonardo — Solution Engineer @ Microsoft. Data, AI and Agentic ERP. Italian in London. Sports, Nature & Coffee.*
