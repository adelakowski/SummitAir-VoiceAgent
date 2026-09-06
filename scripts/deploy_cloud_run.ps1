# Deploy Summit Air Voice Agent webhooks to Google Cloud Run.
# Fill placeholders; do not hardcode secrets.

param(
    [string]$ProjectId = $(if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "YOUR_GCP_PROJECT" }),
    [string]$Region = $(if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }),
    [string]$Service = $(if ($env:CLOUD_RUN_SERVICE) { $env:CLOUD_RUN_SERVICE } else { "summit-air-voice-agent" }),
    [string]$AllowUnauthenticated = $(if ($env:ALLOW_UNAUTHENTICATED) { $env:ALLOW_UNAUTHENTICATED } else { "true" })
)

$Image = if ($env:CLOUD_RUN_IMAGE) { $env:CLOUD_RUN_IMAGE } else { "gcr.io/$ProjectId/$Service" }

Write-Host "Building $Image ..."
gcloud builds submit --project=$ProjectId --tag $Image .

# Retell must reach these webhooks. Unauthenticated is simplest for a prototype;
# prefer IAM + signed requests for production.
$deployArgs = @(
    "run", "deploy", $Service,
    "--project=$ProjectId",
    "--image=$Image",
    "--region=$Region",
    "--platform=managed",
    "--port=8080",
    "--set-env-vars=APP_ENV=production,LOG_LEVEL=INFO,WEBHOOK_BASE_URL=$($env:WEBHOOK_BASE_URL)"
)

if ($AllowUnauthenticated -eq "true") {
    $deployArgs += "--allow-unauthenticated"
} else {
    $deployArgs += "--no-allow-unauthenticated"
}

Write-Host "Deploying to Cloud Run ($Region) ..."
& gcloud @deployArgs

Write-Host "Done. Set WEBHOOK_BASE_URL to the service URL and update Retell tool URLs."
