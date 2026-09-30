from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
import json


mcp = MCPServer("AI Personal Finance MCP Server")


@mcp.tool()
def calculate_income_expense_summary(
    total_income: float,
    total_expenses: float
) -> dict:
    """
    Calculate an income and expense summary.

    This tool only performs deterministic calculations
    using the supplied income and expense totals.
    """

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


@mcp.tool()
def analyze_budget_summary(summary_json: str) -> dict:
    """Return key budget allocation metrics from a precomputed summary."""
    try:
        summary = json.loads(summary_json)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError("Budget summary must be valid JSON.") from error

    if not isinstance(summary, dict):
        raise ValueError("Budget summary must be a JSON object.")

    top_categories = summary.get("top_categories_by_amount", [])
    top_three_share_pct = sum(
        float(category.get("share_pct", 0) or 0)
        for category in top_categories[:3]
    )

    return {
        "budget_count": int(summary.get("budget_count", 0) or 0),
        "total_budget": round(float(summary.get("total_budget", 0) or 0), 2),
        "average_category_amount": round(
            float(summary.get("average_category_amount", 0) or 0),
            2
        ),
        "largest_category": summary.get("largest_category"),
        "smallest_category": summary.get("smallest_category"),
        "top_categories_by_amount": top_categories,
        "top_three_share_pct": round(top_three_share_pct, 2),
        "potential_trim_candidates": summary.get(
            "potential_trim_candidates", []
        )
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