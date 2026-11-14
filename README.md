# PolyGen frontend

React + Vite + react-three-fiber UI for the PolyGen text-to-3D pipeline.

## Run

```bash
npm install
cp .env.example .env.local   # Windows: copy .env.example .env.local
npm run dev
```

Open http://localhost:5173.

By default the app runs in **mock mode** (`VITE_USE_MOCK=true`): the status flow is simulated and a fixed
sample `.glb` is shown. Mock results are not AI-generated and the UI says so with a "Mock data" badge.
Type a prompt containing the word `fail` to test the failed state.

To use the real backend, set `VITE_USE_MOCK=false`. Requests to `/api/*` are proxied to `http://localhost:8000`.

If the default sample URL does not load, put any `.glb` at `public/models/sample.glb` and set
`VITE_MOCK_ASSET_URL=/models/sample.glb`.

## Structure

```
src/
  api.js                  all backend calls (mock + real)
  validation.js           prompt rules
  App.jsx                 job state and polling
  components/
    PromptPanel.jsx       prompt input, examples, validation
    StatusPanel.jsx       queued / processing / done / failed
    Viewer.jsx            .glb viewer (orbit, zoom, reset, download)
    ViewerErrorBoundary.jsx
docs/api-contract.md      request/response contract to agree with the team
```
