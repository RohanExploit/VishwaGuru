# VishwaGuru

VishwaGuru is an open source platform empowering India's youth to engage with democracy. It uses AI to simplify contacting representatives, filing grievances, and organizing community action. Built for India's languages and governance, it turns selfies and videos into real civic impact.

## Features

- **AI-Powered Action Plans**: Generates WhatsApp messages and email drafts for civic issues using Google's Gemini API.
- **Issue Reporting**: Users can report issues via a web interface or a Telegram bot.
- **Local & Production Ready**: Supports SQLite for local development and PostgreSQL for production.
- **Modern Stack**: Built with React (Vite) and FastAPI.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+**
- **Node.js 18+** and **npm**
- **Git**

## Installation & Deployment Guides

This project is structured to be easily deployable on **Firebase** (Google Cloud) or other platforms like Render/Netlify.

For specific installation and deployment instructions, please verify the `README.md` in each folder:

*   **[Frontend Documentation](./frontend/README.md)**: Instructions for installing dependencies, running locally, and deploying to **Firebase Hosting**.
*   **[Backend Documentation](./backend/README.md)**: Instructions for setting up the API, running with Docker, and deploying to **Google Cloud Run** (Firebase Backend).
*   **[Data Documentation](./data/README.md)**: Details about the static data files used by the application.

## Quick Start (Local)

### 1. Clone the Repository

```bash
git clone <repository_url>
cd vishwaguru
```

### 2. Backend Setup

1.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
2.  Install dependencies:
    ```bash
    pip install -r backend/requirements.txt
    ```
3.  Run the server:
    ```bash
    python -m uvicorn backend.main:app --reload
    ```

### 3. Frontend Setup

1.  Navigate to frontend:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the dev server:
    ```bash
    npm run dev
    ```

## Deployment (Firebase)

The project includes a `firebase.json` for easy deployment to the Firebase ecosystem.

1.  **Frontend**: Deployed to Firebase Hosting.
2.  **Backend**: Deployed to Google Cloud Run, with Firebase Hosting configured to rewrite `/api` requests to the backend service.

See the [Frontend README](./frontend/README.md) and [Backend README](./backend/README.md) for detailed steps.

## Contributing

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/YourFeature`).
3.  Commit your changes (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/YourFeature`).
5.  Open a Pull Request.

## License

This project is licensed under the **AGPL-3.0** License.
