import argparse
import asyncio
import json
import requests

from mcp import Client


MCP_URL = "http://localhost:7001/mcp"
RAG_URL = "http://localhost:7002/rag"


# ----------------------------------
# MCP validation mode
# ----------------------------------

async def validate_mcp():

    print("=" * 60)
    print("SHARED AGENTIC LOOP - MCP VALIDATION MODE")
    print("=" * 60)

    print("\nPLAN")
    print(
        "Validate the shared MCP server, confirm the registered "
        "tool is available, and verify that it returns a valid result."
    )

    print("\nACT")
    print("Connecting to shared MCP server...")

    try:

        async with Client(MCP_URL) as client:

            tools = await client.list_tools()

            tool_names = [
                tool.name
                for tool in tools.tools
            ]

            print("Registered MCP tools:")
            for tool_name in tool_names:
                print(f"- {tool_name}")

            required_tool = (
                "calculate_income_expense_summary"
            )

            if required_tool not in tool_names:
                raise Exception(
                    f"Required MCP tool '{required_tool}' "
                    "was not found."
                )

            result = await client.call_tool(
                required_tool,
                {
                    "total_income": 1000,
                    "total_expenses": 400
                }
            )

            if result.is_error:
                raise Exception(
                    "MCP tool returned an error."
                )

            if not result.content:
                raise Exception(
                    "MCP tool returned no content."
                )

            result_text = (
                result.content[0].text
            )

            result_data = json.loads(
                result_text
            )

            print("\nOBSERVE")
            print("MCP connection: PASS")
            print(
                "Tool found:",
                required_tool
            )
            print(
                "Tool result:",
                json.dumps(
                    result_data,
                    indent=2
                )
            )

            expected_fields = [
                "total_income",
                "total_expenses",
                "net_balance",
                "expense_percentage",
                "status"
            ]

            missing_fields = [
                field
                for field in expected_fields
                if field not in result_data
            ]

            print("\nADAPT")

            if missing_fields:

                print(
                    "Validation result: FAIL"
                )

                print(
                    "Improvement required: "
                    "MCP output is missing fields:"
                )

                for field in missing_fields:
                    print(f"- {field}")

                return False

            print(
                "Validation result: PASS"
            )

            print(
                "The MCP server returned a valid "
                "structured income and expense summary."
            )

            print(
                "No MCP changes are required "
                "for this validation."
            )

            return True

    except Exception as error:

        print("\nOBSERVE")
        print("MCP connection: FAIL")
        print("Error:", str(error))

        print("\nADAPT")
        print(
            "Check that the shared MCP server "
            "is running on port 7001 and that "
            "the required tool is registered."
        )

        return False


# ----------------------------------
# RAG validation mode
# ----------------------------------

def validate_rag():

    print("=" * 60)
    print("SHARED AGENTIC LOOP - RAG VALIDATION MODE")
    print("=" * 60)

    print("\nPLAN")
    print(
        "Validate the shared RAG server using one supported "
        "question and one unsupported question."
    )

    print("\nACT")
    print(
        "Sending grounded and insufficient-context "
        "queries to the shared RAG server..."
    )

    supported_question = (
        "How is remaining money calculated?"
    )

    unsupported_question = (
        "Who won the FIFA World Cup?"
    )

    try:

        # ----------------------------------
        # Supported question
        # ----------------------------------

        supported_response = requests.post(
            RAG_URL,
            json={
                "query":
                    supported_question
            },
            timeout=120
        )

        supported_response.raise_for_status()

        supported_data = (
            supported_response.json()
        )


        # ----------------------------------
        # Unsupported question
        # ----------------------------------

        unsupported_response = requests.post(
            RAG_URL,
            json={
                "query":
                    unsupported_question
            },
            timeout=120
        )

        unsupported_response.raise_for_status()

        unsupported_data = (
            unsupported_response.json()
        )


        print("\nOBSERVE")

        print("\nSupported RAG question:")
        print(supported_question)

        print(
            "Answer:",
            supported_data.get(
                "answer"
            )
        )

        print(
            "Source:",
            supported_data.get(
                "sources"
            )
        )

        print(
            "Confidence:",
            supported_data.get(
                "confidence"
            )
        )

        print(
            "Grounded:",
            supported_data.get(
                "grounded"
            )
        )


        print("\nUnsupported RAG question:")
        print(unsupported_question)

        print(
            "Answer:",
            unsupported_data.get(
                "answer"
            )
        )

        print(
            "Confidence:",
            unsupported_data.get(
                "confidence"
            )
        )

        print(
            "Grounded:",
            unsupported_data.get(
                "grounded"
            )
        )


        # ----------------------------------
        # Validate supported response
        # ----------------------------------

        supported_valid = (
            supported_data.get(
                "grounded"
            ) is True
            and bool(
                supported_data.get(
                    "sources"
                )
            )
            and supported_data.get(
                "confidence"
            ) in [
                "High",
                "Medium",
                "Low"
            ]
        )


        # ----------------------------------
        # Validate insufficient context
        # ----------------------------------

        unsupported_valid = (
            unsupported_data.get(
                "grounded"
            ) is False
            and unsupported_data.get(
                "confidence"
            ) == "Insufficient"
        )


        print("\nADAPT")

        if (
            supported_valid
            and unsupported_valid
        ):

            print(
                "Validation result: PASS"
            )

            print(
                "The RAG server returned a grounded "
                "answer with a source and confidence "
                "category."
            )

            print(
                "The unsupported question correctly "
                "returned insufficient context."
            )

            print(
                "No RAG changes are required "
                "for this validation."
            )

            return True


        print(
            "Validation result: FAIL"
        )

        if not supported_valid:

            print(
                "Improvement required: "
                "Grounded responses must include "
                "a source, confidence category "
                "and grounded=True."
            )

        if not unsupported_valid:

            print(
                "Improvement required: "
                "Unsupported questions must return "
                "insufficient context and "
                "grounded=False."
            )

        return False


    except requests.exceptions.RequestException as error:

        print("\nOBSERVE")
        print("RAG connection: FAIL")
        print("Error:", str(error))

        print("\nADAPT")
        print(
            "Check that the shared RAG server "
            "is running on port 7002 and that "
            "local Ollama is available."
        )

        return False


# ----------------------------------
# Main
# ----------------------------------

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Shared Release 1 Agentic Validation Loop"
        )
    )

    parser.add_argument(
        "--mode",
        choices=[
            "mcp",
            "rag",
            "both"
        ],
        required=True,
        help=(
            "Choose MCP validation, "
            "RAG validation, or both."
        )
    )

    args = parser.parse_args()


    if args.mode == "mcp":

        passed = asyncio.run(
            validate_mcp()
        )


    elif args.mode == "rag":

        passed = validate_rag()


    else:

        mcp_passed = asyncio.run(
            validate_mcp()
        )

        print("\n")

        rag_passed = validate_rag()

        passed = (
            mcp_passed
            and rag_passed
        )


    print("\n" + "=" * 60)

    if passed:

        print(
            "AGENTIC VALIDATION COMPLETE - PASS"
        )

    else:

        print(
            "AGENTIC VALIDATION COMPLETE - FAIL"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()