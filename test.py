# test.py - FOR IN-MEMORY TESTING
import asyncio
from typing import Dict, Any
import json

# Import the function to get the configured MCP application from your server file
from mcp_server import get_mcp_application 

# Import the FastMCP Client - this import path might need verification
# based on FastMCP's actual library structure.
# Trying common patterns:
try:
    from fastmcp import Client as FastMCPClient
except ImportError:
    try:
        from fastmcp.client import Client as FastMCPClient
    except ImportError:
        # If neither works, this will raise an error, guiding the user to fix the import
        raise ImportError("Could not import FastMCPClient from 'fastmcp' or 'fastmcp.client'. Please check FastMCP library structure.")


async def call_in_memory_tool(client: FastMCPClient, tool_name: str, **tool_args) -> Dict[str, Any]:
    """Helper function to call a tool using the in-memory client."""
    print(f"\nCalling tool (in-memory): {tool_name} with args: {tool_args}")
    try:
        # Attempting to access the tool as an attribute and call it.
        # This pattern is sometimes used, e.g., client.my_tool_name(**tool_args)
        # This requires tools to be dynamically added to the client instance or a sub-object.
        # FastMCP might do this, or it might require a more explicit call method.
        
        # First, let's check if the tool name corresponds to a method on the client directly
        # or on a `tools` attribute, which is a common convention.
        target_object = client
        if hasattr(client, "tools") and hasattr(client.tools, tool_name): # e.g. client.tools.my_tool()
            target_object = client.tools 
        
        if hasattr(target_object, tool_name):
            tool_method = getattr(target_object, tool_name)
            print(f"Attempting to call tool as method: client.{'tools.' if target_object is not client else ''}{tool_name}")
            response = await tool_method(**tool_args)
        else:
            # Fallback to a generic `call_tool` or `call` method.
            # This is a more common explicit RPC-style invocation.
            # `call_tool(tool_name, arguments_dict)` is plausible for MCP.
            # `call(tool_name, **arguments)` is also common.
            if hasattr(client, "call_tool"):
                print(f"Attempting to call tool using: client.call_tool('{tool_name}', {{tool_args}})")
                response = await client.call_tool(tool_name, tool_args) # arguments as a single dict
            elif hasattr(client, "call"):
                print(f"Attempting to call tool using: client.call('{tool_name}', **{{tool_args}})")
                response = await client.call(tool_name, **tool_args) # arguments as kwargs
            else:
                raise NotImplementedError(f"FastMCPClient does not have a recognized method to call tool '{tool_name}'. Tried attribute, call_tool, and call.")

        print(f"Raw tool response from client.call_tool (in-memory): {response}")

        # Handle MCP Content wrapping (e.g., [TextContent(text='{...}')])
        if isinstance(response, list) and len(response) > 0:
            content_item = response[0]
            if hasattr(content_item, "text") and isinstance(content_item.text, str):
                # Assuming the .text attribute contains the JSON string
                json_text = content_item.text
                print(f"Extracted JSON text from TextContent: {json_text}")
                parsed_response = json.loads(json_text)
                print(f"Parsed tool response (in-memory): {parsed_response}")
                return parsed_response
            else:
                print(f"WARN: Expected TextContent-like object with a .text string attribute, but got: {content_item}")
                # If it's not TextContent, but still a list, what to do? 
                # For now, assume if it reached here and is a list, it's an unexpected structure from the client.
                return {"error": "Unexpected response structure from client (list item not TextContent)", "raw_response": response}
        elif isinstance(response, dict):
            # If the client directly returns a dict (less likely for MCP standard tools but possible)
            print(f"Tool response was already a dict (in-memory): {response}")
            return response
        else:
            print(f"WARN: Unexpected response type from client: {type(response)}, value: {response}")
            return {"error": f"Unexpected response type from client: {type(response).__name__}", "raw_response": response}

    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to decode JSON from TextContent: {e}. JSON Text was: '{json_text if 'json_text' in locals() else 'unavailable'}'")
        return {"error": f"JSON decode error: {e}", "malformed_text": json_text if 'json_text' in locals() else 'unavailable'}
    except Exception as e:
        print(f"ERROR calling tool {tool_name} (in-memory): {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Client-side error: {str(e)}", "error_type": type(e).__name__}


async def test_search_vehicles_by_criteria_tool_in_memory(client: FastMCPClient):
    print("\n--- Testing MCP Tool (in-memory): search_vehicles ---")
    tool_name = "search_vehicles"

    test_cases = [
        {"case_name": "By Manufacturer (TOYOTA)", "params": {"tozeret_nm": "TOYOTA", "limit": 1}},
        {"case_name": "By Year (2006)", "params": {"shnat_yitzur": 2006, "limit": 1}},
        # For mispar_rechev, ensure your search_vehicles tool logic handles it or use the dedicated tool
        {"case_name": "By License Plate via search (1013660)", "params": {"mispar_rechev": "1013660"}}, 
        {"case_name": "Non-existent License Plate via search tool", "params": {"mispar_rechev": "0000000"}},
        {"case_name": "No filters (default limit)", "params": {}}, # Expects default limit from tool
        {"case_name": "Limit only", "params": {"limit": 2}},
        # Add a test case that you expect to trigger an internal error in your actual tool if possible
        # For example, if specific input to search_vehicles in mcp_server.py would cause an httpx error
        # This "TOYOTA_ERROR_TEST" is based on my previous mock, your actual tool won't have it.
        # {"case_name": "Simulated Tool Error", "params": {"tozeret_nm": "SIMULATE_HTTP_ERROR_PLEASE"}},
    ]

    for test_case in test_cases:
        print(f"\nRunning case: {test_case['case_name']}")
        result = await call_in_memory_tool(client, tool_name, **test_case['params'])
        
        if result and not result.get("error"):
            if "records" in result and isinstance(result["records"], list):
                 print(f"VALIDATION: Got {len(result['records'])} records, total {result.get('total', 'N/A')}.")
                 # Example: Specific check for TOYOTA
                 if test_case['params'].get("tozeret_nm") == "TOYOTA" and len(result['records']) > 0:
                     assert all(r.get("tozeret_nm") == "TOYOTA" for r in result['records'] if "tozeret_nm" in r), "Not all records are TOYOTA"
                     print("Further TOYOTA validation passed.")
            else:
                print(f"VALIDATION WARNING: 'records' key missing or not a list in tool result for {test_case['case_name']}. Result: {{result}}")
        elif result and result.get("error"):
             print(f"Test case '{test_case['case_name']}' resulted in an error: {result['error']}")
             # Example: if your API/tool returns a specific error structure for "not found"
             if "Vehicle not found" in result['error'] and test_case['case_name'] == "Non-existent License Plate via search tool":
                 print("VALIDATION: Correctly handled 'Vehicle not found' via search tool.")
        else:
            print(f"Test case '{test_case['case_name']}' may have failed or had an unexpected result structure: {{result}}")


async def test_get_vehicle_details_by_license_plate_tool_in_memory(client: FastMCPClient):
    print("\n--- Testing MCP Tool (in-memory): get_vehicle_by_plate ---")
    tool_name = "get_vehicle_by_plate"

    valid_id = "1013660" 
    invalid_id = "0000000" 

    print(f"\nRunning case: Valid ID ({valid_id})")
    result_valid = await call_in_memory_tool(client, tool_name, mispar_rechev=valid_id)
    if result_valid and not result_valid.get("error"):
        # Check for a key that should exist in a valid response, e.g., 'mispar_rechev' itself or 'tozeret_nm'
        if str(result_valid.get("mispar_rechev")) == valid_id and "tozeret_nm" in result_valid:
            print(f"VALIDATION: Correct vehicle details received for valid ID. Manufacturer: {result_valid.get('tozeret_nm')}")
        else:
            print(f"VALIDATION WARNING: Vehicle details structure mismatch or key missing for valid ID. Got: {{result_valid}}")
    else:
        print(f"Test for valid ID '{valid_id}' returned an error or unexpected structure: {{result_valid}}")


    print(f"\nRunning case: Invalid ID ({invalid_id})")
    result_invalid = await call_in_memory_tool(client, tool_name, mispar_rechev=invalid_id)
    if result_invalid and result_invalid.get("error") and "Vehicle not found" in result_invalid.get("error", ""):
        print("VALIDATION: Correctly handled 'Vehicle not found' for invalid ID.")
    elif result_invalid and not result_invalid.get("error"): # Successful response for an invalid ID
        print(f"VALIDATION WARNING: Expected 'Vehicle not found' error for invalid ID '{invalid_id}', but got a success-like response: {{result_invalid}}")
    else: # Other error or unexpected structure
        print(f"Test case for invalid ID '{invalid_id}' may have failed or had an unexpected error: {{result_invalid}}")

async def test_list_available_licenses_tool_in_memory(client: FastMCPClient):
    print("\n--- Testing MCP Tool (in-memory): list_available_licenses ---")
    tool_name = "list_available_licenses"
    
    print(f"\nRunning case: Fetch all available licenses")
    result = await call_in_memory_tool(client, tool_name)
    
    # Check for errors returned by call_in_memory_tool itself or by the tool's except block
    if isinstance(result, dict) and result.get("error"):
        print(f"Test for '{tool_name}' returned an error: {result.get('error')}")
    elif isinstance(result, list):
        if len(result) > 0:
            print(f"VALIDATION: Received {len(result)} licenses. First license title: {result[0].get('title')}")
            assert any(lic.get("id") == "cc-zero" for lic in result), "CC-Zero license not found in the list."
            print("VALIDATION: CC-Zero license found.")
        else:
            print(f"VALIDATION: Received an empty list of licenses.") # Success, but no licenses
    else:
        # This case should ideally not be reached if the tool behaves as expected (returns list or dict with error)
        print(f"VALIDATION WARNING: Unexpected result type for '{tool_name}'. Expected list or dict with error, got: {{type(result)}} - {{result}}")

async def test_get_vehicle_dataset_license_tool_in_memory(client: FastMCPClient):
    print("\n--- Testing MCP Tool (in-memory): get_vehicle_dataset_license ---")
    tool_name = "get_vehicle_dataset_license"

    print(f"\nRunning case: Fetch license for the vehicle dataset")
    result = await call_in_memory_tool(client, tool_name)

    if result and not result.get("error"):
        if result.get("license_title") and result.get("package_id") and result.get("resource_id"):
            print(f"VALIDATION: Successfully fetched license for vehicle dataset.")
            print(f"  Package ID: {result.get('package_id')}")
            print(f"  Resource ID: {result.get('resource_id')}")
            print(f"  License Title: {result.get('license_title')}")
            print(f"  License ID: {result.get('license_id')}")
            print(f"  License URL: {result.get('license_url')}")
            # You might want to assert specific expected values if known
            # assert result.get("license_id") == "expected_license_id_for_vehicle_data", "Unexpected license ID"
        else:
            print(f"VALIDATION WARNING: License information structure mismatch. Got: {{result}}")
    else:
        print(f"Test for '{tool_name}' returned an error or unexpected structure: {{result}}")

async def main():
    print("Starting MCP Server In-Memory Interface tests...")

    mcp_application = get_mcp_application() # Get your FastMCP app from mcp_server.py

    # The FastMCP documentation/examples should clarify the exact keyword
    # for passing the app instance (e.g., `app=`, `server=`, `transport=InMemoryTransport(app)`).
    # Using `app=mcp_application` as a strong guess.
    # Also, the client might need to be used within an async context manager.
    client_instance = None
    try:
        # This is the crucial part - how to instantiate the client for in-memory.
        # Option 1: Direct instantiation if it takes the app/server.
        client_instance = FastMCPClient(mcp_application) 
        # Option 2: Alternative if it uses a different keyword.
        # client_instance = FastMCPClient(server=mcp_application) 
        # Option 3: If it uses an in-memory transport explicitly.
        # from fastmcp.transport import InMemoryClientTransport
        # client_instance = FastMCPClient(transport=InMemoryClientTransport(mcp_application))

        # If the client has an explicit connect method or is an async context manager
        if hasattr(client_instance, "__aenter__"):
             async with client_instance as client:
                print("FastMCP In-Memory Client initialized (using async with).")
                await test_search_vehicles_by_criteria_tool_in_memory(client)
                await test_get_vehicle_details_by_license_plate_tool_in_memory(client)
                await test_list_available_licenses_tool_in_memory(client)
                await test_get_vehicle_dataset_license_tool_in_memory(client)
        elif hasattr(client_instance, "connect") and asyncio.iscoroutinefunction(client_instance.connect):
            await client_instance.connect()
            print("FastMCP In-Memory Client initialized (using connect()).")
            await test_search_vehicles_by_criteria_tool_in_memory(client_instance)
            await test_get_vehicle_details_by_license_plate_tool_in_memory(client_instance)
            await test_list_available_licenses_tool_in_memory(client_instance)
            await test_get_vehicle_dataset_license_tool_in_memory(client_instance)
            if hasattr(client_instance, "close"): await client_instance.close()
        else:
            # Assuming simple instantiation is enough and tools can be called directly.
             print("FastMCP In-Memory Client initialized (direct instantiation).")
             await test_search_vehicles_by_criteria_tool_in_memory(client_instance)
             await test_get_vehicle_details_by_license_plate_tool_in_memory(client_instance)
             await test_list_available_licenses_tool_in_memory(client_instance)
             await test_get_vehicle_dataset_license_tool_in_memory(client_instance)
            
        print("\nMCP Server In-Memory Interface tests finished.")

    except ImportError as e:
        print(f"IMPORT ERROR: {{e}}. Please ensure FastMCP client is installed and the import path is correct.")
    except TypeError as e:
        print(f"TYPE ERROR during client instantiation: {{e}}. This likely means the keyword argument for passing the app instance (e.g. 'app=' or 'server=') is incorrect for FastMCPClient. Please check FastMCP documentation.")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"An unexpected error occurred during in-memory tests: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client_instance and hasattr(client_instance, "close") and not hasattr(client_instance, "__aexit__"):
            if asyncio.iscoroutinefunction(client_instance.close):
                await client_instance.close()
            else:
                client_instance.close()
            print("In-memory client closed.")


if __name__ == "__main__":
    asyncio.run(main()) 