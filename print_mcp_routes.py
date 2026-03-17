from backend.app.api.mcp.server import app as mcp_app

print("MCP App Routes:")
for route in mcp_app.routes:
    print(f"{route.path} - {getattr(route, 'name', 'no name')}")
