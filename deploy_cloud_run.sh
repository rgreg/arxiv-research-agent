#!/usr/bin/env bash
set -euo pipefail

# === CONFIG ===
REGION="${GCP_REGION:-us-central1}"
REPO="arxiv-agent"
SERVICE="arxiv-agent"
SA="arxiv-agent-sa"
PROJECT="${GCP_PROJECT:?Must set GCP_PROJECT env var before running}"
BQ_TABLE="${BQ_TABLE:?Must set BQ_TABLE env var before running}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.5-flash-lite}"

# === Move to repo root no matter where script is called from ===
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || echo "$SCRIPT_DIR")"
cd "$REPO_ROOT"

echo "Repo root: $REPO_ROOT"
echo "PWD: $(pwd)"
test -f src/agent_api/Dockerfile || { echo "Missing src/agent_api/Dockerfile in $(pwd)"; exit 1; }

# === Enable required services ===
echo "Enabling required services..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  aiplatform.googleapis.com bigquery.googleapis.com \
  secretmanager.googleapis.com logging.googleapis.com \
  --project "$PROJECT"

# === Create Artifact Registry repo if missing ===
echo "Ensuring Artifact Registry repo [$REPO] exists..."
gcloud artifacts repositories create "$REPO" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Images for Arxiv Research Agent" \
  --project "$PROJECT" || true

# === Service Account setup ===
SA_EMAIL="$SA@$PROJECT.iam.gserviceaccount.com"
echo "Ensuring Service Account [$SA_EMAIL] exists..."
gcloud iam service-accounts create "$SA" \
  --display-name="Arxiv Agent API SA" \
  --project "$PROJECT" || true

echo "Binding roles to SA..."
for role in roles/bigquery.dataViewer roles/aiplatform.user \
            roles/storage.objectViewer roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$role" \
    --quiet
done

# === Configure Docker to push to Artifact Registry ===
echo "Configuring Docker auth for Artifact Registry..."
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

# === Build and push image ===
TAG=$(date +%Y%m%d-%H%M%S)
IMAGE="$REGION-docker.pkg.dev/$PROJECT/$REPO/agent-api:$TAG"

echo "Building and pushing image [$IMAGE]..."
docker build \
  --file "src/agent_api/Dockerfile" \
  --tag "$IMAGE" \
  "$REPO_ROOT"

docker push "$IMAGE"

# === Deploy to Cloud Run ===
echo "Deploying service [$SERVICE]..."
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --service-account "$SA_EMAIL" \
  --cpu=1 --memory=1Gi \
  --min-instances=0 --max-instances=2 \
  --port=8000 \
  --set-env-vars GCP_PROJECT="$PROJECT",GCP_REGION="$REGION",BQ_TABLE="$BQ_TABLE",GEMINI_MODEL="$GEMINI_MODEL" \
  --project "$PROJECT"

URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --format="value(status.url)" --project "$PROJECT")
echo "Deployment complete."
echo "Service URL: $URL"
echo
echo "Test with:"
echo "curl -s \"$URL/v1/chat\" -H \"Content-Type: application/json\" -d '{\"question\":\"test question\",\"k\":3}' | jq"
