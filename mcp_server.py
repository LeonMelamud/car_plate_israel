from fastmcp import FastMCP
import httpx
import json
from typing import Dict, List, Optional
import asyncio
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(name="Israel Vehicle Data MCP")

# Constants
API_ENDPOINT = "https://data.gov.il/api/3/action/datastore_search"
RESOURCE_ID = "053cea08-09bc-40ec-8f7a-156f0677aff3"

# Helper functions for interacting with the CKAN API
async def fetch_vehicle_by_id(license_plate: str) -> Dict:
    """Fetch information for a specific vehicle by its license plate number."""
    async with httpx.AsyncClient() as client:
        params = {
            "resource_id": RESOURCE_ID,
            "filters": json.dumps({"mispar_rechev": license_plate})
        }
        response = await client.post(API_ENDPOINT, data=params)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("success"):
            raise ValueError("Failed to fetch data from API")
        
        records = data.get("result", {}).get("records", [])
        if not records:
            return {"error": "Vehicle not found"}
        
        return records[0]

async def search_vehicles(
    tozeret_nm: Optional[str] = None,
    degem_nm: Optional[str] = None,
    shnat_yitzur: Optional[int] = None,
    mispar_rechev: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict:
    """Search for vehicles based on various criteria."""
    async with httpx.AsyncClient() as client:
        # Build filters
        filters = {}
        if tozeret_nm:
            filters["tozeret_nm"] = [str(tozeret_nm)]
        if degem_nm:
            filters["degem_nm"] = [str(degem_nm)]
        if shnat_yitzur is not None:
            filters["shnat_yitzur"] = [str(shnat_yitzur)]
        if mispar_rechev:
            filters["mispar_rechev"] = [str(mispar_rechev)]
        
        params = {
            "resource_id": RESOURCE_ID,
            "limit": limit,
            "offset": offset
        }
        
        if shnat_yitzur is not None:
            params["shnat_yitzur"] = str(shnat_yitzur)
        
        if filters:
            params["filters"] = json.dumps(filters)
        
        response = await client.post(API_ENDPOINT, data=params)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("success"):
            raise ValueError("Failed to fetch data from API")
        
        result = data.get("result", {})
        return {
            "total": result.get("total", 0),
            "records": result.get("records", []),
            "limit": limit,
            "offset": offset
        }

async def fetch_available_licenses() -> Dict:
    """Fetch the list of available licenses from the CKAN API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_ENDPOINT.replace('datastore_search', 'license_list')}")
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise ValueError("Failed to fetch licenses from API")
        return data.get("result", [])

async def fetch_resource_details(resource_id: str) -> Dict:
    """Fetch metadata for a specific resource using its ID."""
    async with httpx.AsyncClient() as client:
        # Construct the correct API endpoint for resource_show
        # The base API_ENDPOINT is for datastore_search, so we need to adjust it
        action_url = API_ENDPOINT.replace("datastore_search", "resource_show")
        params = {"id": resource_id}
        response = await client.get(action_url, params=params)
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise ValueError(f"Failed to fetch resource details for {resource_id}: {data.get('error')}")
        return data.get("result", {})

async def fetch_package_details(package_id: str) -> Dict:
    """Fetch metadata for a specific package (dataset) using its ID."""
    async with httpx.AsyncClient() as client:
        # Construct the correct API endpoint for package_show
        action_url = API_ENDPOINT.replace("datastore_search", "package_show")
        params = {"id": package_id}
        response = await client.get(action_url, params=params)
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise ValueError(f"Failed to fetch package details for {package_id}: {data.get('error')}")
        return data.get("result", {})

# Define the VehicleInfoResource
@mcp.resource("vehicles://{license_plate}")
async def vehicle_info(license_plate: str) -> Dict:
    """Provides information about a specific vehicle based on license plate number."""
    try:
        return await fetch_vehicle_by_id(license_plate)
    except Exception as e:
        return {"error": str(e)}

# Define the SearchVehiclesByCriteriaTool
#@mcp.tool(name="search_vehicles")
async def search_vehicles_tool(
    degem_nm: Optional[str] = None,
    mispar_rechev: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict:
    """Search for vehicles based on model (degem_nm), license plate (mispar_rechev), limit, and offset.
    Manufacturer (tozeret_nm) and year of manufacture (shnat_yitzur) filters have been removed due to persistent type issues when called via MCP.
    Uses the datastore_search API for the Israeli government vehicle database.
    """
    if not RESOURCE_ID:
        return {"error": "RESOURCE_ID is not configured."}
    try:
        # Call the underlying search_vehicles function, passing None for the removed filters
        return await search_vehicles(
            resource_id=RESOURCE_ID,
            tozeret_nm=None, # Explicitly pass None as this filter is removed from tool signature
            degem_nm=degem_nm,
            shnat_yitzur=None, # Explicitly pass None as this filter is removed from tool signature
            mispar_rechev=mispar_rechev,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"Error in search_vehicles_tool: {e}", exc_info=True)
        return {"error": str(e)}

@mcp.tool(name="get_vehicle_by_plate")
async def get_vehicle_by_plate_tool(
    mispar_rechev: str
) -> Dict:
    """
    Fetches detailed information for a specific vehicle by its license plate number.
    
    Args:
        mispar_rechev: The license plate number of the vehicle (required).
    
    Returns:
        Dictionary containing vehicle information or an error if not found.
    """
    try:
        return await fetch_vehicle_by_id(mispar_rechev)
    except Exception as e:
        return {"error": str(e)}

#@mcp.tool(name="list_available_licenses")
async def list_available_licenses_tool() -> List[Dict]:
    """
    Fetches the list of all available licenses for datasets on data.gov.il.
    
    Returns:
        A list of dictionaries, where each dictionary represents a license.
    """
    try:
        return await fetch_available_licenses()
    except Exception as e:
        return {"error": str(e)}

#@mcp.tool(name="get_vehicle_dataset_license")
async def get_vehicle_dataset_license_tool() -> Dict:
    """
    Fetches the license information for the specific vehicle dataset used by this MCP.
    
    Returns:
        A dictionary containing license details (e.g., title, id, URL) or an error.
    """
    try:
        # Step 1: Get resource details to find the parent package_id
        resource_details = await fetch_resource_details(RESOURCE_ID)
        package_id = resource_details.get("package_id")
        
        if not package_id:
            return {"error": f"Could not determine package_id for resource {RESOURCE_ID}"}
            
        # Step 2: Get package details to find the license information
        package_info = await fetch_package_details(package_id)
        
        license_title = package_info.get("license_title")
        license_id = package_info.get("license_id")
        license_url = package_info.get("license_url") # Some datasets might have this directly
        
        # Fallback if license_url isn't directly on the package
        if not license_url and license_id:
             # We could potentially look up the URL from the list_available_licenses,
             # but for now, let's return what we have.
             pass

        if not license_title and not license_id:
            return {"error": f"No license information found for package {package_id}"}
            
        return {
            "package_id": package_id,
            "resource_id": RESOURCE_ID,
            "license_title": license_title,
            "license_id": license_id,
            "license_url": license_url or "Not explicitly provided in package details"
        }
    except Exception as e:
        return {"error": str(e)}

def get_mcp_application() -> FastMCP:
    """
    Returns the globally configured FastMCP application instance.
    This instance should already have tools registered via @mcp.tool decorators.
    """
    # The 'mcp' instance is already created at the module level and tools are registered to it.
    # We just need to return it.
    # Simplifying the print statement to avoid issues with iterating tools, 
    # as the exact internal structure of mcp.tool is unclear and was causing an error.
    # The FastMCP instance itself knows about its tools.
    print(f"Returning existing MCP Application instance: {mcp.name if hasattr(mcp, 'name') else 'FastMCP app'}")
    return mcp

# Make main_stdio synchronous if mcp_app.run() is a blocking call that handles its own loop.
def main_stdio():
    """
    Main function to run the MCP server using STDIN/STDOUT transport.
    This is called when mcp_server.py is executed directly.
    """
    mcp_app = get_mcp_application()
    print("Starting MCP server (stdio transport)...")
    # Assuming mcp_app.run() is a blocking call that starts its own event loop (via anyio).
    mcp_app.run(transport="stdio")

if __name__ == "__main__":
    print("Executing mcp_server.py directly, attempting to start stdio server.")
    try:
        # Call main_stdio directly, without asyncio.run()
        main_stdio()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Shutting down stdio server.")
    except Exception as e:
        print(f"Error during stdio server execution: {e}")
        import traceback
        traceback.print_exc()

# Example of how you might have had your server run previously (for context, will be removed/replaced by above)
# Original server startup code, if different, would be replaced by the if __name__ == "__main__" block.
# For example, if you had:
# server = FastMCP()
# server.add_tool(...)
# asyncio.run(server.run_stdio())
# This logic is now encapsulated in get_mcp_application() and the main_stdio() + if __name__ block.

# Example of how you might have had your server run previously (for context, will be removed/replaced by above)
# Original server startup code, if different, would be replaced by the if __name__ == "__main__" block.
# For example, if you had:
# server = FastMCP()
# server.add_tool(...)
# asyncio.run(server.run_stdio())
# This logic is now encapsulated in get_mcp_application() and the main_stdio() + if __name__ block. 