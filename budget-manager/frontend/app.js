const API_URL = "http://127.0.0.1:5002/budgets";

const form = document.getElementById("budgetForm");
const table = document.getElementById("budgetTable");

let editingId = null;

async function loadBudgets() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error("Failed to load budgets");

        const budgets = await response.json();

        table.innerHTML = "";

        budgets.forEach(budget => {
            const row = document.createElement("tr");

            row.innerHTML = `
                <td>
                    <button onclick="editBudget(${budget.id})">Edit</button>
                    <button onclick="deleteBudget(${budget.id})">Delete</button>
                </td>
                <td>${budget.name}</td>
                <td>${Number(budget.amount).toFixed(2)}</td>
                <td>${budget.start_date}</td>
                <td>${budget.end_date}</td>
                <td>${budget.description || ""}</td>
            `;

            table.appendChild(row);
        });
    } catch (err) {
        table.innerHTML = `<tr><td colspan="6">Error loading budgets</td></tr>`;
        console.error(err);
    }
}

form.addEventListener("submit", async function(event) {
    event.preventDefault();

    const budget = {
        name: document.getElementById("name").value,
        amount: Number(document.getElementById("amount").value),
        start_date: document.getElementById("start_date").value,
        end_date: document.getElementById("end_date").value,
        description: document.getElementById("description").value
    };

    try {
        if (editingId === null) {
            await fetch(API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(budget)
            });
        } else {
            await fetch(`${API_URL}/${editingId}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(budget)
            });

            editingId = null;
            document.querySelector("button[type='submit']").textContent =
                "Add Budget";
        }

        form.reset();
        await loadBudgets();
    } catch (err) {
        console.error(err);
        alert("Error saving budget");
    }
});

async function editBudget(id) {
    try {
        const response = await fetch(`${API_URL}/${id}`);
        if (!response.ok) throw new Error("Failed to fetch budget");

        const budget = await response.json();

        document.getElementById("name").value = budget.name;
        document.getElementById("amount").value = budget.amount;
        document.getElementById("start_date").value = budget.start_date;
        document.getElementById("end_date").value = budget.end_date;
        document.getElementById("description").value =
            budget.description || "";

        editingId = id;

        document.querySelector("button[type='submit']").textContent =
            "Update Budget";
    } catch (err) {
        console.error(err);
        alert("Error loading budget for edit");
    }
}

async function deleteBudget(id) {
    try {
        await fetch(`${API_URL}/${id}`, {
            method: "DELETE"
        });

        await loadBudgets();
    } catch (err) {
        console.error(err);
        alert("Error deleting budget");
    }
}

// Expose edit/delete functions for inline onclick handlers
window.editBudget = editBudget;
window.deleteBudget = deleteBudget;

loadBudgets();

const aiButton = document.getElementById("aiButton");
const aiResult = document.getElementById("aiResult");

aiButton.addEventListener("click", async function() {
    aiResult.textContent = "Analysing your budgets...";

    try {
        const response = await fetch("http://127.0.0.1:5002/ai-insights");
        if (!response.ok) throw new Error("AI service returned an error");

        const data = await response.json();

        if (data && data.insight) {
            aiResult.textContent = data.insight;
        } else if (data && data.error) {
            aiResult.textContent = `Error: ${data.error}`;
        } else {
            aiResult.textContent = JSON.stringify(data);
        }
    } catch (err) {
        console.error(err);
        aiResult.textContent = "Could not fetch AI insights.";
    }
});


const mcpEnable = document.getElementById("mcpEnable");

const mcpButton = document.getElementById("mcpButton");
const mcpResult = document.getElementById("mcpResult");

mcpButton.addEventListener("click", 
    
    async function() {

        if (!mcpEnable.checked) {
                mcpResult.textContent =
                    "MCP is currently disabled. Enable MCP to use the income and expense summary.";
                return;
            }

        mcpResult.textContent = "Calling shared MCP server...";

        try {
            const response = await fetch(
                "http://127.0.0.1:5002/mcp-budget-summary"
            );
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "MCP request failed");
            }

            const result = data.result;
            const largest = result.largest_category;
            const smallest = result.smallest_category;

            mcpResult.textContent =
                `MCP Tool: ${data.tool}\n` +
                `Budget Count: ${result.budget_count}\n` +
                `Total Budget: $${Number(result.total_budget).toFixed(2)}\n` +
                `Average Category Amount: $${Number(result.average_category_amount).toFixed(2)}\n` +
                `Largest Category: ${largest ? `${largest.name} - $${Number(largest.amount).toFixed(2)}` : "No data"}\n` +
                `Smallest Category: ${smallest ? `${smallest.name} - $${Number(smallest.amount).toFixed(2)}` : "No data"}\n` +
                `Top Three Share: ${Number(result.top_three_share_pct).toFixed(2)}%`;
        } catch (error) {
            console.error(error);
            mcpResult.textContent = "Could not connect to the MCP service.";
    }
});

const ragEnable = document.getElementById("ragEnable");
const ragButton = document.getElementById("ragButton");
const ragQuestion = document.getElementById("ragQuestion");
const ragResult = document.getElementById("ragResult");

ragButton.addEventListener("click", 
    
    async function() {
        if (!ragEnable.checked) {
            ragResult.textContent =
                "RAG is currently disabled. Enable RAG to ask questions using the project knowledge base.";
            return;
        }

        const question = ragQuestion.value.trim();

        if (!question) {
            ragResult.textContent = "Please enter a question.";
            return;
        }

        ragResult.textContent = "Searching project knowledge...";

        try {
            const response = await fetch(
                "http://127.0.0.1:5002/rag-query",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({query: question})
                }
            );
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "RAG request failed");
            }

            if (data.grounded === false) {
                ragResult.textContent =
                    `${data.answer}\nConfidence: ${data.confidence}`;
                return;
            }

            ragResult.textContent =
                `Answer: ${data.answer}\n\n` +
                `Source: ${data.sources.join(", ")}\n` +
                `Confidence: ${data.confidence}`;
        } catch (error) {
            console.error(error);
            ragResult.textContent = "Could not connect to the RAG service.";
    }
});

const backButton = document.getElementById("backButton");

backButton.addEventListener("click", function () {
    window.location.href = "http://localhost:8080";
});

