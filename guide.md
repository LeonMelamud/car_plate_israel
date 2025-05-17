### Project Brief: Israel Vehicle Data MCP

*   **Purpose:** This project creates an MCP (Multi-Capability Program) server that exposes vehicle data from Israel's public government dataset (`data.gov.il`).
*   **Technology:** It uses the `FastMCP` library to define and serve tools.
*   **Core Functionality:**
    *   It fetches vehicle data from the official API endpoint: `https://data.gov.il/api/3/action/datastore_search`.
    *   It provides two primary tools for users (or other AI agents) to interact with this data:
        1.  `search_vehicles`: Allows searching for vehicles based on criteria such as manufacturer name (`tozeret_nm`), model name (`degem_nm`), year of manufacture (`shnat_yitzur`), or license plate number (`mispar_rechev`). It supports pagination (`limit`, `offset`).
        2.  `get_vehicle_by_plate`: Retrieves detailed information for a specific vehicle given its license plate number (`mispar_rechev`).
*   **Structure (`mcp_server.py`):**
    *   Initializes a `FastMCP` instance.
    *   Helper functions (`fetch_vehicle_by_id`, `search_vehicles`) handle the actual logic of querying the external API using `httpx`.
    *   Tool functions (`search_vehicles_tool`, `get_vehicle_by_plate_tool`) are decorated with `@mcp.tool(name="...")` to register them with `FastMCP`. These functions wrap the helper functions and include error handling.
    *   A `get_mcp_application()` function returns the configured `FastMCP` instance.
    *   The `main_stdio()` function runs the MCP server using standard input/output when the script is executed directly.

### In-Memory Testing Pattern (`test.py`)

This setup allows you to test your MCP tools directly in memory without needing to run a separate server process or deal with network/stdio communication complexities. It's faster and ideal for unit/integration tests of your tool logic.

Here's how it was created, which you can adapt for future projects:

1.  **Isolate MCP Application Access:**
    *   In your main server file (`mcp_server.py` in this case), ensure you have a function like `get_mcp_application()`. This function should return the `FastMCP` instance to which all your tools are registered (e.g., the global `mcp` variable that you decorate your tools with).

2.  **Create a Test File (e.g., `test.py`):**
    *   **Import Necessities:**
        ```python
        import asyncio
        from typing import Dict, Any
        import json
        # Import the function to get your MCP app
        from mcp_server import get_mcp_application
        # Import the FastMCP client
        from fastmcp import Client as FastMCPClient # Or the correct import path
        ```

3.  **Main Test Runner (`async def main()`):**
    *   Get your MCP application instance: `mcp_app = get_mcp_application()`
    *   **Instantiate `FastMCPClient` for In-Memory Use:** Pass the `mcp_app` instance directly to the client's constructor. This is the key for in-memory testing.
        ```python
        client = FastMCPClient(mcp_app)
        # If the client needs to be used as an async context manager:
        # async with FastMCPClient(mcp_app) as client:
        #    await run_your_tests(client)
        ```
    *   Call your individual test functions from here, passing the `client` instance.

4.  **Helper for Calling Tools (`async def call_in_memory_tool()`):**
    *   This function simplifies calling tools and processing their responses.
    *   **Parameters:** `client: FastMCPClient`, `tool_name: str`, `**tool_args`.
    *   **Invoking the tool:** Use `response = await client.call_tool(tool_name, tool_args)`. (The `FastMCP` client might have variations like `client.call(tool_name, **tool_args)` or allow direct attribute access `await client.tools.tool_name(**tool_args)` if it dynamically creates them. `call_tool` with a dictionary of arguments is a common pattern.)
    *   **Response Handling:** `FastMCP` tools often return a list containing a `Content` object (e.g., `TextContent`) whose `.text` attribute holds the JSON string. The helper should extract this, parse the JSON, and return the resulting dictionary.
    *   **Error Handling:** Include basic try-except blocks for `json.JSONDecodeError` or other client-side exceptions.

5.  **Individual Tool Test Functions (e.g., `async def test_specific_tool()`):**
    *   **Parameters:** `client: FastMCPClient`.
    *   Define various test cases (different inputs, expected outcomes, edge cases).
    *   For each test case, call your `call_in_memory_tool()` helper.
    *   Print the results and add assertions or simple print-based validations to check if the output is as expected.

6.  **Run with `asyncio`:**
    *   Use `if __name__ == "__main__": asyncio.run(main())` to execute your tests.

**Benefits of this In-Memory Approach:**

*   **Speed:** Much faster than tests that involve network or process overhead.
*   **Isolation:** Tests your tool logic directly without external dependencies like a running server process.
*   **Simplicity:** Easier to debug as it's all within the same process.
*   **CI/CD Friendly:** Great for automated testing pipelines.

By following this pattern, you can create robust tests for your `FastMCP` tools. Remember to adapt the client instantiation and tool calling method based on the specific version and features of `FastMCP` you are using.
