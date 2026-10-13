
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { runWorkflow } from "./services/workflowService";
import "./App.css";

// Convert backend values into displayable text.
function getText(value) {
  if (typeof value === "string") return value;
  if (value === null || value === undefined) return "";
  return JSON.stringify(value, null, 2);
}

// Find the latest matching agent message.
function findMessage(history, sender, intent) {
  return [...history]
    .reverse()
    .find(
      (message) =>
        message.sender === sender &&
        (!intent || message.intent === intent)
    );
}

// Render AI-generated Markdown.
function FormattedOutput({ text }) {
  const content = getText(text);

  if (!content.trim()) {
    return <p className="muted">No output available.</p>;
  }

  return (
    <div className="formatted-output">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  );
}

function App() {
  const [task, setTask] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleRunWorkflow(event) {
    event.preventDefault();

    if (!task.trim() || loading) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await runWorkflow(task.trim());
      setResult(data);
    } catch (err) {
      setError(err.message || "Unable to run workflow.");
    } finally {
      setLoading(false);
    }
  }

  const history = Array.isArray(result?.message_history)
    ? result.message_history
    : [];

  const workflowResult = result?.result;
  const content = workflowResult?.content || {};

  const plannerMessage = findMessage(
    history,
    "planner",
    "execute_subtasks"
  );

  const workerMessage = findMessage(
    history,
    "worker",
    "execution_result"
  );

  const reviewerMessage = findMessage(history, "reviewer");

  const subtasks = Array.isArray(content.subtasks)
    ? content.subtasks
    : Array.isArray(plannerMessage?.content?.subtasks)
      ? plannerMessage.content.subtasks
      : [];

  const workerResults = Array.isArray(content.results)
    ? content.results
    : Array.isArray(workerMessage?.content?.results)
      ? workerMessage.content.results
      : [];

  const status =
    content.status ||
    (workflowResult?.intent === "review_approved"
      ? "approved"
      : "unknown");

  const approved = status === "approved";

  const revisionCount =
    result?.revisions ??
    result?.revision_count ??
    history.filter(
      (message) => message.intent === "revision_required"
    ).length;

  return (
    <div className="app-container">
      <header className="page-header">
        <div className="header-icon">AI</div>

        <h1>Multi-Agent Task Assistant</h1>

        <p>
          AI-Assisted Task Planning and Workflow Management
        </p>
      </header>

      <main>
        <section className="task-section">
          <div className="section-heading">
            <h2>Run Multi-Agent Workflow</h2>

            <p>
              Enter a task for the Planner, Worker and
              Reviewer agents to process.
            </p>
          </div>

          <form onSubmit={handleRunWorkflow}>
            <label
              htmlFor="task-input"
              className="field-label"
            >
              Task description
            </label>

            <textarea
              id="task-input"
              value={task}
              onChange={(event) =>
                setTask(event.target.value)
              }
              placeholder="Example: Prepare a weekly study plan with revision, assignments and breaks."
              rows={5}
              maxLength={500}
              disabled={loading}
            />

            <div className="form-footer">
              <span className="character-count">
                {task.length}/500 characters
              </span>

              <button
                type="submit"
                disabled={loading || !task.trim()}
              >
                {loading
                  ? "Processing workflow..."
                  : "Run Workflow"}
              </button>
            </div>
          </form>

          {loading && (
            <div
              className="loading-message"
              role="status"
            >
              <span
                className="spinner"
                aria-hidden="true"
              />
              AI agents are processing your task.
              This may take a minute.
            </div>
          )}

          {error && (
            <div
              className="error-message"
              role="alert"
            >
              {error}
            </div>
          )}
        </section>

        {result && (
          <section className="result-section">
            <div className="result-header">
              <div>
                <h2>Workflow Results</h2>

                <p className="muted">
                  Workflow ID: {result.workflow_id}
                </p>
              </div>

              <span
                className={`status-badge ${
                  approved ? "success" : "failure"
                }`}
              >
                {status}
              </span>
            </div>

            <div className="summary-grid">
              <div className="summary-card">
                <span>Workflow Steps</span>
                <strong>{result.steps ?? 0}</strong>
              </div>

              <div className="summary-card">
                <span>Revisions</span>
                <strong>{revisionCount}</strong>
              </div>

              <div className="summary-card">
                <span>Messages</span>
                <strong>{history.length}</strong>
              </div>
            </div>

            <div className="result-block">
              <h3>1. Planner Agent</h3>

              <p className="muted">
                Task analysis and generated subtasks
              </p>

              {subtasks.length > 0 ? (
                <ol className="subtask-list">
                  {subtasks.map((subtask, index) => (
                    <li key={index}>
                      {getText(subtask)}
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="muted">
                  No subtasks available.
                </p>
              )}
            </div>

            <div className="result-block">
              <h3>2. Worker Agent</h3>

              <p className="muted">
                AI-generated execution results
              </p>

              {workerResults.length > 0 ? (
                <div className="worker-results">
                  {workerResults.map((item, index) => (
                    <details
                      className="worker-item"
                      key={index}
                      open={index === 0}
                    >
                      <summary>
                        Subtask {index + 1}
                        {subtasks[index]
                          ? `: ${getText(subtasks[index])}`
                          : ""}
                      </summary>

                      <FormattedOutput text={item} />
                    </details>
                  ))}
                </div>
              ) : (
                <p className="muted">
                  No Worker results available.
                </p>
              )}
            </div>

            <div className="result-block">
              <h3>3. Reviewer Agent</h3>

              <div
                className={`review-panel ${
                  approved ? "approved" : "rejected"
                }`}
              >
                <strong>
                  {approved
                    ? "Output Approved"
                    : "Workflow Not Approved"}
                </strong>

                <p>
                  {approved
                    ? "The Reviewer Agent approved the generated output according to its validation rules."
                    : getText(
                        content.reason ||
                        reviewerMessage?.content?.reason ||
                        "The workflow did not complete successfully."
                      )}
                </p>
              </div>
            </div>

            <div className="result-block">
              <h3>4. Final Output</h3>

              <div className="final-output">
                <FormattedOutput
                  text={
                    content.final_output ||
                    content.reason ||
                    "No final output returned."
                  }
                />
              </div>
            </div>

            <div className="result-block">
              <details className="history-details">
                <summary>
                  Agent Communication History
                  ({history.length} messages)
                </summary>

                <div className="message-list">
                  {history.map((message, index) => (
                    <div
                      className="message-card"
                      key={index}
                    >
                      <div className="message-heading">
                        <strong>
                          {message.sender} →{" "}
                          {message.receiver}
                        </strong>

                        <span>Step {index + 1}</span>
                      </div>

                      <p>
                        <strong>Intent:</strong>{" "}
                        {message.intent}
                      </p>

                      <details>
                        <summary>
                          View message data
                        </summary>

                        <pre>
                          {JSON.stringify(
                            message.content,
                            null,
                            2
                          )}
                        </pre>
                      </details>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          </section>
        )}

        <section className="agents-section">
          <div className="section-heading">
            <h2>Multi-Agent Architecture</h2>

            <p>
              Three specialised agents collaborate
              through the orchestrator.
            </p>
          </div>

          <div className="agents">
            <div className="agent-card">
              <div className="agent-number">01</div>

              <h3>Planner Agent</h3>

              <p>
                Analyses tasks and creates structured
                subtasks.
              </p>
            </div>

            <div className="agent-card">
              <div className="agent-number">02</div>

              <h3>Worker Agent</h3>

              <p>
                Processes subtasks using AI and
                generates results.
              </p>
            </div>

            <div className="agent-card">
              <div className="agent-number">03</div>

              <h3>Reviewer Agent</h3>

              <p>
                Validates output and requests
                revisions when required.
              </p>
            </div>
          </div>
        </section>
      </main>

      <footer className="app-footer">
        Multi-Agent Task Assistant
      </footer>
    </div>
  );
}

export default App;
