export async function runWorkflow(task) {
  const response = await fetch("/api/workflow/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ task }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error.detail?.[0]?.msg ||
      error.detail ||
      `Workflow request failed (${response.status})`
    );
  }

  return response.json();
}