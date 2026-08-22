const API_URL = "http://127.0.0.1:5001/transactions";

const form = document.getElementById("transactionForm");
const table = document.getElementById("transactionTable");

let editingId = null;

async function loadTransactions() {
    const response = await fetch(API_URL);
    const transactions = await response.json();

    table.innerHTML = "";

    transactions.forEach(transaction => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${transaction.type}</td>
            <td>${transaction.category}</td>
            <td>$${Number(transaction.amount).toFixed(2)}</td>
            <td>${transaction.date}</td>
            <td>${transaction.description || ""}</td>
            <td>
                <button onclick="editTransaction(${transaction.id})">Edit</button>
                <button onclick="deleteTransaction(${transaction.id})">Delete</button>
            </td>
        `;

        table.appendChild(row);
    });
}

form.addEventListener("submit", async function(event) {
    event.preventDefault();

    const transaction = {
        type: document.getElementById("type").value,
        category: document.getElementById("category").value,
        amount: Number(document.getElementById("amount").value),
        date: document.getElementById("date").value,
        description: document.getElementById("description").value
    };

    if (editingId === null) {
        await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(transaction)
        });
    } else {
        await fetch(`${API_URL}/${editingId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(transaction)
        });

        editingId = null;
        document.querySelector("button[type='submit']").textContent =
            "Add Transaction";
    }

    form.reset();
    loadTransactions();
});

async function editTransaction(id) {
    const response = await fetch(`${API_URL}/${id}`);
    const transaction = await response.json();

    document.getElementById("type").value = transaction.type;
    document.getElementById("category").value = transaction.category;
    document.getElementById("amount").value = transaction.amount;
    document.getElementById("date").value = transaction.date;
    document.getElementById("description").value =
        transaction.description || "";

    editingId = id;

    document.querySelector("button[type='submit']").textContent =
        "Update Transaction";
}

async function deleteTransaction(id) {
    await fetch(`${API_URL}/${id}`, {
        method: "DELETE"
    });

    loadTransactions();
}

loadTransactions();

const aiButton = document.getElementById("aiButton");
const aiResult = document.getElementById("aiResult");

aiButton.addEventListener("click", async function() {
    aiResult.textContent = "Analysing your transactions...";

    try {
        const response = await fetch("http://127.0.0.1:5001/ai-insights");
        const data = await response.json();

        if (data.insight) {
            aiResult.textContent = data.insight;
        } else {
            aiResult.textContent = "AI insight could not be generated.";
        }
    } catch (error) {
        aiResult.textContent = "Could not connect to the AI service.";
    }
});