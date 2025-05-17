# Israel Vehicle Data MCP

A FastMCP server providing tools to access the Israeli government's vehicle registration data API (data.gov.il). This MCP allows you to query vehicle information programmatically.

## Features

*   **Get Vehicle by Plate (`get_vehicle_by_plate`)**: Fetch detailed information for a specific vehicle using its license plate number.
*   **Vehicle Info Resource (`vehicles://{license_plate}`)**: Access vehicle details as an MCP resource.

## Prerequisites

*   Python 3.8+
*   pip (Python package installer)

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone git@github.com:LeonMelamud/car_plate_israel.git
    cd car_plate_israel
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    ```
    *   On macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```
    *   On Windows:
        ```bash
        .venv\Scripts\activate
        ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the MCP Server

The MCP server can be run directly using its STDIN/STDOUT transport, which is useful for local development or integration with tools that can manage stdio-based processes.

To start the server:
```bash
python mcp_server.py
```
This will make the MCP tools available via the `fastmcp.cli` or other MCP clients configured to use stdio.

## Using with Cursor or Claude Desktop

You can integrate this MCP server with AI assistants like Cursor or Claude Desktop that support custom MCP tool providers.

1.  **Ensure the MCP server can be started by the assistant.** For local usage, the assistant will typically run the `mcp_server.py` script.
2.  **Add as a Tool Provider:**
    *   In your AI assistant's settings for adding new tools or MCPs, you'll typically provide a way to invoke the server.
    *   For `stdio` transport, you would specify the command to run the server. This often involves providing the full path to your Python interpreter within the virtual environment and the `mcp_server.py` script.
        Example URI format for `stdio`: `stdio:/path/to/your/.venv/bin/python /path/to/your/car_plate_israel/mcp_server.py`
        (Adjust paths according to your actual setup).
    *   Alternatively, if you were to modify `mcp_server.py` to run as a persistent HTTP server, you would provide its HTTP endpoint.

3.  **Available Tools (and Resources):**
    Once configured, the AI assistant should be able to list and use the following (the prefix `israel-vehicle-data` is derived from the MCP name):
    *   Tool: `israel-vehicle-data.get_vehicle_by_plate`
        *   Args: `mispar_rechev: str` (license plate number)
        *   Returns: Vehicle details or an error.
    *   Resource: `israel-vehicle-data.vehicles://{license_plate}`
        *   Accessing this resource with a specific license plate will provide vehicle details.

## Development

The core logic is in `mcp_server.py`. Tests (if any) would typically be in a separate file like `test.py`.

## Dependencies

*   `fastmcp`: For creating the MCP server and tools.
*   `httpx`: For making asynchronous HTTP requests to the data.gov.il API.

## Future Development

The following tools are defined in `mcp_server.py` but are currently not enabled (their `@mcp.tool` decorators are commented out). They represent potential future enhancements:

*   **`search_vehicles`**: This tool is intended to provide more comprehensive search functionality for vehicles, potentially including filters for manufacturer (`tozeret_nm`) and year of manufacture (`shnat_yitzur`) that were previously removed due to type compatibility issues with the MCP call.
*   **`list_available_licenses`**: This tool would provide a direct way to list all available licenses from the CKAN API, which could be useful for understanding data usage rights across different datasets.
*   **`get_vehicle_dataset_license`**: This tool aims to fetch the specific license details for the vehicle dataset used by this MCP.

Re-enabling these tools would involve uncommenting their `@mcp.tool` decorators and ensuring their parameters and return types are fully compatible with the MCP client.

## Description

This project provides an MCP server and REST API that accesses the Israeli government's vehicle database through the data.gov.il CKAN API. It allows retrieval of specific vehicle information by license plate number and searching for vehicles based on various criteria.

## Data Source

The data is sourced from the Israeli government's data portal:
- Dataset URL: https://data.gov.il/dataset/private-and-commercial-vehicles/resource/053cea08-09bc-40ec-8f7a-156f0677aff3
- Resource ID: `053cea08-09bc-40ec-8f7a-156f0677aff3`

The dataset includes information such as:
- `mispar_rechev`: License plate number
- `tozeret_nm`: Manufacturer name
- `degem_nm`: Model name
- `shnat_yitzur`: Year of manufacture
- And more...

## Installation

### Prerequisites

- Python 3.10+
- uv (Python package manager)

### Setup

1. Clone this repository
2. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate
uv pip install fastmcp fastapi httpx uvicorn
```

## Implementation

The project is implemented using FastMCP 2.0, following the best practices from [FastMCP documentation](https://github.com/jlowin/fastmcp).

### MCP Server (`mcp_server.py`)

- Uses the standard FastMCP server architecture
- Implements a resource with URI template: `vehicles://{mispar_rechev}`
- Provides a search tool: `search_vehicles_tool`
- Uses the streamable-http transport for the MCP server

### FastAPI Integration (`fastapi_app.py`)

- Creates a FastAPI application that exposes REST endpoints
- Properly integrates with the MCP server using FastMCP's integration methods
- Provides OpenAPI documentation at `/docs`

## Usage

### Running the MCP Server Only

```bash
python mcp_server.py
```

The MCP server will be available at http://127.0.0.1:8000/mcp using the streamable-http transport.

### Running the FastAPI Application

```bash
python fastapi_app.py
```

The FastAPI application will be available at `http://localhost:8000` with the MCP server integrated at `/mcp`.

### API Endpoints

- **GET /** - Root endpoint with API information
- **GET /vehicle/{mispar_rechev}** - Get information about a specific vehicle by license plate number
- **GET /vehicles/search** - Search for vehicles based on various criteria
- **MCP Server** - Available at `/mcp`
- **API Documentation** - Available at `/docs`

## MCP Resources and Tools

The MCP server provides the following:

### Resources

- `vehicles://{mispar_rechev}`: Provides information about a specific vehicle when given its license plate number.

### Tools

- `search_vehicles_tool`: Allows searching for vehicles based on various criteria (manufacturer, model, year, etc.)

## Using with Cursor

The MCP server can be integrated with Cursor using the `update_mcp_config.py` script, which adds it to the Cursor MCP configuration file.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Data provided by the Israeli government's data portal (data.gov.il)
- Built with FastMCP 2.0 and FastAPI 