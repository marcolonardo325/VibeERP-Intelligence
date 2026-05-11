# 🚇 Deploying the Live Tube Map to Azure Container Apps

This guide gets the live, interactive map running on a public Azure URL with auto-deploy from GitHub. Total time: ~15 minutes. Cost: free tier eligible (~$0–5/mo with scale-to-zero).

---

## Prerequisites

- Azure subscription
- GitHub repo (this one)
- Azure CLI installed locally — [download](https://learn.microsoft.com/cli/azure/install-azure-cli)

---

## Step 1 — One-time Azure setup (run locally)

Open PowerShell in the repo root and run:

```powershell
# --- Variables (edit these) ---
$RG       = "vibeconf-rg"
$LOCATION = "westeurope"
$ACR      = "marcotubeacr$([Random]::new().Next(1000,9999))"  # must be globally unique
$ENV      = "tube-env"
$APP      = "tube-map"

# --- Login ---
az login
az account set --subscription "<your-subscription-id-or-name>"

# --- Resource group ---
az group create -n $RG -l $LOCATION

# --- Azure Container Registry (Basic SKU, ~$5/mo) ---
az acr create -n $ACR -g $RG --sku Basic --admin-enabled true

# --- Container Apps environment (free) ---
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App
az containerapp env create -n $ENV -g $RG -l $LOCATION

# --- Build the image once locally and push (so the app exists) ---
az acr build --registry $ACR --image live-tube-map:v1 .

# --- Create the Container App (1 vCPU / 2GB, scale 0–2) ---
az containerapp create `
  --name $APP `
  --resource-group $RG `
  --environment $ENV `
  --image "$ACR.azurecr.io/live-tube-map:v1" `
  --registry-server "$ACR.azurecr.io" `
  --target-port 8000 `
  --ingress external `
  --min-replicas 0 `
  --max-replicas 2 `
  --cpu 1.0 --memory 2.0Gi `
  --query properties.configuration.ingress.fqdn -o tsv
```

The last command prints your public URL, e.g.:
```
tube-map.kindrock-1a2b3c4d.westeurope.azurecontainerapps.io
```

Open `https://<that-url>` and your live tube map is on the internet. 🎉

---

## Step 2 — Set env vars on the Container App (optional)

If you want the **D365 work-order** and **Graph email** features to work in the cloud:

```powershell
az containerapp update -n $APP -g $RG --set-env-vars `
  TFL_APP_KEY=secretref:tfl-key `
  TENANT_ID=<your-tenant> `
  CLIENT_ID=<your-client-id> `
  CLIENT_SECRET=secretref:client-secret `
  D365_URL=https://<env>.operations.dynamics.com `
  GRAPH_TENANT_ID=<your-tenant> `
  GRAPH_CLIENT_ID=<graph-client-id> `
  GRAPH_CLIENT_SECRET=secretref:graph-secret `
  GRAPH_SENDER_EMAIL=<sender@tenant.onmicrosoft.com>

# Add the actual secrets
az containerapp secret set -n $APP -g $RG --secrets `
  tfl-key=<tfl-api-key> `
  client-secret=<d365-client-secret> `
  graph-secret=<graph-client-secret>
```

(Skip this if you just want the read-only live map.)

---

## Step 3 — Wire up GitHub auto-deploy

Every `git push` to `main` will rebuild and redeploy.

### 3a. Create a service principal for GitHub

```powershell
$SUBSCRIPTION = az account show --query id -o tsv
az ad sp create-for-rbac --name "github-tube-deploy" `
  --role contributor `
  --scopes "/subscriptions/$SUBSCRIPTION/resourceGroups/$RG" `
  --json-auth
```

Copy the entire JSON output.

### 3b. Add GitHub secrets

Go to **GitHub → your repo → Settings → Secrets and variables → Actions → New repository secret** and add:

| Name | Value |
|---|---|
| `AZURE_CREDENTIALS` | the full JSON from step 3a |
| `ACR_NAME` | your ACR name (e.g. `marcotubeacr1234`) |
| `AZURE_RG` | `vibeconf-rg` |
| `CONTAINER_APP_NAME` | `tube-map` |

Also grant the SP push rights on the registry:

```powershell
$SP_ID = az ad sp list --display-name "github-tube-deploy" --query "[0].id" -o tsv
$ACR_ID = az acr show -n $ACR --query id -o tsv
az role assignment create --assignee $SP_ID --role AcrPush --scope $ACR_ID
```

### 3c. Push and watch it deploy

```powershell
git add Dockerfile .dockerignore requirements.txt live_tube_server.py .github/
git commit -m "Add Azure Container Apps deployment"
git push
```

Go to **GitHub → Actions** and watch the workflow build & deploy. Done in ~3 min.

---

## Updating the app

Just edit code and `git push`. The workflow rebuilds the image and rolls out a new revision automatically.

---

## Cost notes

- **Container Apps**: scale-to-zero means **$0 when idle** (cold start ~5s on first request). Active usage on 1 vCPU/2GB ≈ $0.000024/vCPU-second. A demo URL with light traffic costs $1–5/month.
- **ACR Basic**: ~$5/month flat.
- **Total realistic**: **~$5–10/month** for a public always-on demo.

To shut it down: `az group delete -n vibeconf-rg --yes` removes everything.

---

## Linking from the article

Once live, add this near the top of `Medium_Article_TfL_DigitalTwin_D365.md`:

```markdown
> 🚇 **[Try the live map →](https://tube-map.kindrock-1a2b3c4d.westeurope.azurecontainerapps.io)**
```

And in your GitHub `README.md`:

```markdown
[![Live demo](https://img.shields.io/badge/🚇_Live_Demo-Open-1a8917?style=for-the-badge)](https://tube-map.<your-fqdn>.azurecontainerapps.io)
```
