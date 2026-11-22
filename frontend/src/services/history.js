// Remembers recently completed models in this browser so they can be reopened.
const KEY = "polygen.history.v1";
const MAX_ITEMS = 8;

export function loadHistory() {
  try {
    const raw = localStorage.getItem(KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveHistory(items) {
  try {
    localStorage.setItem(KEY, JSON.stringify(items));
  } catch {
    /* storage unavailable or full: history just won't persist */
  }
}

// Newest first, no duplicates, capped at MAX_ITEMS.
export function addToHistory(items, entry) {
  return [entry, ...items.filter((item) => item.jobId !== entry.jobId)].slice(0, MAX_ITEMS);
}
