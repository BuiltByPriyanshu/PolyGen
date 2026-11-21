# PolyGen API contract (draft for team agreement)

Base path: `/api/v1`. All bodies are JSON. Agreed asset format: **`.glb`**.

## Create a job
`POST /api/v1/jobs`

Request:
```json
{ "prompt": "A low-poly red sports car with black wheels" }
```

Response `201`:
```json
{ "jobId": "abc123", "status": "queued" }
```

Errors (`400` invalid prompt, `500` server error):
```json
{ "error": "Prompt must be between 3 and 500 characters." }
```

## Get job status
`GET /api/v1/jobs/{jobId}`

| status       | extra fields                                             |
|--------------|----------------------------------------------------------|
| `queued`     | none                                                     |
| `processing` | none                                                     |
| `completed`  | `assetUrl` (URL of the .glb), `metadata` (optional)      |
| `failed`     | `error` (human-readable message)                         |

Example, completed:
```json
{
  "jobId": "abc123",
  "status": "completed",
  "assetUrl": "/api/v1/assets/abc123.glb",
  "metadata": { "format": "glb", "generationSeconds": 48 }
}
```

## Rules
- Status values must reflect real backend state. No simulated progress.
- `assetUrl` must be fetchable by the browser (same origin or CORS enabled) and return `model/gltf-binary`.
- A stub generator may be used during development but must be labelled as a stub and never reported as AI output.
- Prompt limits: 3 to 500 characters (enforced on both frontend and backend).
