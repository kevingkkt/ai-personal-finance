from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import os


app = Flask(__name__)
CORS(app)


# ----------------------------------
# Configuration
# ----------------------------------

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"

OLLAMA_URL = os.environ.get(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

RAG_MODEL = os.environ.get(
    "RAG_MODEL",
    "qwen2.5:0.5b"
)


# ----------------------------------
# Load knowledge
# ----------------------------------

def load_knowledge():
    chunks = []

    for file_path in KNOWLEDGE_DIR.glob("*.md"):

        text = file_path.read_text(
            encoding="utf-8"
        )

        # Split the document into smaller sections
        sections = [
            section.strip()
            for section in text.split("\n\n")
            if section.strip()
        ]

        for section in sections:

            chunks.append({
                "text": section,
                "source": file_path.name
            })

    return chunks


# ----------------------------------
# Retrieve relevant context
# ----------------------------------

def retrieve_context(query):

    chunks = load_knowledge()

    if not chunks:
        return None

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    vectors = vectorizer.fit_transform(
        texts + [query]
    )

    document_vectors = vectors[:-1]
    query_vector = vectors[-1]

    similarities = cosine_similarity(
        query_vector,
        document_vectors
    )[0]

    best_index = similarities.argmax()
    best_score = float(
        similarities[best_index]
    )

    # Not enough relevant context
    if best_score < 0.10:
        return None

    best_chunk = chunks[best_index]

    if best_score >= 0.35:
        confidence = "High"
    elif best_score >= 0.20:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        "context": best_chunk["text"],
        "source": best_chunk["source"],
        "score": round(best_score, 3),
        "confidence": confidence
    }


# ----------------------------------
# Generate grounded answer
# ----------------------------------

def generate_grounded_answer(
    query,
    retrieved
):

    prompt = f"""
You are a grounded question-answering assistant.

Answer the question ONLY using the CONTEXT below.

Rules:
1. Do not use outside knowledge.
2. Do not add information that is not stated in the context.
3. If the context contains a formula or definition, use it exactly.
4. Keep the answer short and direct.
5. If the answer is not supported by the context, reply exactly:
   Insufficient context to answer this question.
6. Do not mention other factors unless they appear in the context.
7. Do not provide professional financial, investment, tax or credit advice.

CONTEXT:
{retrieved["context"]}

QUESTION:
{query}

ANSWER:
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": RAG_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0
            }
        },
        timeout=120
    )

    response.raise_for_status()

    return response.json().get(
        "response",
        ""
    ).strip()


# ----------------------------------
# Health endpoint
# ----------------------------------

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    knowledge_files = list(
        KNOWLEDGE_DIR.glob("*.md")
    )

    return jsonify({
        "status": "ok",
        "service": "Shared RAG Server",
        "model": RAG_MODEL,
        "knowledge_files": len(
            knowledge_files
        )
    })


# ----------------------------------
# RAG endpoint
# ----------------------------------

@app.route(
    "/rag",
    methods=["POST"]
)
def rag():

    data = request.get_json(
        silent=True
    ) or {}

    query = str(
        data.get("query", "")
    ).strip()

    if not query:

        return jsonify({
            "error": "A query is required."
        }), 400

    try:

        retrieved = retrieve_context(
            query
        )

        # Required insufficient-context behaviour
        if retrieved is None:

            return jsonify({
                "answer": (
                    "Insufficient context to "
                    "answer this question."
                ),
                "sources": [],
                "confidence": "Insufficient",
                "grounded": False
            })

        answer = generate_grounded_answer(
            query,
            retrieved
        )

        return jsonify({
            "answer": answer,
            "sources": [
                retrieved["source"]
            ],
            "confidence":
                retrieved["confidence"],
            "retrieval_score":
                retrieved["score"],
            "grounded": True
        })

    except requests.exceptions.RequestException:

        return jsonify({
            "error": (
                "Could not connect to the "
                "local Ollama service."
            )
        }), 503

    except Exception as error:

        return jsonify({
            "error": "RAG request failed.",
            "details": str(error)
        }), 500


# ----------------------------------
# Start local RAG server
# ----------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=7002,
        debug=True
    )