# Multi-Agent Task Assistant

**COIT12204 – AI-Assisted Software Development**  
**Assessment 4: Multi-Agent System**  
**Developed by:** Prajita Bhandari

## 1. Project Overview

The Multi-Agent Task Assistant is an AI-powered task management application developed using Python, FastAPI, LangChain, Google Gemini and React.

The project extends the Single-Agent Task Assistant developed for Assessment 3 by introducing a collaborative multi-agent architecture. Three specialised AI agents—Planner, Worker and Reviewer—work together under the supervision of an Orchestrator to process user requests.

The Planner divides a task into subtasks, the Worker executes those subtasks using Google Gemini, and the Reviewer evaluates the generated output. If improvements are required, the Reviewer can request revisions before the workflow finishes.

The application provides a React-based user interface for submitting tasks, viewing generated results and inspecting communication between agents.

## 2. Project Objectives

The main objectives of this project are to:

- Implement a multi-agent system with three specialised agents.
- Coordinate agent execution through a central Orchestrator.
- Support structured communication between agents.
- Integrate Google Gemini for AI-assisted task planning, execution and review.
- Implement feedback and revision cycles.
- Apply input validation, exception handling and workflow guardrails.
- Provide a user-friendly React interface.
- Evaluate system behaviour through automated testing and live integration testing.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Backend programming |
| FastAPI | REST API development |
| Pydantic | Data modelling and input validation |
| Google Gemini | AI-generated planning, execution and review |
| LangChain | AI integration for the retained single-agent functionality |
| React | Frontend user interface |
| Vite | Frontend development and build tool |
| JavaScript | Frontend application logic |
| Uvicorn | ASGI application server |
| Pytest | Automated testing |
| HTTPX | HTTP requests and API testing |
| Python logging | Workflow monitoring and debugging |
| Git and GitHub | Version control |

## 4. Key Features

### 4.1. Multi-Agent Collaboration

The application implements three specialised agents that perform different responsibilities.

**Planner Agent**

- Receives the user's task.
- Analyses the task requirements.
- Generates structured subtasks.
- Sends execution instructions to the Worker.

**Worker Agent**

- Receives subtasks from the Planner.
- Uses Google Gemini to generate responses.
- Processes subtasks and combines their results.
- Sends the generated output to the Reviewer.
- Supports revisions when requested.

**Reviewer Agent**

- Evaluates the Worker's generated output.
- Checks response structure and quality.
- Approves acceptable results.
- Requests revisions when improvements are necessary.
- Returns review decisions to the Orchestrator.

### 4.2. Orchestrator

The Orchestrator manages the overall workflow and coordinates communication between agents.

Its responsibilities include:

- Initialising workflows.
- Routing messages between agents.
- Maintaining workflow identifiers.
- Recording message history.
- Tracking execution steps and revisions.
- Enforcing maximum iteration and revision limits.
- Handling invalid routing and agent errors.
- Returning the final workflow response.

### 4.3. Structured Agent Communication

Agents exchange information using the `AgentMessage` model.

Each message includes:

- `sender` – Component sending the message.
- `receiver` – Intended destination.
- `intent` – Purpose of the message.
- `content` – Task instructions, generated results or review feedback.
- `constraints` – Additional workflow requirements.

The structured communication model improves consistency, traceability and coordination.

### 4.4. Feedback and Revision

The Reviewer can approve the Worker's output or request improvements.

When a revision is required, the Orchestrator routes the feedback to the Worker for further processing.

Execution and revision limits prevent unlimited communication cycles.

### 4.5. React User Interface

The frontend provides:

- A task submission interface.
- Workflow execution status.
- Planner-generated subtasks.
- Worker-generated results.
- Reviewer approval information.
- Final AI-generated output.
- Workflow step and revision counts.
- Agent communication history.
- A visual summary of the multi-agent architecture.

## 5. Project Structure

```text
Multi-Agent-Task-Assistant/
│
├── agents/
│   ├── __init__.py
│   ├── agent_state.py
│   ├── due_date_agent.py
│   ├── planner_agent.py
│   ├── reviewer_agent.py
│   ├── tools.py
│   └── worker_agent.py
│
├── api/
│   ├── __init__.py
│   ├── agent_routes.py
│   ├── routes.py
│   └── workflow_routes.py
│
├── models/
│   ├── __init__.py
│   ├── agent_message.py
│   └── task.py
│
├── orchestration/
│   └── orchestrator.py
│
├── services/
│   └── task_service.py
│
├── utils/
│   └── llm_client.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_agent_routes.py
│   ├── test_agent_state.py
│   ├── test_agent_tools.py
│   ├── test_api_routes.py
│   ├── test_due_date_agent.py
│   ├── test_orchestrator.py
│   ├── test_reviewer_agent.py
│   ├── test_task_model.py
│   ├── test_task_service.py
│   ├── test_worker_agent.py
│   └── test_workflow_routes.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── docs/
├── .env.example
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

The project retains the earlier task-management and Due Date Agent components from Assessment 3. These remain part of the application alongside the new multi-agent functionality.

## 6. Multi-Agent System Architecture

The workflow follows a centralised orchestration architecture.

```text
                  USER
                    |
                    v
              React Frontend
                    |
                    v
              FastAPI Backend
                    |
                    v
               Orchestrator
                    |
                    v
               Planner Agent
                    |
                    | Planned Subtasks
                    v
                Worker Agent
                    |
                    | Execution Results
                    v
               Reviewer Agent
                    |
          +---------+----------+
          |                    |
       Approved           Revision Required
          |                    |
          v                    v
     Orchestrator          Worker Agent
          |                    |
          |                    |
          |             Revised Output
          |                    |
          |                    v
          |               Reviewer Agent
          |                    |
          +--------------------+
                    |
                    v
              Final Response
                    |
                    v
               React Frontend
```

The Orchestrator controls communication and prevents agents from exchanging messages outside the supported workflow routes.

## 7. Agent Communication Workflow

A successful workflow generally involves four communication steps.

| Step | Sender | Receiver | Intent |
|---|---|---|---|
| 1 | User | Planner | `plan_task` |
| 2 | Planner | Worker | `execute_subtasks` |
| 3 | Worker | Reviewer | `execution_result` |
| 4 | Reviewer | Orchestrator | `review_approved` |

If the Reviewer requests a revision, additional communication steps occur.

### Example Task

A user may submit:

> Create a seven-day study timetable for a university student studying Python, Database Systems and Networking. Include daily study sessions, revision and breaks.

The Planner divides the task into four subtasks, the Worker generates the requested content, and the Reviewer evaluates the results.

In a successful live integration test, the application recorded:

- Workflow steps: 4
- Revisions: 0
- Communication messages: 4
- Reviewer decision: Approved
- HTTP response: 200 OK

These values describe the demonstrated successful run, not a guarantee that every task will complete in four steps.

## 8. API Endpoints

The application exposes the multi-agent workflow through FastAPI.

### 8.1. Run Multi-Agent Workflow

**Endpoint**

```http
POST /api/workflow/run
```

**Example request**

```json
{
  "task": "Prepare a weekly study plan for Python, Database Systems and Networking"
}
```

The endpoint accepts a natural-language task and initiates the multi-agent workflow.

The response includes workflow information such as the execution status, workflow identifier, step count, revision count, generated output and communication history.

### 8.2. Swagger Documentation

FastAPI provides interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

The documentation allows users to inspect endpoints, submit test requests and examine API responses.

### 8.3. Existing Task Management

The project also retains the original task-management functionality from Assessment 3, including task creation, retrieval, updating, deletion and AI-assisted due-date suggestions.

The Due Date Agent endpoint is:

```http
POST /api/agent/suggest_due_date
```

## 9. Installation and Setup

### 9.1. Prerequisites

Before running the application, install:

- Python 3.11 or a compatible version.
- Node.js and npm.
- Git.
- Visual Studio Code or another code editor.
- A Google Gemini API key.
- An internet connection for live AI requests.

### 9.2. Clone the Repository

```bash
git clone https://github.com/prajitabhandari1234/Multi-Agent-Task-Assistant.git
cd Multi-Agent-Task-Assistant
```

### 9.3. Create a Python Virtual Environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 9.4. Install Backend Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 9.5. Configure Environment Variables

Create a `.env` file in the project root.

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**macOS/Linux**

```bash
cp .env.example .env
```

Open `.env` and configure the Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Replace the placeholder with a valid API key.

Never upload a real API key to GitHub.

### 9.6. Start the Backend

From the project root, run:

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

### 9.7. Install Frontend Dependencies

Open a second terminal:

```bash
cd frontend
npm ci
```

### 9.8. Start the Frontend

```bash
npm run dev
```

Open the local address displayed by Vite, typically:

```text
http://localhost:5173
```

The backend and frontend should run simultaneously in separate terminals.

## 10. Testing

The project uses Pytest to verify application functionality, agent behaviour and workflow reliability.

### 10.1. Run All Tests

From the project root:

```bash
python -m pytest -v
```

### 10.2. Run Orchestrator Tests

```bash
python -m pytest tests/test_orchestrator.py -v
```

### 10.3. Run Worker Tests

```bash
python -m pytest tests/test_worker_agent.py -v
```

### 10.4. Run Reviewer Tests

```bash
python -m pytest tests/test_reviewer_agent.py -v
```

### 10.5. Run Workflow API Tests

```bash
python -m pytest tests/test_workflow_routes.py -v
```

### 10.6. Test Coverage

The automated tests evaluate:

- Agent communication and routing.
- Successful workflow completion.
- Workflow identifier generation.
- Message history.
- Worker execution.
- Reviewer approval and revision behaviour.
- Invalid receiver handling.
- Agent exceptions.
- Maximum iteration guardrails.
- FastAPI workflow request validation.
- Existing task-management and single-agent functionality.

The project has demonstrated successful automated testing, including Orchestrator tests and a complete backend integration run.

Tests using mocked agent or model responses help avoid unpredictable live Gemini responses during automated regression testing.

## 11. Failure Handling and Resilience

### 11.1. Input Validation

FastAPI validates incoming requests before starting the workflow.

Invalid requests, including empty or malformed task input, are rejected.

### 11.2. Structured Error Responses

The system provides structured responses for different failure conditions.

| Error | Description |
|---|---|
| `agent_error` | An unexpected agent exception occurs |
| `execution_failed` | Worker execution cannot complete |
| `routing_error` | A message has an unsupported receiver |
| `max_iterations_exceeded` | The workflow reaches its iteration limit |

### 11.3. Iteration and Revision Limits

The Orchestrator enforces execution limits to prevent endless feedback cycles.

The workflow API in the reviewed implementation configures a maximum of five iterations.

Revision handling is also bounded to prevent repeated processing without a defined stopping condition.

### 11.4. Reviewer Validation

The Reviewer evaluates the generated results and may request changes when the output does not meet its quality criteria.

Malformed or unsuccessful AI review responses are handled through the application's validation and error-handling logic rather than being treated as automatically approved.

### 11.5. Logging

Python logging records:

- Workflow identifiers.
- Agent activity.
- Message routing.
- Execution progress.
- Review decisions.
- Exceptions and failures.

These logs support debugging, evaluation and traceability.

## 12. Evaluation and Results

### 12.1. Successful Workflow

A live integration test was performed using a seven-day university study timetable request.

The workflow completed successfully, demonstrating communication between the React frontend, FastAPI backend, Orchestrator and three specialised agents.

The Worker processed four subtasks using Gemini, and the Reviewer approved the final output.

### 12.2. Variable AI Responses

During development, a test expected exactly four communication messages.

However, additional review interactions caused the workflow to record six messages and reach its configured iteration limit.

This exposed the unreliability of fixed-message-count assumptions when live AI responses can vary.

The automated tests were improved through mocked agent responses, allowing predictable approval and revision scenarios to be evaluated independently.

### 12.3. Invalid Receiver Handling

The Orchestrator was tested using an unsupported message receiver.

The `test_invalid_receiver_returns_routing_error` test verified that the system returned a structured routing error instead of continuing through an invalid communication path.

### 12.4. Output Quality

Although the live workflow was approved, manual evaluation identified inconsistencies in some study-hour calculations.

This highlights an important limitation: AI-assisted review improves quality control but does not guarantee factual or numerical correctness.

## 13. Limitations

The current implementation has several limitations:

- AI-generated content can contain inaccuracies.
- Reviewer decisions may vary between executions.
- External Gemini requests require network connectivity and available API quota.
- Structured errors do not provide a complete offline fallback.
- Comprehensive timeout, retry and alternative-model fallback mechanisms have not been established by the available testing evidence.
- Workflow iteration limits may stop tasks that require several revision cycles.
- Earlier task-management functionality uses in-memory storage.

These limitations should be considered when evaluating reliability and potential production deployment.

## 14. Future Improvements

Potential future improvements include:

- Persistent database storage.
- Improved frontend responsiveness.
- More detailed workflow analytics.
- Deterministic checks for calculations and structured outputs.
- Configurable workflow iteration limits.
- Improved retry and timeout management.
- Alternative-model fallback support.
- Additional Planner Agent unit tests.
- Enhanced reviewer feedback and revision quality.
- User authentication and workflow history.
- Cloud deployment and monitoring.

## 15. Security Considerations

The application uses environment variables to configure Gemini credentials.

The `.env` file must not be committed to GitHub.

The `.gitignore` should exclude:

```gitignore
.env
.venv/
venv/
__pycache__/
.pytest_cache/
frontend/node_modules/
frontend/dist/
```

Only a placeholder `.env.example` should be included in the repository.

If an API key is accidentally exposed, it should be revoked and replaced.

## 16. Troubleshooting

### Backend Does Not Start

Check that the Python virtual environment is activated and dependencies are installed:

```bash
pip install -r requirements.txt
```

### Gemini API Error

Confirm that:

- The `.env` file exists.
- `GEMINI_API_KEY` is configured correctly.
- The API key is valid.
- The Gemini service is accessible.
- The configured model is available to the API key.

### Frontend Does Not Start

From the `frontend` directory, run:

```bash
npm ci
npm run dev
```

### Port Already in Use

Start FastAPI on a different port if required:

```bash
python -m uvicorn main:app --reload --port 8001
```

If changing the backend port, update the frontend API configuration accordingly.

### Tests Fail Unexpectedly

Run:

```bash
python -m pytest -v
```

Check whether the failure involves live AI responses, incorrect test expectations, missing dependencies or configuration issues.

For reliable automated tests, use mocked model responses rather than depending on live Gemini output.

## 17. AI Assistance Declaration

Generative AI tools were used as supporting resources during project development, including technical explanation, code review, debugging, testing assistance and documentation preparation.

AI-generated suggestions were reviewed and adapted during implementation. The system was evaluated through automated testing, API execution, agent communication logs and frontend integration testing.

The project demonstrates the implementation of a coordinated multi-agent architecture using FastAPI, Google Gemini, structured communication, workflow orchestration, validation and testing.

## 18. Author

**Prajita Bhandari**  
