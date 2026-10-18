import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from flask import Flask, jsonify, request


app = Flask(__name__)


# Configuration
OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

MULTI_AGENT_MODEL = os.getenv(
    "MULTI_AGENT_MODEL",
    "llama3.1:8b"
)

PORT = int(
    os.getenv(
        "MULTI_AGENT_PORT",
        "7003"
    )
)

# Workflow storage and audit log
WORKFLOWS = {}

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

AUDIT_LOG = LOG_DIR / "multi_agent_audit.jsonl"


def timestamp():

    return datetime.now(
        timezone.utc
    ).isoformat()


def save_audit_event(
    workflow_id,
    stage,
    message
):

    event = {
        "time":
            timestamp(),

        "workflow_id":
            workflow_id,

        "stage":
            stage,

        "message":
            message
    }

    with AUDIT_LOG.open(
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            json.dumps(event) + "\n"
        )


# Ollama helper
def call_ollama(
    system_role,
    prompt
):

    full_prompt = f"""
You are the {system_role} in a university Personal Finance Management System.

Follow your assigned role carefully.

IMPORTANT EVIDENCE RULES:
- Treat the supplied evidence as the only source of truth.
- Never invent, assume, request, or mention information that is not present in the supplied evidence.
- Do not introduce bank statements, tax records, pay slips, balance sheets, investments, liabilities, or other documents unless they are explicitly included in the evidence.
- If the evidence is not sufficient for something, say that it is not supported by the supplied evidence.
- Do not use outside financial knowledge to create new facts about the user.

{prompt}

Give a concise and clear response.
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model":
                    MULTI_AGENT_MODEL,

                "prompt":
                    full_prompt,

                "stream":
                    False,

                "options": {
                    "temperature": 0
                }
            },
            timeout=300
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "response",
            "No response was generated."
        ).strip()

    except requests.RequestException as error:

        raise RuntimeError(
            f"Agent service error: {error}"
        ) from error


# Planner Agent
def planner_agent(
    task,
    evidence
):

    prompt = f"""
TASK:
{task}

AVAILABLE EVIDENCE:
{evidence}

Create a short plan for completing this task.

Rules:
- Use only the supplied evidence.
- Do not invent missing facts, documents, transactions, or personal information.
- If evidence is missing, clearly state what evidence is unavailable.
- Do not assume access to pay slips, tax returns, bank records, or other documents unless they are explicitly supplied.

The plan should:
1. Identify what needs to be done.
2. Identify which supplied evidence can be used.
3. Explain what the Worker should produce.
"""

    return call_ollama(
        "Planner Agent",
        prompt
    )


# Worker Agent
def worker_agent(
    task,
    plan,
    evidence
):

    prompt = f"""
TASK:
{task}

PLANNER'S PLAN:
{plan}

AVAILABLE EVIDENCE:
{evidence}

Perform the task using only the supplied evidence.

Rules:
- Do not invent information.
- Do not assume access to information that was not supplied.
- If there is not enough evidence, state "INSUFFICIENT EVIDENCE" and explain what is missing.
- Return the completed work for the Reviewer.
"""

    return call_ollama(
        "Worker Agent",
        prompt
    )


# Reviewer Agent
def reviewer_agent(
    task,
    plan,
    worker_output,
    evidence
):

    prompt = f"""
TASK:
{task}

PLANNER'S PLAN:
{plan}

WORKER OUTPUT:
{worker_output}

AVAILABLE EVIDENCE:
{evidence}

Review the Worker output.

Check:
1. Whether the plan was followed.
2. Whether every important claim is supported by the supplied evidence.
3. Whether the Worker invented or assumed information.
4. Whether there are errors or risks.
5. What should be improved.

If unsupported information was invented, do not approve it.

Finish with one recommendation:
APPROVE
PARTIAL
REVISE
REJECT
"""

    return call_ollama(
        "Reviewer Agent",
        prompt
    )


# Health
@app.get("/health")
def health():

    return jsonify({
        "service":
            "Shared Multi-Agent Server",

        "status":
            "ok",

        "model":
            MULTI_AGENT_MODEL
    }), 200



# Start Multi-Agent Workflow
@app.post("/multi-agent")
def start_multi_agent_workflow():

    body = (
        request.get_json(
            silent=True
        ) or {}
    )

    task = str(
        body.get(
            "task",
            ""
        )
    ).strip()

    evidence = body.get(
        "evidence",
        ""
    )

    if not task:

        return jsonify({
            "error":
                "A task is required."
        }), 400

    if isinstance(
        evidence,
        (dict, list)
    ):

        evidence_text = json.dumps(
            evidence,
            indent=2
        )

    else:

        evidence_text = str(
            evidence
        )

    workflow_id = str(
        uuid.uuid4()
    )

    save_audit_event(
        workflow_id,
        "WORKFLOW_STARTED",
        task
    )

    planner_output = None
    worker_output = None
    reviewer_output = None

    try:

        planner_output = planner_agent(
            task,
            evidence_text
        )

        save_audit_event(
            workflow_id,
            "PLANNER",
            planner_output
        )

        worker_output = worker_agent(
            task,
            planner_output,
            evidence_text
        )

        save_audit_event(
            workflow_id,
            "WORKER",
            worker_output
        )

        reviewer_output = reviewer_agent(
            task,
            planner_output,
            worker_output,
            evidence_text
        )

        save_audit_event(
            workflow_id,
            "REVIEWER",
            reviewer_output
        )

    except RuntimeError as error:

        workflow = {
            "workflow_id":
                workflow_id,

            "created_at":
                timestamp(),

            "task":
                task,

            "evidence":
                evidence,

            "planner": {
                "role":
                    "Planner",

                "output":
                    planner_output
            },

            "worker": {
                "role":
                    "Worker",

                "output":
                    worker_output
            },

            "reviewer": {
                "role":
                    "Reviewer",

                "output":
                    reviewer_output
            },

            "human_review":
                None,

            "status":
                "FAILED",

            "error":
                str(error)
        }

        WORKFLOWS[
            workflow_id
        ] = workflow

        save_audit_event(
            workflow_id,
            "WORKFLOW_FAILED",
            str(error)
        )

        return jsonify(
            workflow
        ), 503

    workflow = {
        "workflow_id":
            workflow_id,

        "created_at":
            timestamp(),

        "task":
            task,

        "evidence":
            evidence,

        "planner": {
            "role":
                "Planner",

            "output":
                planner_output
        },

        "worker": {
            "role":
                "Worker",

            "output":
                worker_output
        },

        "reviewer": {
            "role":
                "Reviewer",

            "output":
                reviewer_output
        },

        "human_review":
            None,

        "status":
            "AWAITING_HUMAN_REVIEW"
    }

    WORKFLOWS[
        workflow_id
    ] = workflow

    save_audit_event(
        workflow_id,
        "AWAITING_HUMAN_REVIEW",
        "Workflow requires a human decision."
    )

    return jsonify(
        workflow
    ), 200


# Human Review
@app.post(
    "/multi-agent/<workflow_id>/human-review"
)
def human_review(
    workflow_id
):

    if workflow_id not in WORKFLOWS:

        return jsonify({
            "error":
                "Workflow not found."
        }), 404

    workflow = WORKFLOWS[
        workflow_id
    ]

    if workflow.get("status") == "FAILED":

        return jsonify({
            "error":
                "A failed workflow cannot be approved through Human Review."
        }), 409

    body = (
        request.get_json(
            silent=True
        ) or {}
    )

    decision = str(
        body.get(
            "decision",
            ""
        )
    ).strip().lower()

    comments = str(
        body.get(
            "comments",
            ""
        )
    ).strip()

    allowed_decisions = {
        "approve",
        "correct",
        "partial",
        "reject"
    }

    if decision not in allowed_decisions:

        return jsonify({
            "error":
                (
                    "Decision must be approve, "
                    "correct, partial, or reject."
                )
        }), 400

    workflow["human_review"] = {
        "decision":
            decision,

        "comments":
            comments,

        "reviewed_at":
            timestamp()
    }

    if decision == "approve":

        workflow["status"] = (
            "APPROVED"
        )

    elif decision == "partial":

        workflow["status"] = (
            "PARTIALLY_APPROVED"
        )

    elif decision == "correct":

        workflow["status"] = (
            "CORRECTION_REQUIRED"
        )

    else:

        workflow["status"] = (
            "REJECTED"
        )

    save_audit_event(
        workflow_id,
        "HUMAN_REVIEW",
        (
            f"Decision: {decision}. "
            f"Comments: {comments}"
        )
    )

    return jsonify(
        workflow
    ), 200

# Get one workflow

@app.get(
    "/multi-agent/<workflow_id>"
)
def get_workflow(
    workflow_id
):

    workflow = WORKFLOWS.get(
        workflow_id
    )

    if workflow is None:

        return jsonify({
            "error":
                "Workflow not found."
        }), 404

    return jsonify(
        workflow
    ), 200



# Workflow history


@app.get(
    "/multi-agent-history"
)
def workflow_history():

    return jsonify(
        list(
            WORKFLOWS.values()
        )
    ), 200



# Run server
if __name__ == "__main__":

    print(
        "Shared Multi-Agent Server"
    )

    print(
        f"Model: {MULTI_AGENT_MODEL}"
    )

    print(
        f"Port: {PORT}"
    )

    print()

    print(
        "Workflow:"
    )

    print(
        "Planner -> Worker -> Reviewer -> Human Review"
    )

    print()

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )