// All backend communication lives here. Components never call fetch directly.
// Contract: see API_CONTRACT.md at the repo root.
// Job statuses: "queued" | "processing" | "completed" | "failed"

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";
const API_BASE = "/api/v1";
const MOCK_ASSET_URL =
  import.meta.env.VITE_MOCK_ASSET_URL ||
  "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Duck/glTF-Binary/Duck.glb";

export const isMockMode = USE_MOCK;

// ---------------------------------------------------------------- real API
// Accept camelCase or snake_case so the UI works with whichever the backend returns.
function normalizeJob(data) {
  return {
    jobId: data.jobId ?? data.job_id,
    status: data.status,
    assetUrl: data.assetUrl ?? data.asset_url ?? null,
    error: data.error ?? null,
    metadata: data.metadata ?? null,
  };
}

async function request(path, options) {
  let res;
  try {
    res = await fetch(path, options);
  } catch {
    throw new Error("Could not reach the PolyGen server. Check that the backend is running.");
  }
  if (!res.ok) {
    let detail = "";
    try {
      const body = await res.json();
      detail = body.error || body.detail || "";
    } catch {
      /* response had no JSON body */
    }
    throw new Error(typeof detail === "string" && detail ? detail : `The server returned an error (${res.status}).`);
  }
  return normalizeJob(await res.json());
}

const realApi = {
  createJob: (prompt) =>
    request(`${API_BASE}/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    }),
  getJob: (jobId) => request(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`),
};

// ---------------------------------------------------------------- mock API
// MOCK ONLY: simulates job states and always returns a fixed sample model.
// Nothing returned here is AI-generated. Include "fail" in a prompt to test the failed state.
const mockJobs = new Map();

const mockApi = {
  async createJob(prompt) {
    await new Promise((r) => setTimeout(r, 300));
    const jobId = `mock-${Date.now()}`;
    mockJobs.set(jobId, { prompt, createdAt: Date.now() });
    return { jobId, status: "queued" };
  },
  async getJob(jobId) {
    await new Promise((r) => setTimeout(r, 150));
    const job = mockJobs.get(jobId);
    if (!job) throw new Error("Job not found.");
    const elapsed = Date.now() - job.createdAt;

    if (elapsed < 2000) return { jobId, status: "queued" };
    if (elapsed < 6000) return { jobId, status: "processing" };
    if (job.prompt.toLowerCase().includes("fail")) {
      return { jobId, status: "failed", error: "Mock failure: the generator did not return a model." };
    }
    return {
      jobId,
      status: "completed",
      assetUrl: MOCK_ASSET_URL,
      metadata: { format: "glb", mock: true },
    };
  },
};

export const api = USE_MOCK ? mockApi : realApi;
