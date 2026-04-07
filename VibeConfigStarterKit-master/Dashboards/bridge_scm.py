"""
D365 F&O — C-Suite SCM & Procurement Bridge
Flask API that proxies OData calls to Dynamics 365 Finance & Operations.
Handles OAuth2 authentication, field mapping, and write-back operations.

Usage:
    pip install flask flask-cors requests
    python bridge_scm.py

The dashboard HTML connects to http://localhost:5000
"""

import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ─── D365 F&O Connection ─────────────────────────────────────────────────────
# In production, use environment variables instead of hardcoded secrets.
TENANT_ID     = "2aef5e13-b940-4c1d-bca5-f36d9427170a"
CLIENT_ID     = "2dbf663a-7e0e-4af9-850c-81c759cfcb6d"
CLIENT_SECRET = "REDACTED_SECRET"
D365_URL      = "https://usenvironment1.operations.dynamics.com"

# ─── Token Cache ──────────────────────────────────────────────────────────────
_token_cache = {"token": None, "expires_at": 0}


def get_token():
    """Acquire or return cached Azure AD bearer token."""
    if _token_cache["token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         f"{D365_URL}/.default",
    }
    r = requests.post(url, data=data, timeout=15)
    if r.status_code != 200:
        raise Exception(f"Azure AD token error {r.status_code}: {r.text}")

    body = r.json()
    _token_cache["token"] = body["access_token"]
    _token_cache["expires_at"] = time.time() + body.get("expires_in", 3600)
    return _token_cache["token"]


# ─── D365 OData Helpers ──────────────────────────────────────────────────────

def d365_headers():
    return {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }


def d365_get(entity, params=None, timeout=30):
    """GET from D365 OData. Returns list of records or raises."""
    url = f"{D365_URL}/data/{entity}"
    # D365 stores dataAreaId in lowercase — normalize filters
    final_params = {"cross-company": "true"}
    for k, v in (params or {}).items():
        if k == "$filter" and "dataAreaId" in v:
            import re
            v = re.sub(r"dataAreaId eq '([^']+)'", lambda m: f"dataAreaId eq '{m.group(1).lower()}'", v)
        final_params[k] = v
    r = requests.get(url, headers=d365_headers(), params=final_params, timeout=timeout)
    if r.status_code != 200:
        raise Exception(f"D365 GET {entity} → {r.status_code}: {r.text[:300]}")
    return r.json().get("value", [])


def d365_post(entity, payload, timeout=30):
    """POST to D365 OData. Returns created record."""
    url = f"{D365_URL}/data/{entity}"
    # Normalize dataAreaId to lowercase
    if "dataAreaId" in payload:
        payload["dataAreaId"] = payload["dataAreaId"].lower()
    r = requests.post(url, headers=d365_headers(), json=payload, timeout=timeout)
    if r.status_code not in (200, 201):
        raise Exception(f"D365 POST {entity} → {r.status_code}: {r.text[:300]}")
    return r.json()


# ═════════════════════════════════════════════════════════════════════════════
#  HEALTH CHECK
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/health", methods=["GET"])
def health():
    """Verify Azure AD auth and D365 connectivity."""
    try:
        token = get_token()
        # Quick probe — fetch 1 legal entity record
        r = requests.get(
            f"{D365_URL}/data/LegalEntities?$top=1",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=10,
        )
        d365_ok = r.status_code == 200
        if not d365_ok:
            print(f"⚠️  D365 probe returned {r.status_code}: {r.text[:200]}")
        else:
            print(f"✅ D365 connected — {r.json().get('value', [])}")
        return jsonify({
            "status": "ok",
            "d365": d365_ok,
            "d365_status": r.status_code,
            "url": D365_URL,
        })
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  VENDORS
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/vendors", methods=["GET"])
def get_vendors():
    entity = request.args.get("entity", "USMF")
    top = request.args.get("top", "50")
    try:
        rows = d365_get("VendorsV2", {
            "$filter": f"dataAreaId eq '{entity}'",
            "$top": top,
            "$orderby": "VendorAccountNumber",
        })
        data = []
        for v in rows:
            data.append({
                "id":      v.get("VendorAccountNumber", ""),
                "name":    v.get("VendorOrganizationName", ""),
                "group":   v.get("VendorGroupId", ""),
                "country": v.get("AddressCountryRegionId", ""),
            })
        return jsonify({"data": data, "count": len(data), "source": "d365"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  RELEASED PRODUCTS
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/products", methods=["GET"])
def get_products():
    entity = request.args.get("entity", "USMF")
    top = request.args.get("top", "100")
    try:
        rows = d365_get("ReleasedProductsV2", {
            "$filter": f"dataAreaId eq '{entity}'",
            "$top": top,
            "$orderby": "ItemNumber",
        })
        data = []
        for p in rows:
            data.append({
                "itemId":    p.get("ItemNumber", ""),
                "name":      p.get("ProductName") or p.get("SearchName") or p.get("ItemNumber", ""),
                "category":  p.get("ProductGroupId") or p.get("ItemModelGroupId") or "General",
            })
        return jsonify({"data": data, "count": len(data), "source": "d365"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  PURCHASE ORDER HEADERS
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/purchase-orders", methods=["GET"])
def get_purchase_orders():
    entity = request.args.get("entity", "USMF")
    top = request.args.get("top", "50")
    try:
        rows = d365_get("PurchaseOrderHeadersV2", {
            "$filter": f"dataAreaId eq '{entity}'",
            "$top": top,
            "$orderby": "PurchaseOrderNumber desc",
        })
        data = []
        for po in rows:
            data.append({
                "poNumber":  po.get("PurchaseOrderNumber", ""),
                "vendor":    po.get("OrderVendorAccountNumber", ""),
                "vendorId":  po.get("OrderVendorAccountNumber", ""),
                "status":    po.get("PurchaseOrderStatus", ""),
                "currency":  po.get("CurrencyCode", "USD"),
            })
        return jsonify({"data": data, "count": len(data), "source": "d365"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  PURCHASE ORDER LINES  (recent POs with amounts)
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/po-lines", methods=["GET"])
def get_po_lines():
    entity = request.args.get("entity", "USMF")
    top = request.args.get("top", "30")
    try:
        rows = d365_get("PurchaseOrderLinesV2", {
            "$filter": f"dataAreaId eq '{entity}'",
            "$top": top,
            "$orderby": "PurchaseOrderNumber desc",
        })
        data = []
        for ln in rows:
            data.append({
                "po":       ln.get("PurchaseOrderNumber", ""),
                "itemId":   ln.get("ItemNumber", ""),
                "item":     ln.get("ItemNumber", ""),
                "vendor":   "",
                "price":    ln.get("PurchasePrice", 0),
                "qty":      ln.get("OrderedPurchaseQuantity", 0),
                "amount":   ln.get("LineAmount", 0),
            })
        return jsonify({"data": data, "count": len(data), "source": "d365"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  VENDOR SPEND AGGREGATION  (groups PO lines by vendor)
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/vendor-spend", methods=["GET"])
def get_vendor_spend():
    entity = request.args.get("entity", "USMF")
    try:
        # PO lines don't carry vendor — build PO→vendor map from headers
        po_rows = d365_get("PurchaseOrderHeadersV2", {
            "$filter": f"dataAreaId eq '{entity}'",
            "$top": "5000",
        })
        po_vendor = {p.get("PurchaseOrderNumber", ""): p.get("OrderVendorAccountNumber", "") for p in po_rows}

        rows = d365_get("PurchaseOrderLinesV2", {
            "$filter": f"dataAreaId eq '{entity}'",
            "$top": "1000",
        })
        spend_map = {}
        for ln in rows:
            vid = po_vendor.get(ln.get("PurchaseOrderNumber", ""), "")
            spend_map[vid] = spend_map.get(vid, 0) + (ln.get("LineAmount") or 0)

        # Remove empty-vendor bucket
        spend_map.pop("", None)

        # Fetch vendor names
        vendor_names = {}
        if spend_map:
            v_rows = d365_get("VendorsV2", {
                "$filter": f"dataAreaId eq '{entity}'",
                "$top": "200",
            })
            for v in v_rows:
                vendor_names[v["VendorAccountNumber"]] = v.get("VendorOrganizationName", v["VendorAccountNumber"])

        sorted_vendors = sorted(spend_map.items(), key=lambda x: x[1], reverse=True)
        total = sum(s for _, s in sorted_vendors) or 1
        cum = 0
        data = []
        for vid, spend in sorted_vendors:
            cum += spend
            data.append({
                "id":     vid,
                "name":   vendor_names.get(vid, vid),
                "spend":  round(spend, 2),
                "cumPct": round(cum / total * 100, 1),
            })
        return jsonify({"data": data, "count": len(data), "source": "d365"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  CATEGORY SPEND AGGREGATION
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/category-spend", methods=["GET"])
def get_category_spend():
    entity = request.args.get("entity", "USMF")
    try:
        rows = d365_get("PurchaseOrderLinesV2", {
            "$filter": f"dataAreaId eq '{entity}'",
            "$top": "1000",
        })
        cat_map = {}
        for ln in rows:
            cat = ln.get("ProcurementProductCategoryName") or "Uncategorized"
            cat_map[cat] = cat_map.get(cat, 0) + (ln.get("LineAmount") or 0)
        data = sorted(
            [{"category": k, "spend": round(v, 2)} for k, v in cat_map.items()],
            key=lambda x: x["spend"], reverse=True,
        )
        return jsonify({"data": data, "count": len(data), "source": "d365"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  INVENTORY ON-HAND
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    entity = request.args.get("entity", "USMF")
    top = request.args.get("top", "200")
    site = request.args.get("site", "")
    warehouse = request.args.get("warehouse", "")
    try:
        odata_filter = f"dataAreaId eq '{entity}'"
        if site:
            odata_filter += f" and InventorySiteId eq '{site}'"

        rows = d365_get("InventorySitesOnHand", {
            "$filter": odata_filter,
            "$top": top,
        })
        data = []
        for i in rows:
            oh   = i.get("OnHandQuantity", 0) or 0
            res  = i.get("ReservedOnHandQuantity", 0) or 0
            avl  = i.get("AvailableOnHandQuantity", oh - res) or 0
            data.append({
                "itemId":     i.get("ItemNumber", ""),
                "name":       i.get("ProductName") or i.get("ItemNumber", ""),
                "site":       i.get("InventorySiteId", ""),
                "warehouse":  "",
                "onHand":     oh,
                "reserved":   res,
                "available":  avl,
                "value":      0,
                "isLowStock": avl < 100,
            })
        return jsonify({"data": data, "count": len(data), "source": "d365"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  WAREHOUSE LOCATIONS
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/warehouses", methods=["GET"])
def get_warehouses():
    entity = request.args.get("entity", "USMF")
    try:
        rows = d365_get("Warehouses", {
            "$filter": f"dataAreaId eq '{entity}'",
            "$top": "50",
        })
        data = [
            {
                "id":   w.get("WarehouseId", ""),
                "name": w.get("WarehouseName") or w.get("WarehouseId", ""),
                "site": w.get("OperationalSiteId", ""),
            }
            for w in rows
        ]
        return jsonify({"data": data, "count": len(data), "source": "d365"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  TRADE AGREEMENTS  (PriceDiscAdmTrans)
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/trade-agreements", methods=["GET"])
def get_trade_agreements():
    entity = request.args.get("entity", "USMF")
    try:
        rows = d365_get("TradeAgreementJournalHeaders", {
            "$filter": f"dataAreaId eq '{entity}'",
            "$top": "100",
        })
        data = []
        for t in rows:
            data.append({
                "journal":   t.get("JournalNumber", ""),
                "relation":  t.get("DefaultTradeAgreementType", ""),
                "account":   t.get("TradeAgreementJournalNameId", ""),
                "item":      "",
                "price":     0,
                "currency":  "",
                "validTo":   (t.get("PostedDate") or "")[:10],
                "description": t.get("JournalDescription", ""),
                "posted":    t.get("Posted", ""),
            })
        return jsonify({"data": data, "count": len(data), "source": "d365"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  PURCHASE AGREEMENTS
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/purchase-agreements", methods=["GET"])
def get_purchase_agreements():
    entity = request.args.get("entity", "USMF")
    try:
        rows = d365_get("PurchaseAgreements", {
            "$filter": f"dataAreaId eq '{entity}'",
            "$top": "50",
        })
        data = []
        for pa in rows:
            data.append({
                "num":       pa.get("PurchaseAgreementId", ""),
                "vendorId":  pa.get("AgreementVendorAccountNumber", ""),
                "vendor":    pa.get("AgreementVendorAccountNumber", ""),
                "cls":       pa.get("PurchaseAgreementClassificationName")
                             or pa.get("DefaultCommitmentType", ""),
                "status":    pa.get("AgreementStatus", ""),
                "expiry":    (pa.get("DefaultExpirationDate") or "")[:10],
                "title":     pa.get("DocumentTitle", ""),
                "currency":  pa.get("CurrencyCode", ""),
            })
        return jsonify({"data": data, "count": len(data), "source": "d365"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  KPI SUMMARY  (aggregated from multiple entities)
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/kpis", methods=["GET"])
def get_kpis():
    entity = request.args.get("entity", "USMF")
    kpis = {}
    try:
        # Open PO count
        po_rows = d365_get("PurchaseOrderHeadersV2", {
            "$filter": f"dataAreaId eq '{entity}'",
            "$top": "5000",
        })
        kpis["openPOs"] = len(po_rows)

        # Total PO spend from lines
        ln_rows = d365_get("PurchaseOrderLinesV2", {
            "$filter": f"dataAreaId eq '{entity}'",
            "$top": "5000",
        })
        kpis["totalSpend"] = round(sum(l.get("LineAmount", 0) or 0 for l in ln_rows), 2)

        # Vendor count
        v_rows = d365_get("VendorsV2", {
            "$filter": f"dataAreaId eq '{entity}'",
            "$top": "5000",
        })
        kpis["activeVendors"] = len(v_rows)

        # Inventory on-hand summary
        try:
            inv_rows = d365_get("InventorySitesOnHand", {
                "$filter": f"dataAreaId eq '{entity}'",
                "$top": "5000",
            })
            total_on_hand = sum(r.get("OnHandQuantity", 0) or 0 for r in inv_rows)
            low_stock = sum(1 for r in inv_rows if (r.get("AvailableOnHandQuantity", 0) or 0) < 100)
            kpis["inventoryItems"] = len(inv_rows)
            kpis["totalOnHand"] = total_on_hand
            kpis["lowStockAlerts"] = low_stock
        except Exception:
            kpis["inventoryItems"] = 0
            kpis["totalOnHand"] = 0
            kpis["lowStockAlerts"] = 0

        return jsonify({"data": kpis, "source": "d365"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  WRITE:  CREATE PURCHASE ORDER
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/create-purchase-order", methods=["POST"])
def create_purchase_order():
    body = request.get_json(force=True)
    entity = body.get("entity", "USMF")
    vendor = body.get("vendorAccount", "")
    item   = body.get("itemNumber", "")
    qty    = body.get("quantity", 1)

    if not vendor:
        return jsonify({"error": "vendorAccount is required"}), 400

    try:
        # 1. Create PO Header
        po_header = d365_post("PurchaseOrderHeadersV2", {
            "dataAreaId": entity,
            "OrderVendorAccountNumber": vendor,
        })
        po_num = po_header.get("PurchaseOrderNumber", "")

        # 2. Add PO Line if item specified
        line_error = None
        if item and po_num:
            try:
                d365_post("PurchaseOrderLinesV2", {
                    "dataAreaId": entity,
                    "PurchaseOrderNumber": po_num,
                    "LineNumber": 1,
                    "ItemNumber": item,
                    "OrderedPurchaseQuantity": qty,
                })
            except Exception as le:
                line_error = str(le)
                print(f"⚠️  PO {po_num} header created but line failed: {line_error}")

        return jsonify({
            "success": True,
            "poNumber": po_num,
            "vendor": vendor,
            "item": item,
            "entity": entity,
            "source": "d365",
            "lineError": line_error,
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  WRITE:  CREATE MOVEMENT JOURNAL
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/create-movement-journal", methods=["POST"])
def create_movement_journal():
    body = request.get_json(force=True)
    entity      = body.get("entity", "USMF")
    item_id     = body.get("itemNumber", "")
    site        = body.get("site", "")
    warehouse   = body.get("warehouse", "")
    qty         = body.get("quantity", 0)
    adj_type    = body.get("adjustmentType", "increase")
    description = body.get("description", "Dashboard stock adjustment")

    if not item_id:
        return jsonify({"error": "itemNumber is required"}), 400

    actual_qty = qty if adj_type == "increase" else -abs(qty)

    try:
        # 1. Create Journal Header
        jh = d365_post("InventoryMovementJournalHeaders", {
            "dataAreaId": entity,
            "JournalNameId": "IMov",
            "Description": description,
        })
        journal_id = jh.get("JournalBatchNumber", "")

        # 2. Add Journal Line
        if journal_id:
            d365_post("InventoryMovementJournalEntriesV4", {
                "dataAreaId": entity,
                "JournalBatchNumber": journal_id,
                "ItemNumber": item_id,
                "InventSiteId": site,
                "InventLocationId": warehouse,
                "Quantity": actual_qty,
            })

        return jsonify({
            "success": True,
            "journalId": journal_id,
            "item": item_id,
            "quantity": actual_qty,
            "entity": entity,
            "source": "d365",
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
#  WRITE:  ESCALATE TO MANAGER  (Power Automate HTTP trigger)
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/escalate", methods=["POST"])
def escalate():
    body = request.get_json(force=True)

    flow_url = body.get("flowUrl", "")
    if not flow_url:
        return jsonify({"error": "flowUrl is required — set your Power Automate HTTP trigger URL"}), 400

    payload = {
        "tradeAgreement": body.get("journal", ""),
        "vendor":         body.get("vendor", ""),
        "price":          body.get("price", ""),
        "currency":       body.get("currency", ""),
        "entity":         body.get("entity", "USMF"),
        "requestedBy":    body.get("requestedBy", "Dashboard User"),
        "approvalType":   "Trade Agreement Review",
    }

    try:
        r = requests.post(flow_url, json=payload, timeout=15)
        return jsonify({
            "success": r.status_code in (200, 202),
            "statusCode": r.status_code,
            "source": "power_automate",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("─" * 60)
    print("  D365 F&O — C-Suite SCM Bridge")
    print(f"  D365 URL : {D365_URL}")
    print(f"  Tenant   : {TENANT_ID}")
    print("  Dashboard: http://localhost:5000")
    print("─" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
