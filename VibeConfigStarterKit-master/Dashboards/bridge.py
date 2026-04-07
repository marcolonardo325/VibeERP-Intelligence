import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

TENANT_ID = "2aef5e13-b940-4c1d-bca5-f36d9427170a"
CLIENT_ID = "2dbf663a-7e0e-4af9-850c-81c759cfcb6d"
CLIENT_SECRET = "REDACTED_SECRET"
# Assicurati che non ci sia la slash finale qui
D365_URL = "https://usenvironment1.operations.dynamics.com"

def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    # MODIFICA QUI: Per Dynamics 365, lo scope deve terminare con /.default
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': f"{D365_URL}/.default" 
    }
    
    try:
        r = requests.post(url, data=data)
        if r.status_code != 200:
            print(f"❌ Errore Azure AD: {r.text}") # Questo ti dirà l'errore esatto (es. Secret sbagliato)
            return None
        return r.json().get('access_token')
    except Exception as e:
        print(f"❌ Eccezione durante richiesta token: {e}")
        return None

# --- QUESTA DEVE ESSERE L'UNICA FUNZIONE PER /api/data ---
@app.route('/api/data', methods=['GET'])
def get_dashboard_data():
    token = get_access_token()
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    try:
        # Recupero Vendor
        r_v = requests.get(f"{D365_URL}/data/VendorsV2?$top=12", headers=headers)
        if r_v.status_code == 200:
            vendors = r_v.json().get('value', [])
            # IMPORTANTE: Mappiamo i campi per farli digerire all'HTML
            formatted_vendors = []
            for v in vendors:
                formatted_vendors.append({
                    "id": v.get("VendorAccountNumber"), # Mappa su 'id'
                    "name": v.get("VendorName"),        # Mappa su 'name'
                    "country": v.get("VendorRegionId", "US"),
                    "spend": 1500000 + (len(formatted_vendors) * 10000) # Demo spend
                })
            return jsonify({"vendors": formatted_vendors})
    except Exception as e:
        print(f"Errore: {e}")
    return jsonify({"vendors": []})

if __name__ == '__main__':
    app.run(port=5000, debug=True)