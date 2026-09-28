import asyncio
from unittest import result
from mcp import Client


async def main():
    async with Client("http://localhost:7001/mcp") as client:

        tools = await client.list_tools()

        print("Available MCP tools:")
        for tool in tools.tools:
            print("-", tool.name)

        result = await client.call_tool(
            "calculate_income_expense_summary",
            {
                "total_income": 1000,
                "total_expenses": 400
            }
        )

        print("\nMCP TOOL RESULT:")
        print("Error:", result.is_error)
        print("Content:", result.content)
        print("Structured content:", result.structured_content)


if __name__ == "__main__":
    asyncio.run(main())