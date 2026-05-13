export default function ConfidenceRing({ value }) {
  const pct = Math.round((value || 0) * 100);
  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value || 0) * circumference;

  let color = "#ef4444";
  if (pct >= 80) color = "#22c55e";
  else if (pct >= 50) color = "#f59e0b";

  return (
    <div className="confidence-container">
      <div className="confidence-ring">
        <svg width="72" height="72" viewBox="0 0 72 72">
          <circle className="ring-bg" cx="36" cy="36" r={radius} />
          <circle
            className="ring-fill"
            cx="36"
            cy="36"
            r={radius}
            stroke={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <span className="confidence-value" style={{ color }}>{pct}%</span>
      </div>
      <div>
        <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>Confidence</div>
        <div className="confidence-label">
          {pct >= 80 ? "High confidence" : pct >= 50 ? "Moderate" : "Low confidence"}
        </div>
      </div>
    </div>
  );
}
