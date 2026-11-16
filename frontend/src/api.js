// All backend communication lives here. Components never call fetch directly.
// Job statuses: "queued" | "processing" | "completed" | "failed"

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";
const MOCK_ASSET_URL =
  import.meta.env.VITE_MOCK_ASSET_URL ||
  "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Duck/glTF-Binary/Duck.glb";

export const isMockMode = USE_MOCK;

// ---------------------------------------------------------------- real API
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
    throw new Error(detail || `The server returned an error (${res.status}).`);
  }
  return res.json();
}

const realApi = {
  createJob: (prompt) =>
    request("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    }),
  getJob: (jobId) => request(`/api/jobs/${encodeURIComponent(jobId)}`),
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
