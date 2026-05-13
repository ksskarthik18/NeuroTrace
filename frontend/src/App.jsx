import { useState } from "react";
import Header from "./components/Header";
import Pipeline from "./components/Pipeline";
import ResultsPanel from "./components/ResultsPanel";
import { debugCode } from "./api";

const SAMPLE_CODE = `def divide_list_elements(numbers, divisor):
    results = []
    for i in range(len(numbers)):
        results.append(numbers[i] / divisor)
    return results

print(divide_list_elements([10, 20, 30], 0))`;

export default function App() {
  const [code, setCode] = useState(SAMPLE_CODE);
  const [testCode, setTestCode] = useState("");
  const [result, setResult] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState("");
  const [error, setError] = useState(null);

  async function handleDebug() {
    if (!code.trim()) return;
    setIsRunning(true);
    setResult(null);
    setError(null);

    const steps = ["execution", "static_analysis", "trace", "root_cause", "patch", "validation"];
    let stepIdx = 0;
    const interval = setInterval(() => {
      if (stepIdx < steps.length) {
        setCurrentStep(steps[stepIdx]);
        stepIdx++;
      }
    }, 800);

    try {
      const res = await debugCode(code, testCode || null);
      clearInterval(interval);
      setResult(res);
      setCurrentStep("");
    } catch (e) {
      clearInterval(interval);
      setError(e.message);
      setCurrentStep("");
    } finally {
      setIsRunning(false);
    }
  }

  function handleClear() {
    setCode("");
    setTestCode("");
    setResult(null);
    setError(null);
  }

  return (
    <>
      <Header />
      <div className="main-layout">
        <div className="panel panel-left">
          <div className="editor-section">
            <div className="editor-header">
              <h2>Source Code</h2>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Python</span>
            </div>
            <textarea
              id="code-editor"
              className="code-textarea"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Paste your buggy Python code here..."
              spellCheck={false}
            />
            <div className="editor-header" style={{ marginTop: "16px" }}>
              <h2>Test Code (Optional)</h2>
            </div>
            <textarea
              id="test-editor"
              className="code-textarea test-textarea"
              value={testCode}
              onChange={(e) => setTestCode(e.target.value)}
              placeholder="assert add(1, 2) == 3"
              spellCheck={false}
            />
            <div className="btn-group">
              <button
                id="debug-btn"
                className="btn btn-primary"
                onClick={handleDebug}
                disabled={isRunning || !code.trim()}
              >
                {isRunning ? (
                  <>
                    <span className="spinner" />
                    Debugging...
                  </>
                ) : (
                  "Debug Code"
                )}
              </button>
              <button id="clear-btn" className="btn btn-secondary" onClick={handleClear}>
                Clear
              </button>
            </div>
            {error && (
              <div style={{ marginTop: "12px", padding: "12px", background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: "var(--radius-sm)", color: "var(--red)", fontSize: "0.85rem" }}>
                {error}
              </div>
            )}
          </div>
        </div>

        <div className="panel">
          <Pipeline result={result} currentStep={currentStep} isRunning={isRunning} />
          <ResultsPanel result={result} />
        </div>
      </div>
    </>
  );
}
