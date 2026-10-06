import os
import requests
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import math
from typing import Annotated
from pydantic import Field

MoneyInput = Annotated[float, Field(strict=True)]
BILLS_API_URL = os.environ.get("BILLS_API_URL","http://localhost:5004")


mcp = MCPServer("AI Personal Finance MCP Server")
python .\ai-services\mcp_server.py

@mcp.tool(structured_output=True)
def calculate_income_expense_summary(
    total_income: MoneyInput,
    total_expenses: MoneyInput
) -> dict[str, object]:
    """
    Calculate an income and expense summary.

    This tool only performs deterministic calculations
    using the supplied income and expense totals.
    """

    if not math.isfinite(total_income) or not math.isfinite(total_expenses):
        raise ValueError("Income and expenses must be finite.")

    if total_income < 0:
        raise ValueError(
            "Total income cannot be negative."
        )

    if total_expenses < 0:
        raise ValueError(
            "Total expenses cannot be negative."
        )

    net_balance = total_income - total_expenses

    if total_income > 0:
        expense_percentage = (
            total_expenses / total_income
        ) * 100
    else:
        expense_percentage = 0.0

    if net_balance > 0:
        status = "Surplus"
    elif net_balance < 0:
        status = "Deficit"
    else:
        status = "Break-even"

    return {
        "tool": "calculate_income_expense_summary",
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_balance": round(net_balance, 2),
        "expense_percentage": round(
            expense_percentage,
            2
        ),
        "status": status
    }
#Luke Section
#first we get the info from here

@mcp.tool()
def get_all_bills() -> dict[str, object]:
    """
    Get all the bills data.
    """
    response = requests.get(
        f"{BILLS_API_URL}/bills",
        timeout=10
    )
    response.raise_for_status()

    return response.json()


@mcp.tool()
def get_paid_bills() -> dict[str, object]:
    """
    Get all of the paid bills.
    """
    response = requests.get(
        f"{BILLS_API_URL}/bills/paid",
        timeout=10
    )
    response.raise_for_status()

    return response.json()


@mcp.tool()
def get_unpaid_bills() -> dict[str, object]:
    """
    Get all unpaid bills  
    """
    response = requests.get(
        f"{BILLS_API_URL}/bills/unpaid",
        timeout=10
    )
    response.raise_for_status()

    return response.json()

#The actual useful tool case.
@mcp.tool()
def get_total_unpaid() -> dict[str, float]:
    """
    Go get the total number of all the bills which are unpaid.
    """
    response = requests.get(
        f"{BILLS_API_URL}/bills/unpaid",
        timeout=10
    )
    response.raise_for_status()

    bills = response.json()

    total = sum(float(bill["amount"]) for bill in bills)

    return {
        "total_unpaid": total
    }



def money_value(value, name, *, positive=False):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{name} must be a number")
    if not amount.is_finite():
        raise ValueError(f"{name} must be finite")
    if amount < 0 or (positive and amount == 0):
        raise ValueError(f"{name} is outside the allowed range")
    if amount > Decimal("1000000000"):
        raise ValueError(f"{name} exceeds the supported limit")
    if amount != amount.quantize(Decimal("0.01")):
        raise ValueError(f"{name} must have at most two decimal places")
    return amount


def parse_goal_date(value, name):
    if not isinstance(value, str):
        raise ValueError(f"{name} must use DD-MM-YYYY")
    try:
        parsed = datetime.strptime(value, "%d-%m-%Y").date()
    except ValueError:
        raise ValueError(f"{name} must be a real DD-MM-YYYY date")
    if parsed.strftime("%d-%m-%Y") != value:
        raise ValueError(f"{name} must use DD-MM-YYYY")
    return parsed


@mcp.tool(structured_output=True)
def calculate_savings_goal_progress(
    target_amount: MoneyInput,
    current_amount: MoneyInput,
    target_date: str,
    reference_date: str,
) -> dict[str, object]:
    """Read-only calculation from supplied amounts and DD-MM-YYYY dates.

    No database, filesystem, shell or external URL access. Money must be
    finite, at most two decimal places and at most one billion dollars.
    Progress can exceed 100%; completed goals take precedence over overdue.
    """
    target = money_value(target_amount, "target_amount", positive=True)
    current = money_value(current_amount, "current_amount")
    deadline = parse_goal_date(target_date, "target_date")
    today = parse_goal_date(reference_date, "reference_date")
    remaining = max(target - current, Decimal("0"))
    days = (deadline - today).days
    percentage = (current / target * 100).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    status = ("completed" if remaining == 0 else "overdue" if days < 0
              else "due_today" if days == 0 else "active")
    return {
        "tool": "calculate_savings_goal_progress",
        "target_amount": float(target), "current_amount": float(current),
        "remaining_amount": float(remaining),
        "progress_percentage": float(percentage),
        "target_date": target_date, "reference_date": reference_date,
        "days_remaining": days, "status": status,
    }


if __name__ == "__main__":
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "localhost:*",
            "127.0.0.1:*",
            "host.docker.internal:*",
        ],
        allowed_origins=[
            "http://localhost:*",
            "http://127.0.0.1:*",
        ],
    )

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=7001,
        stateless_http=True,
        json_response=True,
        transport_security=security,
    )