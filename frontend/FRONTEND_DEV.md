# Frontend Development Guide

## Local Development

### Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Create `.env.local` file:
```bash
# For local backend
VITE_API_URL=http://localhost:8000

# OR for deployed backend
VITE_API_URL=https://your-backend.onrender.com
```

3. Start development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`.

## Environment Variables

The frontend uses Vite environment variables (prefixed with `VITE_`):

- **`VITE_API_URL`**: Backend API URL (no trailing slash)
  - Local dev: `http://localhost:8000`
  - Production: Your Render backend URL

If `VITE_API_URL` is not set, the app will use relative URLs (for monolithic deployment).

## Building for Production

```bash
npm run build
```

This creates a `dist/` folder with optimized production files.

## Deployment to Netlify

See [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) for full instructions.

**Quick summary:**
1. Push code to GitHub
2. Connect GitHub repo to Netlify
3. Set base directory: `frontend`
4. Set build command: `npm run build`
5. Set publish directory: `frontend/dist`
6. Add environment variable: `VITE_API_URL=https://your-backend.onrender.com`

## API Endpoints Used

The frontend calls these backend endpoints:

- `GET /api/responsibility-map` - Fetch responsibility map data
- `POST /api/issues` - Submit new issue with description, category, and optional image

## Troubleshooting

### CORS Errors

If you see CORS errors in the browser console:

1. **Local Development**: Make sure backend `FRONTEND_URL` includes `http://localhost:5173`
2. **Production**: Ensure backend `FRONTEND_URL` matches your Netlify URL exactly

### API Calls Failing

1. Check that `VITE_API_URL` is set correctly
2. Verify backend is running and accessible
3. Open DevTools → Network tab to inspect requests
4. Check for typos (no trailing slash in URL)

### Build Failures

1. Delete `node_modules` and `package-lock.json`, then `npm install`
2. Check Node.js version (requires 18+)
3. Clear Vite cache: `rm -rf node_modules/.vite`
