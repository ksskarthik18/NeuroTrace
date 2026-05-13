const API_BASE = "http://localhost:8000/api/v1";

export async function debugCode(sourceCode, testCode = null) {
  const response = await fetch(`${API_BASE}/debug`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      source_code: sourceCode,
      test_code: testCode || null,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error: ${response.status} - ${error}`);
  }

  return response.json();
}

export async function executeCode(sourceCode) {
  const response = await fetch(`${API_BASE}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_code: sourceCode }),
  });
  if (!response.ok) throw new Error(`API Error: ${response.status}`);
  return response.json();
}

export async function analyzeCode(sourceCode) {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_code: sourceCode }),
  });
  if (!response.ok) throw new Error(`API Error: ${response.status}`);
  return response.json();
}

export async function healthCheck() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error("Backend unreachable");
  return response.json();
}
