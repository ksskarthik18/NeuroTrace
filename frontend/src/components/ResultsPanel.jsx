import ConfidenceRing from "./ConfidenceRing";
import DiffViewer from "./DiffViewer";

export default function ResultsPanel({ result }) {
  if (!result) {
    return (
      <div className="empty-state">
        <svg viewBox="0 0 64 64" fill="none">
          <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="2" />
          <path d="M24 24L40 40M40 24L24 40" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
        <h3>No debug results yet</h3>
        <p>Paste your buggy Python code in the editor and click Debug to start the analysis pipeline.</p>
      </div>
    );
  }

  const { execution, static_analysis, trace, root_cause, patch, validation } = result;

  return (
    <div>
      {/* Execution Result */}
      {execution && (
        <div className="card">
          <div className="card-title">
            <span className="icon">{execution.return_code === 0 ? "✓" : "✗"}</span>
            Execution Result
            <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
              {execution.execution_time_ms}ms
            </span>
          </div>
          <div className="exec-output">
            <div className="exec-output-block">
              <div className="exec-output-label">stdout</div>
              <div className="exec-output-text">{execution.stdout || "(empty)"}</div>
            </div>
            <div className="exec-output-block">
              <div className="exec-output-label">stderr</div>
              <div className="exec-output-text" style={{ color: execution.stderr ? "var(--red)" : "inherit" }}>
                {execution.stderr || "(empty)"}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Static Analysis */}
      {static_analysis && (
        <div className="card">
          <div className="card-title">
            <span className="icon">🔍</span>
            Static Analysis
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px", marginBottom: "12px" }}>
            {[
              ["Lines", static_analysis.metrics?.num_lines],
              ["Functions", static_analysis.metrics?.num_functions],
              ["Classes", static_analysis.metrics?.num_classes],
              ["Imports", static_analysis.metrics?.num_imports],
            ].map(([label, val]) => (
              <div key={label} style={{ textAlign: "center", padding: "8px", background: "var(--bg-input)", borderRadius: "var(--radius-sm)" }}>
                <div style={{ fontSize: "1.2rem", fontWeight: 700 }}>{val ?? 0}</div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{label}</div>
              </div>
            ))}
          </div>
          {[...static_analysis.ast_issues, ...static_analysis.pylint_issues, ...static_analysis.mypy_issues].length > 0 && (
            <div style={{ fontSize: "0.8rem" }}>
              {[...static_analysis.ast_issues, ...static_analysis.pylint_issues, ...static_analysis.mypy_issues].map((issue, i) => (
                <div key={i} style={{ padding: "6px 0", borderBottom: "1px solid var(--border)", display: "flex", gap: "8px", alignItems: "center" }}>
                  <span style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)", minWidth: "40px" }}>L{issue.line}</span>
                  <span className={`severity-badge ${issue.severity}`}>{issue.source}</span>
                  <span style={{ color: "var(--text-secondary)" }}>{issue.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Runtime Trace */}
      {trace && trace.exception && (
        <div className="card">
          <div className="card-title">
            <span className="icon">⚡</span>
            Runtime Trace
          </div>
          <div style={{ marginBottom: "10px" }}>
            <span style={{ fontWeight: 600, color: "var(--red)" }}>{trace.exception.type}</span>
            <span style={{ color: "var(--text-secondary)", marginLeft: "8px" }}>{trace.exception.message}</span>
          </div>
          {trace.crash_line && (
            <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "8px" }}>
              Crash at <strong style={{ color: "var(--text-primary)" }}>line {trace.crash_line}</strong>
            </div>
          )}
          {Object.keys(trace.variables_at_crash || {}).length > 0 && (
            <div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "6px" }}>Variables at crash</div>
              <div className="code-block">
                {Object.entries(trace.variables_at_crash).map(([k, v]) => `${k} = ${v}`).join("\n")}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Root Cause Analysis */}
      {root_cause && root_cause.root_cause && (
        <div className="card">
          <div className="card-title">
            <span className="icon">🧠</span>
            Root Cause Analysis
            {root_cause.severity && (
              <span className={`severity-badge ${root_cause.severity}`} style={{ marginLeft: "auto" }}>
                {root_cause.severity}
              </span>
            )}
          </div>
          <div style={{ marginBottom: "8px" }}>
            <span style={{ fontWeight: 600 }}>{root_cause.bug_type}</span>
            {root_cause.faulty_line && (
              <span style={{ color: "var(--text-muted)", marginLeft: "8px" }}>at line {root_cause.faulty_line}</span>
            )}
          </div>

          {root_cause.reasoning_steps?.length > 0 && (
            <ul className="reasoning-steps">
              {root_cause.reasoning_steps.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Patch */}
      {patch && patch.diff && (
        <div className="card">
          <div className="card-title">
            <span className="icon">🔧</span>
            Generated Patch
          </div>
          <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "12px" }}>
            {patch.explanation}
          </div>
          <DiffViewer diff={patch.diff} />
        </div>
      )}

      {/* Validation */}
      {validation && (
        <div className="card">
          <div className="card-title">
            <span className="icon">✓</span>
            Validation Result
            <span className={`status-badge ${validation.status}`} style={{ marginLeft: "auto" }}>
              {validation.status}
            </span>
          </div>
          <ConfidenceRing value={validation.confidence} />
          <div style={{ marginTop: "12px", fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Resolved in {validation.attempts} attempt{validation.attempts !== 1 ? "s" : ""}
          </div>
          {validation.repair_history?.length > 0 && (
            <div className="repair-history">
              {validation.repair_history.map((r) => (
                <div key={r.attempt} className="repair-attempt">
                  <span className="attempt-num">#{r.attempt}</span>
                  <span className={`status-badge ${r.status}`}>{r.status}</span>
                  {r.error && <span className="attempt-error">{r.error}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Patched Code */}
      {validation?.patched_code && validation.status === "validated" && patch?.diff && (
        <div className="card">
          <div className="card-title">
            <span className="icon">✨</span>
            Fixed Code
          </div>
          <div className="code-block">{validation.patched_code}</div>
        </div>
      )}
    </div>
  );
}
