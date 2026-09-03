const API_URL = "http://127.0.0.1:5003";

const state = {
    goals: [],
    goalId: null,
    editGoalId: null,
    editContributionId: null,
    contributions: []
};


function getElement(selector) {
    return document.querySelector(selector);
}


function money(value) {
    const number = Number(value) || 0;

    return new Intl.NumberFormat("en-AU", {
        style: "currency",
        currency: "AUD"
    }).format(number);
}


function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";

    return div.innerHTML;
}


function validDate(value) {
    const datePattern = /^(\d{2})-(\d{2})-(\d{4})$/;
    const match = datePattern.exec(value);

    if (!match) {
        return false;
    }

    const day = Number(match[1]);
    const month = Number(match[2]);
    const year = Number(match[3]);

    const date = new Date(year, month - 1, day);

    return (
        date.getFullYear() === year &&
        date.getMonth() === month - 1 &&
        date.getDate() === day
    );
}


function positive(value, label) {
    const number = Number(value);

    if (!Number.isFinite(number) || number <= 0) {
        throw new Error(
            `${label} must be a number greater than zero.`
        );
    }

    return number;
}


async function call(path, options = {}) {
    const headers = {
        ...options.headers
    };

    if (options.body) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(API_URL + path, {
        ...options,
        headers: headers
    });

    const data = await response.json().catch(function () {
        return {
            error: "Invalid server response."
        };
    });

    if (!response.ok) {
        throw new Error(
            data.error || `Request failed (${response.status}).`
        );
    }

    return data;
}


function notify(text, error = false) {
    const message = getElement("#message");

    message.textContent = text;

    if (error) {
        message.className = "notice error";
    } else {
        message.className = "notice online";
    }

    clearTimeout(notify.timer);

    notify.timer = setTimeout(function () {
        message.classList.add("hidden");
    }, 3500);
}


function progress(goal) {
    const targetAmount = Number(goal.target_amount);
    const currentAmount = Number(goal.current_amount);

    if (targetAmount <= 0) {
        return 0;
    }

    const percentage = (currentAmount / targetAmount) * 100;

    return Math.min(percentage, 100);
}


function renderGoals() {
    const goalsBody = getElement("#goals-body");

    if (state.goals.length === 0) {
        goalsBody.innerHTML = `
            <tr>
                <td colspan="6">
                    No savings goals have been added yet.
                </td>
            </tr>
        `;

        return;
    }

    const rows = state.goals.map(function (goal) {
        const percentage = progress(goal).toFixed(1);

        return `
            <tr>
                <td>${escapeHtml(goal.goal_name)}</td>
                <td>${money(goal.current_amount)}</td>
                <td>${money(goal.target_amount)}</td>
                <td>${percentage}%</td>
                <td>${escapeHtml(goal.target_date)}</td>

                <td class="table-actions">
                    <button
                        type="button"
                        data-act="view"
                        data-id="${goal.id}"
                    >
                        View
                    </button>

                    <button
                        type="button"
                        class="secondary"
                        data-act="edit"
                        data-id="${goal.id}"
                    >
                        Edit
                    </button>

                    <button
                        type="button"
                        class="danger"
                        data-act="delete"
                        data-id="${goal.id}"
                    >
                        Delete
                    </button>
                </td>
            </tr>
        `;
    });

    goalsBody.innerHTML = rows.join("");
}


function renderDetail() {
    const goal = state.goals.find(function (item) {
        return item.id === state.goalId;
    });

    const detailSection = getElement("#detail");

    if (!goal) {
        detailSection.classList.add("hidden");
        return;
    }

    detailSection.classList.remove("hidden");

    getElement("#detail-name").textContent = goal.goal_name;

    getElement("#detail-summary").textContent =
        `${money(goal.current_amount)} of ` +
        `${money(goal.target_amount)} saved ` +
        `(${progress(goal).toFixed(1)}%).`;

    const contributionsBody =
        getElement("#contributions-body");

    if (state.contributions.length === 0) {
        contributionsBody.innerHTML = `
            <tr>
                <td colspan="3">
                    No contributions found.
                </td>
            </tr>
        `;

        return;
    }

    const rows = state.contributions.map(function (contribution) {
        return `
            <tr>
                <td>${money(contribution.amount)}</td>

                <td>
                    ${escapeHtml(contribution.contribution_date)}
                </td>

                <td class="table-actions">
                    <button
                        type="button"
                        class="secondary"
                        data-cact="edit"
                        data-id="${contribution.id}"
                    >
                        Edit
                    </button>

                    <button
                        type="button"
                        class="danger"
                        data-cact="delete"
                        data-id="${contribution.id}"
                    >
                        Delete
                    </button>
                </td>
            </tr>
        `;
    });

    contributionsBody.innerHTML = rows.join("");
}


async function loadGoals() {
  try {
      state.goals = await call("/goals");

      const status = getElement("#status");
      const goalsMessage = getElement("#goals-message");
      const goalsTable = getElement("#goals-table");

      status.textContent = "Backend connected";
      status.className = "notice online";

      goalsMessage.textContent = "";
      goalsTable.classList.remove("hidden");

      renderGoals();
      renderDetail();
  } catch (error) {
      const status = getElement("#status");

      status.textContent = "Backend unavailable on port 5003";
      status.className = "notice error";

      getElement("#goals-message").textContent =
          error.message;
  }
}


async function selectGoal(id) {
    state.goalId = id;

    state.contributions = await call(
        `/goals/${id}/contributions`
    );

    renderDetail();
}


function resetGoal() {
    state.editGoalId = null;

    getElement("#goal-form").reset();

    getElement("#goal-form-title").textContent =
        "Add a savings goal";

    getElement("#goal-save").textContent =
        "Add goal";

    getElement("#goal-cancel").classList.add("hidden");
}


function resetContribution() {
    state.editContributionId = null;

    getElement("#contribution-form").reset();

    getElement("#contribution-form-title").textContent =
        "Add a contribution";

    getElement("#contribution-save").textContent =
        "Add contribution";

    getElement("#contribution-cancel").classList.add(
        "hidden"
    );
}


getElement("#goal-form").addEventListener(
    "submit",
    async function (event) {
        event.preventDefault();

        try {
            const name =
                getElement("#goal-name").value.trim();

            const amount = positive(
                getElement("#goal-target").value,
                "Target amount"
            );

            const date =
                getElement("#goal-date").value.trim();

            if (!name) {
                throw new Error(
                    "Goal name is required."
                );
            }

            if (!validDate(date)) {
                throw new Error(
                    "Use a real date in DD-MM-YYYY format."
                );
            }

            const editing =
                state.editGoalId !== null;

            let path = "/goals";
            let method = "POST";

            if (editing) {
                path = `/goals/${state.editGoalId}`;
                method = "PUT";
            }

            await call(path, {
                method: method,
                body: JSON.stringify({
                    goal_name: name,
                    target_amount: amount,
                    target_date: date
                })
            });

            resetGoal();
            await loadGoals();

            if (editing) {
                notify("Goal updated.");
            } else {
                notify("Goal added.");
            }
        } catch (error) {
            notify(error.message, true);
        }
    }
);


getElement("#goals-body").addEventListener(
    "click",
    async function (event) {
        const button =
            event.target.closest("[data-act]");

        if (!button) {
            return;
        }

        const id = Number(button.dataset.id);

        const goal = state.goals.find(function (item) {
            return item.id === id;
        });

        if (!goal) {
            notify("Goal not found.", true);
            return;
        }

        try {
            if (button.dataset.act === "view") {
                await selectGoal(id);
            }

            if (button.dataset.act === "edit") {
                state.editGoalId = id;

                getElement("#goal-name").value =
                    goal.goal_name;

                getElement("#goal-target").value =
                    goal.target_amount;

                getElement("#goal-date").value =
                    goal.target_date;

                getElement("#goal-form-title").textContent =
                    "Edit savings goal";

                getElement("#goal-save").textContent =
                    "Save changes";

                getElement("#goal-cancel").classList.remove(
                    "hidden"
                );
            }

            if (button.dataset.act === "delete") {
                const confirmed = confirm(
                    `Delete ${goal.goal_name}?`
                );

                if (!confirmed) {
                    return;
                }

                await call(`/goals/${id}`, {
                    method: "DELETE"
                });

                if (state.goalId === id) {
                    state.goalId = null;
                    state.contributions = [];
                }

                await loadGoals();
                notify("Goal deleted.");
            }
        } catch (error) {
            notify(error.message, true);
        }
    }
);


getElement("#contribution-form").addEventListener(
    "submit",
    async function (event) {
        event.preventDefault();

        try {
            if (state.goalId === null) {
                throw new Error(
                    "Select a savings goal first."
                );
            }

            const amount = positive(
                getElement("#contribution-amount").value,
                "Contribution amount"
            );

            const date =
                getElement("#contribution-date").value.trim();

            if (!validDate(date)) {
                throw new Error(
                    "Use a real date in DD-MM-YYYY format."
                );
            }

            const editing =
                state.editContributionId !== null;

            let path =
                `/goals/${state.goalId}/contributions`;

            let method = "POST";

            if (editing) {
                path =
                    `/contributions/${state.editContributionId}`;

                method = "PUT";
            }

            await call(path, {
                method: method,
                body: JSON.stringify({
                    amount: amount,
                    contribution_date: date
                })
            });

            resetContribution();

            await loadGoals();
            await selectGoal(state.goalId);

            if (editing) {
                notify("Contribution updated.");
            } else {
                notify("Contribution added.");
            }
        } catch (error) {
            notify(error.message, true);
        }
    }
);


getElement("#contributions-body").addEventListener(
    "click",
    async function (event) {
        const button =
            event.target.closest("[data-cact]");

        if (!button) {
            return;
        }

        const id = Number(button.dataset.id);

        const contribution =
            state.contributions.find(function (item) {
                return item.id === id;
            });

        if (!contribution) {
            notify("Contribution not found.", true);
            return;
        }

        try {
            if (button.dataset.cact === "edit") {
                state.editContributionId = id;

                getElement("#contribution-amount").value =
                    contribution.amount;

                getElement("#contribution-date").value =
                    contribution.contribution_date;

                getElement(
                    "#contribution-form-title"
                ).textContent = "Edit contribution";

                getElement(
                    "#contribution-save"
                ).textContent = "Save changes";

                getElement(
                    "#contribution-cancel"
                ).classList.remove("hidden");
            }

            if (button.dataset.cact === "delete") {
                const confirmed = confirm(
                    "Delete this contribution?"
                );

                if (!confirmed) {
                    return;
                }

                await call(`/contributions/${id}`, {
                    method: "DELETE"
                });

                await loadGoals();
                await selectGoal(state.goalId);

                notify("Contribution deleted.");
            }
        } catch (error) {
            notify(error.message, true);
        }
    }
);


// AI insights: reset duplicate-name choices when the name changes.
getElement("#ai-goal-name").addEventListener(
    "input",
    function () {
        getElement("#ai-goal-choice").replaceChildren();
        getElement("#ai-choice-container").classList.add("hidden");
    }
);


// AI insights: overall by default, or a specific named goal.
getElement("#ai-button").addEventListener(
    "click",
    async function () {
        const button = getElement("#ai-button");
        const result = getElement("#ai-result");
        const nameInput = getElement("#ai-goal-name");
        const questionInput = getElement("#ai-question");
        const choice = getElement("#ai-goal-choice");
        const choiceContainer = getElement("#ai-choice-container");

        const choosingGoal =
            !choiceContainer.classList.contains("hidden");

        if (choosingGoal && !choice.value) {
            result.textContent = "Please choose one of the matching goals.";
            result.classList.remove("hidden");
            return;
        }

        const payload = {
            goal_name: nameInput.value.trim(),
            input: questionInput.value.trim()
        };

        if (choosingGoal) {
            payload.goal_id = Number(choice.value);
        }

        button.disabled = true;
        nameInput.disabled = true;
        questionInput.disabled = true;
        choice.disabled = true;

        result.textContent = "Generating insight...";
        result.classList.remove("hidden");

        try {
            const response = await fetch(
                `${API_URL}/ai-insights`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                }
            );

            const data = await response.json();

            if (
                response.status === 409 &&
                Array.isArray(data.matches)
            ) {
                choice.replaceChildren();

                const placeholder = document.createElement("option");
                placeholder.value = "";
                placeholder.textContent = "Choose a goal";
                choice.appendChild(placeholder);

                data.matches.forEach(function (goal) {
                    const option = document.createElement("option");

                    option.value = goal.id;
                    option.textContent =
                        `${goal.goal_name} - ${money(goal.target_amount)} - ` +
                        `${goal.target_date} - ID ${goal.id}`;

                    choice.appendChild(option);
                });

                choiceContainer.classList.remove("hidden");
                result.textContent = data.error;
                return;
            }

            if (!response.ok) {
                throw new Error(
                    data.error || "Could not generate insights."
                );
            }

            if (
                typeof data.insight !== "string" ||
                !data.insight.trim()
            ) {
                throw new Error("AI returned no insight.");
            }

            const heading = data.scope === "overall"
                ? "Overall savings insights"
                : `Insights for ${data.goal_name}`;

            result.textContent = `${heading}\n\n${data.insight}`;
        } catch (error) {
            result.textContent = error.message;
        } finally {
            button.disabled = false;
            nameInput.disabled = false;
            questionInput.disabled = false;
            choice.disabled = false;
        }
    }
);


getElement("#refresh").addEventListener(
    "click",
    function () {
        loadGoals();
    }
);


getElement("#goal-cancel").addEventListener(
    "click",
    function () {
        resetGoal();
    }
);


getElement("#contribution-cancel").addEventListener(
    "click",
    function () {
        resetContribution();
    }
);


getElement("#detail-close").addEventListener(
    "click",
    function () {
        state.goalId = null;
        state.contributions = [];

        resetContribution();
        renderDetail();
    }
);


loadGoals();