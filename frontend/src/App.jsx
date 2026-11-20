import { useEffect, useState } from "react";
import { api, isMockMode } from "./services/api.js";
import PromptPanel from "./components/PromptPanel.jsx";
import StatusPanel from "./components/StatusPanel.jsx";
import Viewer from "./components/Viewer.jsx";

const POLL_MS = 2000;
const TERMINAL = new Set(["completed", "failed"]);

export default function App() {
  const [job, setJob] = useState(null); // { jobId, status, assetUrl?, error?, metadata? }
  const [sentPrompt, setSentPrompt] = useState("");
  const [startedAt, setStartedAt] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  async function handleSubmit(prompt) {
    setSubmitting(true);
    setSubmitError("");
    setJob(null);
    try {
      const created = await api.createJob(prompt);
      setSentPrompt(prompt);
      setStartedAt(Date.now());
      setJob(created);
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  // Poll the job until it reaches a final state.
  useEffect(() => {
    if (!job || TERMINAL.has(job.status)) return;
    const id = setInterval(async () => {
      try {
        const next = await api.getJob(job.jobId);
        setJob(next);
      } catch (err) {
        setJob({ jobId: job.jobId, status: "failed", error: err.message });
      }
    }, POLL_MS);
    return () => clearInterval(id);
  }, [job?.jobId, job?.status]);

  const busy = submitting || (job && !TERMINAL.has(job.status));
  const assetUrl = job?.status === "completed" ? job.assetUrl : null;

  return (
    <div className="app">
      <header className="topbar">
        <h1>PolyGen</h1>
        <span className="tagline">Describe an object, get a 3D model</span>
        {isMockMode && (
          <span className="badge badge-mock" title="Results come from a fixed sample model, not an AI">
            Mock data
          </span>
        )}
      </header>

      <main className="workspace">
        <aside className="controls">
          <PromptPanel onSubmit={handleSubmit} busy={busy} submitError={submitError} />
          <StatusPanel job={job} prompt={sentPrompt} startedAt={startedAt} />
        </aside>

        <section className="stage" aria-label="3D preview">
          <Viewer assetUrl={assetUrl} />
        </section>
      </main>
    </div>
  );
}
