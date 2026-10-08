import { useState } from "react";
import { runWorkflow } from "./services/workflowService";
import "./App.css";

function App() {
  const [task, setTask] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleRunWorkflow() {
    if (!task.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await runWorkflow(task.trim());
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-container">
      <header>
        <h1>Multi-Agent Task Assistant</h1>
        <p>AI-Assisted Task Planning and Workflow Management</p>
      </header>

      <main>
        <section className="task-section">
          <h2>Run Multi-Agent Workflow</h2>

          <p>
            Enter a task to process using the Planner,
            Worker and Reviewer agents.
          </p>

          <textarea
            value={task}
            onChange={(event) => setTask(event.target.value)}
            placeholder="Example: Prepare a weekly study plan"
            rows={4}
            maxLength={500}
          />

          <button
            disabled={loading || !task.trim()}
            onClick={handleRunWorkflow}
          >
            {loading ? "Processing..." : "Run Workflow"}
          </button>

          {error && (
            <p role="alert" style={{ color: "#dc2626" }}>
              {error}
            </p>
          )}
        </section>

        {result && (
          <section className="result-section">
            <h2>Workflow Results</h2>

            <p><strong>Workflow ID:</strong> {result.workflow_id}</p>
            <p><strong>Steps:</strong> {result.steps}</p>
            <p><strong>Status:</strong> {result.result?.content?.status}</p>
            <p><strong>Final Output:</strong> {result.result?.content?.final_output || result.result?.content?.reason || "No final output"}</p>

            <h3>Agent Message History</h3>

            {result.message_history?.map((message, index) => (
              <div className="agent-card" key={index} style={{ marginBottom: 12 }}>
                <strong>
                  {message.sender} → {message.receiver}
                </strong>
                <p>Intent: {message.intent}</p>
                <pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
                  {JSON.stringify(message.content, null, 2)}
                </pre>
              </div>
            ))}
          </section>
        )}

        <section className="agents-section">
          <h2>Multi-Agent Architecture</h2>

          <div className="agents">
            <div className="agent-card">
              <h3>Planner Agent</h3>
              <p>Analyses the task and prepares subtasks.</p>
            </div>

            <div className="agent-card">
              <h3>Worker Agent</h3>
              <p>Processes subtasks and prepares results.</p>
            </div>

            <div className="agent-card">
              <h3>Reviewer Agent</h3>
              <p>Reviews the output and provides feedback.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;