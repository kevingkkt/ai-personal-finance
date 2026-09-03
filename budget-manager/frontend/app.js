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
                <td>${budget.name}</td>
                <td>${Number(budget.amount).toFixed(2)}</td>
                <td>${budget.start_date}</td>
                <td>${budget.end_date}</td>
                <td>${budget.description || ""}</td>
                <td>
                    <button onclick="editBudget(${budget.id})">Edit</button>
                    <button onclick="deleteBudget(${budget.id})">Delete</button>
                </td>
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

const backButton = document.getElementById("backButton");

backButton.addEventListener("click", function () {
    window.location.href = "http://localhost:8080";
});

