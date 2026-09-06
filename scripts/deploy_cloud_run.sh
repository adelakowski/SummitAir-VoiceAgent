#!/usr/bin/env bash

# Deploy Summit Air Voice Agent webhooks to Google Cloud Run.

# Fill placeholders; do not hardcode secrets.

set -euo pipefail



PROJECT_ID="${GCP_PROJECT_ID:-YOUR_GCP_PROJECT}"

REGION="${GCP_REGION:-us-central1}"

SERVICE="${CLOUD_RUN_SERVICE:-summit-air-voice-agent}"

IMAGE="${CLOUD_RUN_IMAGE:-gcr.io/${PROJECT_ID}/${SERVICE}}"



# Retell must reach these webhooks. Unauthenticated is simplest for a prototype;

# prefer IAM + Retell IP allowlisting / signed requests for production.

ALLOW_UNAUTHENTICATED="${ALLOW_UNAUTHENTICATED:-true}"



echo "Building ${IMAGE} ..."

gcloud builds submit --project="${PROJECT_ID}" --tag "${IMAGE}" .



AUTH_FLAG="--no-allow-unauthenticated"

if [[ "${ALLOW_UNAUTHENTICATED}" == "true" ]]; then

  AUTH_FLAG="--allow-unauthenticated"

fi



echo "Deploying to Cloud Run (${REGION}) ..."

gcloud run deploy "${SERVICE}" \

  --project="${PROJECT_ID}" \

  --image="${IMAGE}" \

  --region="${REGION}" \

  --platform=managed \

  --port=8080 \

  ${AUTH_FLAG} \

  --set-env-vars="APP_ENV=production,LOG_LEVEL=INFO,WEBHOOK_BASE_URL=${WEBHOOK_BASE_URL:-},SCHEDULE_DB_PATH=/tmp/schedule.db"



echo "Done. Set WEBHOOK_BASE_URL to the service URL and update Retell tool URLs."


