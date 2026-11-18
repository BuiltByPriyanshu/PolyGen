import { useEffect, useState } from "react";

const LABELS = {
  queued: "Queued",
  processing: "Processing",
  completed: "Done",
  failed: "Failed",
};

const HINTS = {
  queued: "Your request is waiting for the generator.",
  processing: "The model is being generated. This can take a minute or more.",
  completed: "Your model is ready in the preview.",
};

function formatElapsed(ms) {
  const s = Math.floor(ms / 1000);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export default function StatusPanel({ job, prompt, startedAt }) {
  const [now, setNow] = useState(Date.now());
  const running = job && (job.status === "queued" || job.status === "processing");

  // Show real elapsed time instead of a made-up progress bar.
  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(id);
  }, [running]);

  if (!job) {
    return (
      <div className="panel">
        <h2 className="panel-title">Status</h2>
        <p className="muted">Nothing running yet. Submit a description to start.</p>
      </div>
    );
  }

  return (
    <div className="panel" aria-live="polite">
      <h2 className="panel-title">Status</h2>
      <div className="status-row">
        <span className={`badge badge-${job.status}`}>{LABELS[job.status] ?? job.status}</span>
        {running && startedAt && <span className="elapsed">{formatElapsed(now - startedAt)}</span>}
      </div>

      {job.status === "failed" ? (
        <p className="error">{job.error || "Generation failed. Try rewording the description."}</p>
      ) : (
        <p className="muted">{HINTS[job.status]}</p>
      )}

      <dl className="meta">
        <dt>Prompt sent</dt>
        <dd>{prompt}</dd>
        <dt>Job ID</dt>
        <dd className="mono">{job.jobId}</dd>
        {job.metadata?.format && (
          <>
            <dt>Format</dt>
            <dd>{job.metadata.format}</dd>
          </>
        )}
      </dl>
    </div>
  );
}
