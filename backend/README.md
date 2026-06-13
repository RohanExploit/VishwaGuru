# VishwaGuru Backend

This is the FastAPI backend for the VishwaGuru application.

## Prerequisites

*   Python 3.12+
*   Google Cloud SDK (gcloud CLI)
*   Firebase CLI (optional, for integrated deployment)

## Local Development

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Locally:**
    ```bash
    PYTHONPATH=. python -m uvicorn main:app --reload
    ```
    The API will be available at `http://localhost:8000`.

## Deployment to Firebase (Google Cloud Run)

To make the backend deployable "on Firebase", we use Google Cloud Run, which is the serverless container platform that integrates with Firebase Hosting.

### Steps

1.  **Install Google Cloud SDK:**
    Follow instructions at [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install).

2.  **Authenticate:**
    ```bash
    gcloud auth login
    gcloud config set project YOUR_PROJECT_ID
    ```

3.  **Build and Deploy:**
    **Crucial:** Run the following command from the **root** of the repository (not inside `backend/`), because the Dockerfile needs access to the `data/` directory.

    ```bash
    gcloud run deploy vishwaguru-backend \
      --source . \
      --platform managed \
      --region us-central1 \
      --allow-unauthenticated
    ```

    When prompted, if it asks to confirm the `Dockerfile` path, ensure it uses `backend/Dockerfile`.

    *Note: If `gcloud` tries to use a default Python builder instead of the Dockerfile, use this command to specify it explicitly (requires building the image first or using Cloud Build):*

    **Alternative (Explicit Build):**
    ```bash
    gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/vishwaguru-backend --file backend/Dockerfile .
    gcloud run deploy vishwaguru-backend --image gcr.io/YOUR_PROJECT_ID/vishwaguru-backend --platform managed --region us-central1
    ```

4.  **Get the Service URL:**
    Once deployed, note the service URL (e.g., `https://vishwaguru-backend-xyz.a.run.app`).

5.  **Connect to Firebase Hosting:**
    Update the root `firebase.json` "rewrites" section to point to this Cloud Run service ID:

    ```json
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "vishwaguru-backend",
          "region": "us-central1"
        }
      }
    ]
    ```

## Environment Variables

Ensure you set the required environment variables in Cloud Run:
*   `GEMINI_API_KEY`
*   `OPENROUTER_API_KEY`
*   `DATABASE_URL` (if using PostgreSQL)
*   `TELEGRAM_BOT_TOKEN`

You can set these via the Google Cloud Console or CLI:
```bash
gcloud run services update vishwaguru-backend --set-env-vars GEMINI_API_KEY=...,DATABASE_URL=...
```
