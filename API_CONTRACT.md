# PolyGen — Shared API & Module Interface Contract

> **Project:** PolyGen (Generative Text-to-3D Asset Pipeline)[cite: 1, 10]  
> **Assignment Ref:** ITS/GAI/1279  
> **Owner:** Member 3 (Backend, Integration & Delivery)  
> **Status:** Draft v1.0 (Initial Agreement)

---

## 1. Team-Wide Rules & Architecture

1. **One Agreed Architecture:** The browser (Member 1) communicates *only* with the Backend (Member 3). The Backend coordinates with the 3D Generation Module (Member 2). Private AI provider API keys or credentials must **never** be exposed in the frontend bundle or repository.
2. **One Source of Truth:** This document governs all field names, routes, status values, and error formats. Do not invent field names or change contracts silently[cite: 3, 5]. Any modification requires team agreement and updating this file before merging[cite: 3, 5].
3. **One Real Output:** The 3D viewer must render the actual asset produced by the pipeline[cite: 3]. Static placeholder models must not be substituted to mask a failed generation[cite: 3].

---

## 2. Standardized Job Status Values

All modules (Frontend, Backend, Generator) must use **exact** lowercase string matching for job states[cite: 3]:

| Status | Meaning |
| :--- | :--- |
| `queued` | Request validated and unique job ID assigned; waiting to start generation[cite: 1, 3, 5]. |
| `processing` | Generation module is actively building the 3D mesh and textures[cite: 1, 3, 10]. |
| `completed` | Valid 3D asset file exists, metadata/size verified, and asset is ready for preview[cite: 1, 3, 5]. |
| `failed` | Input validation, generation, or asset verification failed[cite: 1, 3, 5]. |

*(Do not use variations such as `done`, `success`, `error`, or `generating`[cite: 3].)*

---

## 3. Asset Format & Packaging Agreement

* **Primary Asset Format:** `.glb` (Binary glTF) — single self-contained file bundling geometry, UV maps, and PBR textures for direct browser WebGL rendering and game engine export[cite: 4, 10].
* **Delivery Mechanism:** Server-hosted static/storage URL served via Backend (with documented expiry if temporary links are used).

---

## 4. Frontend $\leftrightarrow$ Backend HTTP Endpoints (Member 1 & Member 3)

**Base Path:** `/api/v1`

### 4.1 Submit Text-to-3D Generation Job
Creates a new asynchronous generation job[cite: 1, 5].

* **Endpoint:** `POST /api/v1/jobs`
* **Content-Type:** `application/json`

**Request Body:**
```json
{
  "prompt": "A rusted, medieval broadsword with a glowing blue sapphire in the hilt",
  "options": {
    "target_polycount": 10000,
    "texture_resolution": 1024
  }
}