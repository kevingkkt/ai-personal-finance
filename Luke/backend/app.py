from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import requests
import asyncio
import json
from mcp import Client

app = Flask(__name__)

# Cloud security: only the app's own frontends may call this API, and each
# client IP is rate limited. Local runs default to any origin.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]
CORS(app, origins=ALLOWED_ORIGINS)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[os.environ.get("RATE_LIMIT", "300 per minute")],
    storage_uri="memory://",
)

DATABASE_API_URL = os.environ.get(
    "DATABASE_API_URL",
    "http://bills-database:5002"
)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")

MCP_URL = os.environ.get("MCP_URL","http://localhost:7001/mcp")


RAG_URL = os.environ.get("RAG_URL","http://localhost:7002/rag")
#taken off kevin code
MULTI_AGENT_URL = os.environ.get("MULTI_AGENT_URL", "http://localhost:7003")
AI_MODE_ENABLED = (
    os.environ.get(
        "AI_MODE_ENABLED",
        "false"
    ).lower()
    == "true"
)

MCP_ENABLED = (
    os.environ.get(
        "MCP_ENABLED",
        "false"
    ).lower()
    == "true"
)

RAG_ENABLED = (
    os.environ.get(
        "RAG_ENABLED",
        "false"
    ).lower()
    == "true"
)


MULTI_AGENT_ENABLED = (
    os.environ.get(
        "MULTI_AGENT_ENABLED",
        "false"
    ).lower()
    == "true"
)

#get all the bills
@app.route("/bills", methods=["GET"])
def get_bills():
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/bills",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

#grab a single bill by id
@app.route("/bills/<int:bill_id>", methods=["GET"])
def get_bill(bill_id):
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/bills/{bill_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500
# for paid bills
@app.route("/bills/paid", methods=["GET"])
def get_paid_bills():
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/bills/by-status",
            params={"payment_status": 1},
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


# for unpaid bills
@app.route("/bills/unpaid", methods=["GET"])
def get_unpaid_bills():
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/bills/by-status",
            params={"payment_status": 0},
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500
#MCP
async def call_total_unpaid_mcp():
    async with Client(MCP_URL) as client:

        result = await client.call_tool(
            "get_total_unpaid",
            {}
        )

        if result.is_error:
            raise Exception("MCP tool returned an error")

        if not result.content:
            raise Exception("MCP tool returned no content")
        return json.loads(result.content[0].text)
#now setup is done
@app.route(
    "/mcp/total-unpaid",
    methods=["GET"]
)
def mcp_total_unpaid():
    try:
        mcp_result = asyncio.run(
            call_total_unpaid_mcp()
        )

        return jsonify({
            "source":"Shared MCP Server",

            "tool":"get_total_unpaid",

            "result":mcp_result
        })


    except Exception as error:

        return jsonify({
            "error":
                "Could not connect to MCP server",

            "details":
                str(error)
        }), 500


@app.route("/bills", methods=["POST"])
def create_bill():
    try:
        response = requests.post(
            f"{DATABASE_API_URL}/bills",
            json=request.get_json(),
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


@app.route("/bills/<int:bill_id>", methods=["PUT"])
def update_bill(bill_id):
    try:
        response = requests.put(
            f"{DATABASE_API_URL}/bills/{bill_id}",
            json=request.get_json(),
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


@app.route("/bills/<int:bill_id>", methods=["DELETE"])
def delete_bill(bill_id):
    try:
        response = requests.delete(
            f"{DATABASE_API_URL}/bills/{bill_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500
        
        
###########
#raf
###########


@app.route(
    "/rag-query",
    methods=["POST"]
)
def rag_query():

    data = request.get_json(
        silent=True
    ) or {}

    query = str(data.get("query", "")).strip()
    feature = data.get("feature", "bills")
    if not isinstance(feature, str) or not feature.strip():
        feature = "bills"

    if not query:
        return jsonify({
            "error":
                "A RAG question is required."
        }), 400
    try:
        response = requests.post(
            RAG_URL,
            json={
                "query": query,
                "feature": feature
            },
            timeout=120
        )

        response.raise_for_status()

        return jsonify(
            response.json()
        )

    except requests.exceptions.RequestException as error:

        return jsonify({
            "error":
                "Could not connect to RAG server.",

            "details":
                str(error)
        }), 503

@app.route("/ai-insights", methods=["POST"])
def ai_insights():
    #adding flush to see if it truely isnt geting even in but we will see
    print("backend was called for AI insights", flush =True)
    inputData = request.get_json() or  {}
    userInput = inputData.get("input", "")
    #this is for the database
    
    
    try:
        database_response = requests.get(
            f"{DATABASE_API_URL}/bills",
            timeout=10
        )

        if database_response.status_code != 200:
            return jsonify({
                "error": "Could not get the bill data"
            }), 500

        bill_data = database_response.json()

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

    prompt = f"""
You are a intelligent ai assistant that is able to analyse incomining  bills and provide insights on making sure that bills are 
being paid on time  and won't miss a bill payment.


Analyse the following bill data and give insights on how to manage the bills effectively:

{bill_data}

Output the following in this exact format:
Give a summary of the unpaid bills, including the total amount due and the number of unpaid bills.
and then give a list of reccommendations on how to pay off the bills the best way possible each week and the amount that they should pay each 
week to make sure that they are paying off the bills on time and not missing any payments.

Return ONLY the final answer.
Do not include your reasoning, thinking process, analysis steps, or a second final answer.

Rules:
Return as a string in about 1 paragraph.
Do not make up any extra information that is not from the bill data or user input.
Do not ignore any of the user input, if it is relevant to the bills.


Also consider the following user input when providing your insights if that be a specific area they want to focus on or a specific question 
they have about the bills:
{userInput}
"""

    try:
        print("check just before OLLAMA to see if its at fault", flush =True)
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "deepseek-r1:1.5b",
                "prompt": prompt,
                "stream": False
            },
            timeout=600
        )
        print("check just after OLLAMA to see if its at fault", flush =True)
        if response.status_code != 200:
            return jsonify({
                "error": "The AI service is unavailable with the following status code: " + str(response.status_code)
            }), 500

        result = response.json()
        print("AI made it to the end")
        return jsonify({
            "model": "deepseek-r1:1.5b",
            "insight": result["response"]
        })

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Sorry, the program could not connect to Ollama"
        }), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "The API worked in backend"
    })

#forgot to do first part
@app.route("/multi-agent-review",
    methods=["POST"])
def multi_agent_review():
    if not MULTI_AGENT_ENABLED:
        return jsonify({"error": "Sorry the Multi-Agent was set to disabled"}), 503

    data = request.get_json(
        silent=True
    ) or {}

    try:
        response = requests.post(
            f"{MULTI_AGENT_URL}/multi-agent",
            json=data,
            timeout=167
        )
        return jsonify(response.json()),response.status_code
    except requests.exceptions.RequestException as error:
        return jsonify({"error": "Could not connect to Multi-Agent server.","details": str(error)}), 503
    


#human review
@app.route(
    "/multi-agent/<workflow_id>/human-review",
    methods=["POST"]
)
def multi_agent_human_review(workflow_id):

    if not MULTI_AGENT_ENABLED:
        return jsonify({
            "error": "Multi-Agent is set to disabled"
        }), 503

    data = request.get_json(
        silent=True
    ) or {}

    try:

        response = requests.post(
            f"{MULTI_AGENT_URL}/multi-agent/"
            f"{workflow_id}/human-review",
            json=data,
            timeout=30
        )

        return jsonify(
            response.json()
        ), response.status_code

    except requests.exceptions.RequestException as error:

        return jsonify({
            "error": "Could not connect to Multi-Agent server.",
            "details": str(error)
        }), 503


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        debug=False,
        port=5001
    )