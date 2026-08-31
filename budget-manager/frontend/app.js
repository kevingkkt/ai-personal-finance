const API_URL = "http://127.0.0.1:5004/budgets"; 

const form = document.getElementById("budgetForm");
const table = document.getElementById("budgetTable");

let editingId = null;

async function loadBudgets() {
    const response = await fetch(API_URL);
    const budgets = await response.json();

    table.innerHTML = "";

    budgets.forEach(budget => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${budget.name}</td>
            <td>${budget.amount}</td>
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
    loadBudgets();
});

async function editBudget(id) {
    const response = await fetch(`${API_URL}/${id}`);
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
}

async function deleteBudget(id) {
    await fetch(`${API_URL}/${id}`, {
        method: "DELETE"
    });

    loadBudgets();
}

loadBudgets();

const aiButton = document.getElementById("aiButton");
const aiResult = document.getElementById("aiResult");

aiButton.addEventListener("click", async function() {
    aiResult.textContent = "Analysing your budgets...";

    try {
        const response = await fetch("http://127.0.0.1:5004/ai-insights");
        const data = await response.json();