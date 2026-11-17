import { useState } from "react";
import { validatePrompt, MAX_PROMPT } from "../services/validation.js";

const EXAMPLES = [
  "A low-poly red sports car with black wheels",
  "A rusted medieval broadsword with a blue sapphire in the hilt",
  "A wooden chair with a woven seat",
  "A stylized pine tree for a mobile game",
];

export default function PromptPanel({ onSubmit, busy, submitError }) {
  const [text, setText] = useState("");
  const [error, setError] = useState("");

  function submit(e) {
    e.preventDefault();
    const problem = validatePrompt(text);
    setError(problem);
    if (!problem) onSubmit(text.trim());
  }

  function pickExample(example) {
    setText(example);
    setError("");
  }

  return (
    <form className="panel" onSubmit={submit} noValidate>
      <label htmlFor="prompt" className="panel-title">
        What should we make?
      </label>
      <textarea
        id="prompt"
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          if (error) setError("");
        }}
        rows={5}
        maxLength={MAX_PROMPT + 100}
        placeholder="Describe the object, its shape, colour and style."
        aria-invalid={Boolean(error)}
        aria-describedby={error ? "prompt-error" : undefined}
        disabled={busy}
      />
      <div className="field-meta">
        {error ? (
          <p id="prompt-error" className="error" role="alert">
            {error}
          </p>
        ) : (
          <span />
        )}
        <span className="count">
          {text.trim().length}/{MAX_PROMPT}
        </span>
      </div>

      <div className="examples" role="group" aria-label="Example prompts">
        {EXAMPLES.map((ex) => (
          <button key={ex} type="button" className="chip" onClick={() => pickExample(ex)} disabled={busy}>
            {ex}
          </button>
        ))}
      </div>

      {submitError && (
        <p className="error" role="alert">
          {submitError}
        </p>
      )}

      <button type="submit" className="primary" disabled={busy}>
        {busy ? "Generating…" : "Generate model"}
      </button>
    </form>
  );
}
