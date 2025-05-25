from fastmcp import FastMCP
import httpx
import json
import sys
from typing import Dict, List, Optional
import asyncio
import logging
import os

# Configure enhanced logging for production observability
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        # Add file handler if needed: logging.FileHandler('mcp_server.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
API_ENDPOINT = "https://data.gov.il/api/3/action/datastore_search"
RESOURCE_ID = "053cea08-09bc-40ec-8f7a-156f0677aff3"

# Log startup information
logger.info("=== Israel Vehicle Data MCP Server Starting ===")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Environment PORT: {os.environ.get('PORT', 'not set')}")
logger.info(f"API Endpoint: {API_ENDPOINT}")
logger.info(f"Resource ID: {RESOURCE_ID}")

# Initialize MCP server
mcp = FastMCP(
    name="Israel Vehicle Data MCP",
    instructions="""
    A comprehensive Model Context Protocol (MCP) server for accessing Israeli government vehicle registration data.
    
    This server provides:
    - Vehicle lookup by license plate number
    - Vehicle search by model name
    - Comprehensive vehicle information including make, model, year, color, technical specs
    - Inspection and registration status
    - Dataset licensing information
    - Multiple specialized prompts for different use cases
    
    Data source: Israeli Government Open Data Portal (data.gov.il)
    Coverage: All registered vehicles in Israel
    
    Available tools:
    - get_vehicle_by_plate: Look up any Israeli vehicle by license plate
    - search_vehicles: Search vehicles by manufacturer, model, or license plate
    - get_vehicle_dataset_license: Get dataset license information
    - list_available_licenses: List all available data licenses
    
    Available prompts (4 total):
    - get_vehicle_info: Complete vehicle information by license plate
    - search_vehicles: Search vehicles by manufacturer, model, or license plate
    - get_dataset_license: Dataset license information
    - list_data_licenses: Overview of all data licenses
    
    Perfect for: Car buyers, insurance agents, mechanics, fleet managers, and anyone needing Israeli vehicle data.
    """
)

async def fetch_vehicle_by_id(license_plate: str) -> Dict:
    """Fetch information for a specific vehicle by its license plate number."""
    logger.info(f"🔍 Fetching vehicle data for license plate: {license_plate}")
    start_time = asyncio.get_event_loop().time()
    
    async with httpx.AsyncClient() as client:
        params = {
            "resource_id": RESOURCE_ID,
            "filters": json.dumps({"mispar_rechev": license_plate})
        }
        logger.debug(f"API request params: {params}")
        
        try:
            response = await client.post(API_ENDPOINT, data=params)
            response.raise_for_status()
            data = response.json()
            
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.info(f"✅ API request completed in {elapsed_time:.2f}s for license plate: {license_plate}")
            
            if not data.get("success"):
                logger.error(f"❌ API returned success=false for license plate: {license_plate}")
                raise ValueError("Failed to fetch data from API")
            
            records = data.get("result", {}).get("records", [])
            if not records:
                logger.warning(f"⚠️ No vehicle found for license plate: {license_plate}")
                return {"error": "Vehicle not found"}
            
            vehicle_data = records[0]
            logger.info(f"🚗 Found vehicle: {vehicle_data.get('tozeret_nm', 'Unknown')} {vehicle_data.get('kinuy_mishari', 'Unknown')} ({vehicle_data.get('shnat_yitzur', 'Unknown')})")
            return vehicle_data
            
        except httpx.HTTPError as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"❌ HTTP error after {elapsed_time:.2f}s for license plate {license_plate}: {e}")
            raise
        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"❌ Unexpected error after {elapsed_time:.2f}s for license plate {license_plate}: {e}")
            raise

async def search_vehicles(
    tozeret_nm: Optional[str] = None,
    degem_nm: Optional[str] = None,
    shnat_yitzur: Optional[int] = None,
    mispar_rechev: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict:
    """Search for vehicles based on various criteria."""
    search_params = {
        "manufacturer": tozeret_nm,
        "model": degem_nm, 
        "year": shnat_yitzur,
        "license_plate": mispar_rechev,
        "limit": limit,
        "offset": offset
    }
    active_filters = {k: v for k, v in search_params.items() if v is not None and k not in ['limit', 'offset']}
    logger.info(f"🔍 Searching vehicles with filters: {active_filters}, limit: {limit}, offset: {offset}")
    start_time = asyncio.get_event_loop().time()
    
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
        
        logger.debug(f"API search params: {params}")
        
        try:
            response = await client.post(API_ENDPOINT, data=params)
            response.raise_for_status()
            data = response.json()
            
            elapsed_time = asyncio.get_event_loop().time() - start_time
            
            if not data.get("success"):
                logger.error(f"❌ API search returned success=false with filters: {active_filters}")
                raise ValueError("Failed to fetch data from API")
            
            result = data.get("result", {})
            total_found = result.get("total", 0)
            records_count = len(result.get("records", []))
            
            logger.info(f"✅ Search completed in {elapsed_time:.2f}s - Found {total_found} total vehicles, returning {records_count} records")
            
            if total_found > 0:
                # Log sample of found vehicles
                sample_vehicles = result.get("records", [])[:3]  # First 3 vehicles
                for i, vehicle in enumerate(sample_vehicles):
                    logger.info(f"  📋 Sample {i+1}: {vehicle.get('mispar_rechev')} - {vehicle.get('tozeret_nm')} {vehicle.get('kinuy_mishari', 'Unknown')} ({vehicle.get('shnat_yitzur')})")
            
            return {
                "total": total_found,
                "records": result.get("records", []),
                "limit": limit,
                "offset": offset
            }
            
        except httpx.HTTPError as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"❌ HTTP error during search after {elapsed_time:.2f}s with filters {active_filters}: {e}")
            raise
        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"❌ Unexpected error during search after {elapsed_time:.2f}s with filters {active_filters}: {e}")
            raise

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
@mcp.tool(name="search_vehicles")
async def search_vehicles_tool(
    tozeret_nm: Optional[str] = None,
    degem_nm: Optional[str] = None,
    mispar_rechev: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict:
    """Search for vehicles based on manufacturer (tozeret_nm), model (degem_nm), license plate (mispar_rechev), limit, and offset.
    Year of manufacture (shnat_yitzur) filter has been removed due to API conflicts (409 errors).
    Uses the datastore_search API for the Israeli government vehicle database.
    """
    logger.info(f"🔧 MCP Tool Called: search_vehicles - tozeret_nm={tozeret_nm}, degem_nm={degem_nm}, mispar_rechev={mispar_rechev}, limit={limit}, offset={offset}")
    
    if not RESOURCE_ID:
        logger.error("❌ RESOURCE_ID is not configured")
        return {"error": "RESOURCE_ID is not configured."}
    try:
        # Call the underlying search_vehicles function, passing None for the year filter
        result = await search_vehicles(
            tozeret_nm=tozeret_nm,
            degem_nm=degem_nm,
            shnat_yitzur=None, # Explicitly pass None as this filter causes API conflicts
            mispar_rechev=mispar_rechev,
            limit=limit,
            offset=offset,
        )
        logger.info(f"✅ MCP Tool Success: search_vehicles returned {result.get('total', 0)} total results")
        return result
    except Exception as e:
        logger.error(f"❌ MCP Tool Error: search_vehicles failed: {e}", exc_info=True)
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
    logger.info(f"🔧 MCP Tool Called: get_vehicle_by_plate - mispar_rechev={mispar_rechev}")
    
    try:
        result = await fetch_vehicle_by_id(mispar_rechev)
        if "error" in result:
            logger.warning(f"⚠️ MCP Tool Warning: get_vehicle_by_plate - {result['error']}")
        else:
            logger.info(f"✅ MCP Tool Success: get_vehicle_by_plate found vehicle {result.get('tozeret_nm', 'Unknown')} {result.get('kinuy_mishari', 'Unknown')}")
        return result
    except Exception as e:
        logger.error(f"❌ MCP Tool Error: get_vehicle_by_plate failed for {mispar_rechev}: {e}", exc_info=True)
        return {"error": str(e)}

@mcp.tool(name="list_available_licenses")
async def list_available_licenses_tool() -> List[Dict]:
    """
    Fetches the list of all available licenses for datasets on data.gov.il.
    
    Returns:
        A list of dictionaries, where each dictionary represents a license.
    """
    logger.info("🔧 MCP Tool Called: list_available_licenses")
    
    try:
        result = await fetch_available_licenses()
        license_count = len(result) if isinstance(result, list) else 0
        logger.info(f"✅ MCP Tool Success: list_available_licenses returned {license_count} licenses")
        return result
    except Exception as e:
        logger.error(f"❌ MCP Tool Error: list_available_licenses failed: {e}", exc_info=True)
        return {"error": str(e)}

@mcp.tool(name="get_vehicle_dataset_license")
async def get_vehicle_dataset_license_tool() -> Dict:
    """
    Fetches the license information for the specific vehicle dataset used by this MCP.
    
    Returns:
        A dictionary containing license details (e.g., title, id, URL) or an error.
    """
    logger.info("🔧 MCP Tool Called: get_vehicle_dataset_license")
    
    try:
        # Step 1: Get resource details to find the parent package_id
        resource_details = await fetch_resource_details(RESOURCE_ID)
        package_id = resource_details.get("package_id")
        
        if not package_id:
            logger.error(f"❌ Could not determine package_id for resource {RESOURCE_ID}")
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
            logger.error(f"❌ No license information found for package {package_id}")
            return {"error": f"No license information found for package {package_id}"}
        
        result = {
            "package_id": package_id,
            "resource_id": RESOURCE_ID,
            "license_title": license_title,
            "license_id": license_id,
            "license_url": license_url or "Not explicitly provided in package details"
        }
        logger.info(f"✅ MCP Tool Success: get_vehicle_dataset_license found license '{license_title}' ({license_id})")
        return result
    except Exception as e:
        logger.error(f"❌ MCP Tool Error: get_vehicle_dataset_license failed: {e}", exc_info=True)
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

def main_streamable_http():
    """
    Main function to run the MCP server using Streamable HTTP transport.
    This is called when mcp_server.py is executed directly.
    """
    mcp_app = get_mcp_application()
    
    # Get port from environment variable or default
    port = int(os.environ.get("PORT", 9876))
    host = "0.0.0.0"  # Listen on all available interfaces for cloud deployment
    
    logger.info(f"🚀 Starting MCP server (streamable-http transport)")
    logger.info(f"📡 Server will listen on {host}:{port}/mcp")
    logger.info(f"🌐 Access URL: http://{host}:{port}/mcp")
    
    try:
        # Assuming mcp_app.run() is a blocking call that starts its own event loop (via anyio).
        mcp_app.run(
            transport="streamable-http",
            host=host,
            port=port,
            path="/mcp"
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}", exc_info=True)
        raise

# Vehicle Information Prompts - One per tool
@mcp.prompt()
def get_vehicle_info(license_plate: str) -> str:
    """Get complete vehicle information by license plate"""
    return f"""Please look up complete information for Israeli vehicle with license plate {license_plate}.

Use the get_vehicle_by_plate tool to retrieve:
- Basic info (make, model, year, color)
- Technical specs (engine, tires, VIN)
- Inspection and registration status
- Ownership details

Present the information in a clear, organized format."""

@mcp.prompt()
def search_vehicles(manufacturer: str = None, model: str = None, license_plate: str = None) -> str:
    """Search for vehicles by manufacturer, model, or license plate"""
    search_params = []
    if manufacturer:
        search_params.append(f"manufacturer: {manufacturer}")
    if model:
        search_params.append(f"model: {model}")
    if license_plate:
        search_params.append(f"license plate: {license_plate}")
    
    search_description = " and ".join(search_params) if search_params else "all vehicles"
    
    return f"""Please search for Israeli vehicles with {search_description}.

Use the search_vehicles tool with appropriate parameters:
- tozeret_nm for manufacturer (e.g., 'טויוטה אנגליה')
- degem_nm for model (e.g., 'ZWE186L-DHXNBW')
- mispar_rechev for license plate

Show total found and sample results (limit to 10 for readability)."""

@mcp.prompt()
def get_dataset_license() -> str:
    """Get information about the vehicle dataset license"""
    return f"""Please provide information about the Israeli vehicle dataset license and usage terms.

Use the get_vehicle_dataset_license tool to show:
- License type and title
- Usage permissions and restrictions
- Data source attribution requirements

This helps understand how the vehicle data can be legally used."""

@mcp.prompt()
def list_data_licenses() -> str:
    """Get overview of all available data licenses"""
    return f"""Please provide an overview of all available data licenses on the Israeli government data portal.

Use the list_available_licenses tool to show:
- Different license types available
- Common license terms
- How to choose appropriate license for different use cases

This helps understand the broader licensing landscape for Israeli government data."""

if __name__ == "__main__":
    print("Executing mcp_server.py directly, attempting to start server.")
    try:
        # Call directly, without asyncio.run()
        main_streamable_http()
        #main_stdio()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Shutting down server.")
    except Exception as e:
        print(f"Error during stdio server execution: {e}")
        import traceback
        traceback.print_exc()

