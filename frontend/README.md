# VishwaGuru Frontend

This is the React frontend for the VishwaGuru application, built with Vite and Tailwind CSS.

## Prerequisites

*   Node.js 18+
*   npm or pnpm
*   Firebase CLI (`npm install -g firebase-tools`)

## Local Development

1.  **Install Dependencies:**
    ```bash
    npm install
    ```

2.  **Run Locally:**
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

## Deployment to Firebase Hosting

This application is configured to be deployed to Firebase Hosting.

### Steps

1.  **Login to Firebase:**
    ```bash
    firebase login
    ```

2.  **Initialize (if not already done):**
    From the root of the repository (parent folder), run:
    ```bash
    firebase init hosting
    ```
    *   **Public directory:** `frontend/dist`
    *   **Configure as a single-page app (rewrite all urls to /index.html)?** Yes
    *   **Set up automatic builds and deploys with GitHub?** Optional

3.  **Build the Project:**
    Inside the `frontend` directory:
    ```bash
    npm run build
    ```
    This generates the static assets in `dist/`.

4.  **Deploy:**
    From the root of the repository:
    ```bash
    firebase deploy --only hosting
    ```

### Configuration

The Firebase configuration is located in `firebase.json` at the root of the repository. It handles:
*   Serving static files from `frontend/dist`.
*   Rewriting `/api` requests to the Backend Cloud Run service.
