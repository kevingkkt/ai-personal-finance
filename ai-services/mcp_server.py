from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings


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