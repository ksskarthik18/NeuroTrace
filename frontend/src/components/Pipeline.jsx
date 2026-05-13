const STEPS = [
  { key: "execution", label: "Execute" },
  { key: "static_analysis", label: "Analyze" },
  { key: "trace", label: "Trace" },
  { key: "root_cause", label: "Root Cause" },
  { key: "patch", label: "Patch" },
  { key: "validation", label: "Validate" },
];

export default function Pipeline({ result, currentStep, isRunning }) {
  function getStatus(key) {
    if (!isRunning && !result) return "pending";
    if (isRunning) {
      const idx = STEPS.findIndex((s) => s.key === key);
      const curIdx = STEPS.findIndex((s) => s.key === currentStep);
      if (idx < curIdx) return "done";
      if (idx === curIdx) return "running";
      return "pending";
    }
    if (result && result[key]) return "done";
    return "pending";
  }

  return (
    <div className="pipeline">
      {STEPS.map((step) => {
        const status = getStatus(step.key);
        return (
          <div key={step.key} className={`pipeline-step ${status}`}>
            {status === "done" && "✓"}
            {status === "running" && <span className="spinner" />}
            {status === "pending" && "○"}
            {step.label}
          </div>
        );
      })}
    </div>
  );
}
