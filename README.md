# PolyGen frontend

React + Vite + react-three-fiber UI for the PolyGen text-to-3D pipeline. Owner: Member 1.

## Run

```bash
cd frontend
npm install
cp .env.example .env.local   # Windows: copy .env.example .env.local
npm run dev
```

Open http://localhost:5173.

By default the app runs in **mock mode** (`VITE_USE_MOCK=true`): the status flow is simulated and a fixed
sample `.glb` is shown. Mock results are not AI-generated, and the UI says so with a "Mock data" badge.
Type a prompt containing the word `fail` to test the failed state.

To use the real backend, set `VITE_USE_MOCK=false`. Requests to `/api/*` are proxied to
`http://localhost:8000` (see `vite.config.js`).

## Structure

```
frontend/
  src/
    App.jsx                    job state and polling
    main.jsx
    styles.css
    services/
      api.js                   all backend calls (mock + real, /api/v1)
      validation.js            prompt rules
    components/
      PromptPanel.jsx          prompt input, examples, validation
      StatusPanel.jsx          queued / processing / done / failed
      Viewer.jsx               .glb viewer (orbit, zoom, reset, download)
      ViewerErrorBoundary.jsx
```

The API contract lives at the repo root: `API_CONTRACT.md`.
