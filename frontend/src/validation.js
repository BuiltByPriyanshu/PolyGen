export const MIN_PROMPT = 3;
export const MAX_PROMPT = 500;

// Returns an error message string, or "" when the prompt is valid.
export function validatePrompt(raw) {
  const prompt = raw.trim();
  if (!prompt) return "Describe the object you want to generate.";
  if (prompt.length < MIN_PROMPT) return "Add a few more words so the model knows what to build.";
  if (prompt.length > MAX_PROMPT) return `Keep the description under ${MAX_PROMPT} characters.`;
  return "";
}
