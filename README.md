# Israel Vehicle Data MCP Server

A clean and focused Model Context Protocol (MCP) server that provides access to Israeli government vehicle registration data.

## Features

- 🚗 **Vehicle Lookup**: Get complete vehicle information by license plate
- 🔍 **Advanced Search**: Search by manufacturer, model, or license plate
- 📊 **Dataset Licensing**: Access licensing information for the data
- ⚡ **High Performance**: Built with FastMCP and modern Python tooling
- 🐳 **Production Ready**: Docker containerized with uv package management
- 🔒 **Secure**: HTTPS deployment ready with proper security practices

## Available Tools (4)

1. **`get_vehicle_by_plate`** - Look up any Israeli vehicle by license plate
2. **`search_vehicles`** - Search vehicles by manufacturer, model, or license plate
3. **`get_vehicle_dataset_license`** - Get dataset license information
4. **`list_available_licenses`** - List all available data licenses

## Available Prompts (4)

1. **`get_vehicle_info`** - Complete vehicle information by license plate
2. **`search_vehicles`** - Search vehicles by manufacturer, model, or license plate
3. **`get_dataset_license`** - Dataset license information
4. **`list_data_licenses`** - Overview of all data licenses

## MCP Client Prompt Support

This server provides both **tools** and **prompts**. However, not all MCP clients support prompts. Here's the compatibility matrix:

### ✅ **Clients that SUPPORT MCP Prompts:**

| Client | Prompt Support | Tools | Resources | Notes |
|--------|---------------|-------|-----------|-------|
| **Claude Desktop App** | ✅ | ✅ | ✅ | Full MCP support - **Recommended** |
| **Claude.ai** | ✅ | ✅ | ✅ | Web version with full support |
| **Claude Code** | ✅ | ✅ | ❌ | Coding-focused client |
| **Continue** | ✅ | ✅ | ✅ | Prompts as slash commands in VS Code/JetBrains |
| **Zed** | ✅ | ❌ | ❌ | Prompts appear as slash commands |
| **AgenticFlow** | ✅ | ✅ | ✅ | No-code AI platform |
| **Amazon Q CLI** | ✅ | ✅ | ❌ | Terminal-based assistant |
| **fast-agent** | ✅ | ✅ | ✅ | Python agent framework |
| **Genkit** | ✅ | ✅ | ⚠️ | Google's GenAI SDK |
| **Glama** | ✅ | ✅ | ✅ | AI workspace platform |
| **Lutra** | ✅ | ✅ | ✅ | Workflow automation |
| **mcp-use** | ✅ | ✅ | ✅ | Python library for MCP |
| **MCPHub** | ✅ | ✅ | ✅ | Neovim plugin |
| **MCPOmni-Connect** | ✅ | ✅ | ✅ | CLI client with ReAct |
| **oterm** | ✅ | ✅ | ❌ | Terminal client for Ollama |
| **Postman** | ✅ | ✅ | ✅ | API testing with MCP support |

### ❌ **Clients that DON'T Support MCP Prompts (Tools Only):**

| Client | Prompt Support | Tools | Resources | Notes |
|--------|---------------|-------|-----------|-------|
| **Cursor** | ❌ | ✅ | ❌ | Use tools directly: "Use get_vehicle_by_plate for 4304032" |
| **VS Code GitHub Copilot** | ❌ | ✅ | ❌ | Tools and roots only |
| **Cline** | ❌ | ✅ | ✅ | VS Code extension |
| **BoltAI** | ❌ | ✅ | ❌ | Native AI chat client |
| **Copilot-MCP** | ❌ | ✅ | ✅ | GitHub Copilot integration |
| **Most other clients** | ❌ | ✅ | ❌ | Tools-only support |

### 🔧 **Usage Examples by Client:**

#### **Claude Desktop App / Claude.ai** (Full Support)
```
@get_vehicle_info 4304032
```

#### **Zed / Continue** (Slash Commands)
```
/get_vehicle_info 4304032
```

#### **Cursor** (Manual Tool Usage)
```
Use the get_vehicle_by_plate tool to look up license plate 4304032. 
Provide complete vehicle information including make, model, year, color, 
technical specs, inspection status, and ownership details in a clear format.
```

### 💡 **Recommendations:**

- **For Full MCP Experience**: Use **Claude Desktop App** - supports all features
- **For VS Code Users**: Use **Continue** extension - prompts become slash commands  
- **For Cursor Users**: Use tools directly with descriptive instructions
- **For Terminal Users**: Try **Amazon Q CLI** or **oterm**
- **For Neovim Users**: Use **MCPHub** plugin

### 🚀 **Future Support:**

According to official documentation, more clients are adding prompt support. Check the [official MCP clients page](https://modelcontextprotocol.io/clients) for the latest updates.

## Search Capabilities

- ✅ **Manufacturer** (`manufacturer`) - e.g., 'טויוטה אנגליה' (Toyota)
- ✅ **Model** (`model`) - e.g., 'ZWE186L-DHXNBW'
- ✅ **License Plate** (`license_plate`) - e.g., '4304032'
- ✅ **Combined Searches** - Mix multiple filters for precise results
- ❌ **Year Filter** - Removed due to API conflicts

## Quick Start

### Development

1. **Install uv** (recommended):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone and setup**:
```bash
git clone <your-repo>
cd car_israel_gov
uv sync
```

3. **Run locally**:
```bash
uv run python mcp_server.py
```

The server will start on `http://0.0.0.0:9876/mcp`

### Production Deployment

#### Using Docker

1. **Build the image**:
```bash
docker build -t israel-vehicle-mcp .
```

2. **Run the container**:
```bash
docker run -p 9876:9876 -e PORT=9876 israel-vehicle-mcp
```

#### Cloud Deployment

The server is configured for cloud deployment with:
- Environment variable `PORT` support
- Health checks configured
- Non-root user for security
- Optimized Docker layers

**Deploy to any cloud platform** that supports Docker containers.

## Configuration

### Cursor Integration

Add to your `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "israel-vehicle-data": {
      "command": "uv",
      "args": ["run", "python", "/path/to/mcp_server.py"],
      "env": {
        "PORT": "9876"
      }
    }
  }
}
```

Or for HTTP transport:
```json
{
  "mcpServers": {
    "israel-vehicle-data": {
      "url": "http://127.0.0.1:9876/mcp"
    }
  }
}
```

### Environment Variables

- `PORT` - Server port (default: 9876)

## Data Source

- **Source**: Israeli Government Open Data Portal (data.gov.il)
- **Coverage**: All registered vehicles in Israel
- **License**: "אחר (פתוח)" (Other - Open)
- **Update Frequency**: Real-time government data

## Example Usage

### Get Vehicle Information
```
Use the get_vehicle_info prompt with license plate "4304032"
```

### Search by Manufacturer
```
Use the search_vehicles prompt with manufacturer "טויוטה אנגליה"
```

### Advanced Search
```
Use the search_vehicles prompt with both manufacturer and model filters
```

## API Performance

- **Vehicle Lookup**: ~1-2 seconds
- **Search Results**: ~2-3 seconds
- **Dataset Size**: 43,000+ Toyota vehicles (example)
- **Concurrent Requests**: Supported via async/await

## Development

### Project Structure
```
car_israel_gov/
├── mcp_server.py          # Main MCP server
├── pyproject.toml         # uv configuration
├── Dockerfile             # Production container
├── .dockerignore          # Docker build optimization
├── README.md              # This file
└── uv.lock               # Dependency lock file
```

### Testing Tools Directly

```bash
# Test vehicle lookup
uv run python -c "
from mcp_server import get_vehicle_by_plate_tool
import asyncio
result = asyncio.run(get_vehicle_by_plate_tool('4304032'))
print(result)
"

# Test search
uv run python -c "
from mcp_server import search_vehicles_tool
import asyncio
result = asyncio.run(search_vehicles_tool(manufacturer='טויוטה אנגליה', limit=3))
print(f'Found {result[\"total\"]} vehicles')
"
```