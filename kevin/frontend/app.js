const API_URL = "http://127.0.0.1:5001/transactions";

const form = document.getElementById("transactionForm");
const table = document.getElementById("transactionTable");

const amountInput = document.getElementById("amount");
const amountError = document.getElementById("amountError");

const dateInput = document.getElementById("date");
const dateError = document.getElementById("dateError");

const submitButton = document.getElementById("submitButton");

let editingId = null;


// ----------------------------------
// DATE FORMAT
// ----------------------------------

function convertToDisplayDate(date) {
    if (!date) {
        return "";
    }

    const parts = date.split("-");

    if (parts.length !== 3) {
        return date;
    }

    return `${parts[2]}/${parts[1]}/${parts[0]}`;
}


function convertToDatabaseDate(date) {
    const parts = date.split("/");

    if (parts.length !== 3) {
        return date;
    }

    return `${parts[2]}-${parts[1]}-${parts[0]}`;
}


// ----------------------------------
// AMOUNT VALIDATION
// ----------------------------------

function validAmount(value) {
    const number = Number(value);

    return (
        value.trim() !== "" &&
        !isNaN(number) &&
        number >= 0
    );
}


amountInput.addEventListener("input", function () {

    const value = amountInput.value.trim();

    if (value === "") {
        amountError.textContent = "";
        return;
    }

    if (!validAmount(value)) {
        amountError.textContent =
            "Please enter a valid number.";
    } else {
        amountError.textContent = "";
    }
});


// ----------------------------------
// DATE VALIDATION
// ----------------------------------

function validDate(value) {

    const pattern = /^\d{2}\/\d{2}\/\d{4}$/;

    if (!pattern.test(value)) {
        return false;
    }

    const parts = value.split("/");

    const day = Number(parts[0]);
    const month = Number(parts[1]);
    const year = Number(parts[2]);

    const testDate =
        new Date(year, month - 1, day);

    return (
        testDate.getFullYear() === year &&
        testDate.getMonth() === month - 1 &&
        testDate.getDate() === day
    );
}


// Auto change 28082026 to 28/08/2026
dateInput.addEventListener("input", function () {

    let numbers =
        dateInput.value.replace(/\D/g, "");

    numbers = numbers.substring(0, 8);

    if (numbers.length <= 2) {

        dateInput.value = numbers;

    } else if (numbers.length <= 4) {

        dateInput.value =
            numbers.substring(0, 2) +
            "/" +
            numbers.substring(2);

    } else {

        dateInput.value =
            numbers.substring(0, 2) +
            "/" +
            numbers.substring(2, 4) +
            "/" +
            numbers.substring(4);
    }

    if (
        dateInput.value.length === 10 &&
        !validDate(dateInput.value)
    ) {
        dateError.textContent =
            "Please enter a valid date.";
    } else {
        dateError.textContent = "";
    }
});


// ----------------------------------
// LOAD TRANSACTIONS
// ----------------------------------

async function loadTransactions() {

    try {

        const response = await fetch(API_URL);

        if (!response.ok) {
            throw new Error("Could not load transactions");
        }

        const transactions =
            await response.json();

        table.innerHTML = "";

        transactions.forEach(transaction => {

            const row =
                document.createElement("tr");

            row.innerHTML = `
                <td>${transaction.type}</td>
                <td>${transaction.category}</td>
                <td>$${Number(transaction.amount).toFixed(2)}</td>
                <td>${convertToDisplayDate(transaction.date)}</td>
                <td>${transaction.description || ""}</td>
                <td>
                    <button
                        type="button"
                        onclick="editTransaction(${transaction.id})">
                        Edit
                    </button>

                    <button
                        type="button"
                        onclick="deleteTransaction(${transaction.id})">
                        Delete
                    </button>
                </td>
            `;

            table.appendChild(row);
        });

    } catch (error) {

        console.error(error);
    }
}


// ----------------------------------
// ADD / UPDATE
// ----------------------------------

form.addEventListener("submit", async function (event) {

    event.preventDefault();

    amountError.textContent = "";
    dateError.textContent = "";

    const type =
        document.getElementById("type").value;

    const category =
        document.getElementById("category").value.trim();

    const amount =
        amountInput.value.trim();

    const date =
        dateInput.value.trim();

    const description =
        document.getElementById("description").value.trim();


    // Check amount
    if (!validAmount(amount)) {

        amountError.textContent =
            "Please enter a valid number.";

        return;
    }


    // Check date
    if (!validDate(date)) {

        dateError.textContent =
            "Please enter a valid date as dd/mm/yyyy.";

        return;
    }


    const transaction = {
        type: type,
        category: category,
        amount: Number(amount),
        date: convertToDatabaseDate(date),
        description: description
    };


    try {

        let response;


        // ADD
        if (editingId === null) {

            response = await fetch(API_URL, {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(transaction)
            });

        }


        // UPDATE
        else {

            response = await fetch(
                `${API_URL}/${editingId}`,
                {

                    method: "PUT",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify(transaction)
                }
            );
        }


        if (!response.ok) {

            const errorText =
                await response.text();

            console.error(errorText);

            alert("Transaction could not be saved.");

            return;
        }


        // Reset after successful add/update
        editingId = null;

        submitButton.textContent =
            "Add Transaction";

        form.reset();

        amountError.textContent = "";
        dateError.textContent = "";

        await loadTransactions();


    } catch (error) {

        console.error(error);

        alert(
            "Could not connect to the backend."
        );
    }
});


// ----------------------------------
// EDIT
// ----------------------------------

async function editTransaction(id) {

    try {

        const response =
            await fetch(`${API_URL}/${id}`);

        const transaction =
            await response.json();


        document.getElementById("type").value =
            transaction.type;

        document.getElementById("category").value =
            transaction.category;

        amountInput.value =
            transaction.amount;

        dateInput.value =
            convertToDisplayDate(
                transaction.date
            );

        document.getElementById("description").value =
            transaction.description || "";


        editingId = id;

        submitButton.textContent =
            "Update Transaction";

    } catch (error) {

        console.error(error);
    }
}


// ----------------------------------
// DELETE
// ----------------------------------

async function deleteTransaction(id) {

    try {

        const response =
            await fetch(
                `${API_URL}/${id}`,
                {
                    method: "DELETE"
                }
            );

        if (!response.ok) {
            alert(
                "Transaction could not be deleted."
            );
            return;
        }

        await loadTransactions();

    } catch (error) {

        console.error(error);
    }
}


// ----------------------------------
// AI
// ----------------------------------

const aiButton =
    document.getElementById("aiButton");

const aiResult =
    document.getElementById("aiResult");


aiButton.addEventListener(
    "click",
    async function () {

        aiResult.textContent =
            "Analysing your transactions...";

        try {

            const response =
                await fetch(
                    "http://127.0.0.1:5001/ai-insights"
                );

            const data =
                await response.json();


            if (data.insight) {

                aiResult.textContent =
                    data.insight;

            } else {

                aiResult.textContent =
                    "AI insight could not be generated.";
            }

        } catch (error) {

            aiResult.textContent =
                "Could not connect to the AI service.";
        }
    }
);

// ----------------------------------
// MCP
// ----------------------------------

const mcpButton =
    document.getElementById("mcpButton");

const mcpResult =
    document.getElementById("mcpResult");


mcpButton.addEventListener(
    "click",
    async function () {

        mcpResult.textContent =
            "Calling shared MCP server...";

        try {

            const response =
                await fetch(
                    "http://127.0.0.1:5001/mcp-income-expense-summary"
                );

            const data =
                await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error || "MCP request failed"
                );
            }

            const result =
                data.result;

            mcpResult.textContent =
                `MCP Tool: ${data.tool}\n` +
                `Total Income: $${Number(result.total_income).toFixed(2)}\n` +
                `Total Expenses: $${Number(result.total_expenses).toFixed(2)}\n` +
                `Net Balance: $${Number(result.net_balance).toFixed(2)}\n` +
                `Expense Percentage: ${Number(result.expense_percentage).toFixed(2)}%\n` +
                `Status: ${result.status}`;

        } catch (error) {

            console.error(error);

            mcpResult.textContent =
                "Could not connect to the MCP service.";
        }
    }
);

// ----------------------------------
// RAG
// ----------------------------------

const ragButton =
    document.getElementById("ragButton");

const ragQuestion =
    document.getElementById("ragQuestion");

const ragResult =
    document.getElementById("ragResult");


ragButton.addEventListener(
    "click",
    async function () {

        const question =
            ragQuestion.value.trim();

        if (!question) {
            ragResult.textContent =
                "Please enter a question.";
            return;
        }

        ragResult.textContent =
            "Searching project knowledge...";

        try {

            const response =
                await fetch(
                    "http://127.0.0.1:5001/rag-query",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body: JSON.stringify({
                            query: question
                        })
                    }
                );

            const data =
                await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error ||
                    "RAG request failed"
                );
            }

            if (data.grounded === false) {

                ragResult.textContent =
                    `${data.answer}\n` +
                    `Confidence: ${data.confidence}`;

                return;
            }

            const sources =
                data.sources.join(", ");

            ragResult.textContent =
                `Answer: ${data.answer}\n\n` +
                `Source: ${sources}\n` +
                `Confidence: ${data.confidence}`;

        } catch (error) {

            console.error(error);

            ragResult.textContent =
                "Could not connect to the RAG service.";
        }
    }
);


// Load transactions when page opens
loadTransactions();