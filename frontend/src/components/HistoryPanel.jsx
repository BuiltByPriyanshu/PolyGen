function formatTime(ms) {
  return new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function HistoryPanel({ items, activeId, onSelect, onClear }) {
  if (items.length === 0) return null;

  return (
    <div className="panel">
      <div className="history-head">
        <h2 className="panel-title">Recent models</h2>
        <button type="button" className="link-button" onClick={onClear}>
          Clear
        </button>
      </div>

      <ul className="history-list">
        {items.map((item) => (
          <li key={item.jobId}>
            <button
              type="button"
              className={`history-item${item.jobId === activeId ? " is-active" : ""}`}
              onClick={() => onSelect(item)}
              aria-current={item.jobId === activeId ? "true" : undefined}
            >
              <span className="history-prompt">{item.prompt}</span>
              <span className="history-time">
                {formatTime(item.completedAt)}
                {item.mock ? " · mock" : ""}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
