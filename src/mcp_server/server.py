"""
Model Context Protocol (MCP) Server for Enterprise Data Fabrics.
Implements the JSON-RPC Model Context Protocol standard over Stdio transport.
"""
import sys
import json
from src.fabric.engine import SandboxedQueryEngine
from src.governor.watcher import LakehouseHealthWatcher
from src.governor.compactor import AutonomousCompactor

engine = SandboxedQueryEngine()
watcher = LakehouseHealthWatcher()
compactor = AutonomousCompactor(engine)

TOOLS = [
    {
        "name": "lakehouse_inspect_schema",
        "description": "Inspects lakehouse table columns, data types, and row count contracts.",
        "inputSchema": {
            "type": "object",
            "properties": {"table_name": {"type": "string", "description": "Table to inspect (e.g. 'orders')"}},
            "required": ["table_name"]
        }
    },
    {
        "name": "lakehouse_explain_query",
        "description": "Analyzes SQL query execution plan, checks for table scans, and recommends optimizations.",
        "inputSchema": {
            "type": "object",
            "properties": {"sql": {"type": "string", "description": "SQL statement to explain"}},
            "required": ["sql"]
        }
    },
    {
        "name": "lakehouse_query_sandboxed",
        "description": "Executes read-only SQL queries with deterministic row caps and timeout guardrails.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SQL query to run"},
                "limit": {"type": "integer", "description": "Maximum rows (capped at 100)", "default": 50}
            },
            "required": ["sql"]
        }
    },
    {
        "name": "governor_audit_pipeline",
        "description": "Audits lakehouse storage fragmentation, small-file sprawl, and CDC latency.",
        "inputSchema": {
            "type": "object",
            "properties": {"table_name": {"type": "string", "description": "Target table name"}},
            "required": ["table_name"]
        }
    },
    {
        "name": "governor_trigger_compaction",
        "description": "Autonomously executes bin-packing compaction with strict row-count verification.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Target table to compact"},
                "target_size_mb": {"type": "integer", "description": "Target block size in MB", "default": 128}
            },
            "required": ["table_name"]
        }
    }
]

def handle_call_tool(name: str, arguments: dict):
    if name == "lakehouse_inspect_schema":
        return engine.get_schema_metadata(arguments.get("table_name", "orders"))
    elif name == "lakehouse_explain_query":
        return engine.explain_plan(arguments.get("sql", ""))
    elif name == "lakehouse_query_sandboxed":
        return engine.execute_sandboxed(arguments.get("sql", ""), arguments.get("limit", 50))
    elif name == "governor_audit_pipeline":
        return watcher.audit_fragmentation(arguments.get("table_name", "orders"))
    elif name == "governor_trigger_compaction":
        return compactor.execute_compaction(arguments.get("table_name", "orders"), arguments.get("target_size_mb", 128))
    else:
        return {"error": f"Unknown tool: {name}"}

def main():
    """Stdio JSON-RPC loop for Model Context Protocol."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            method = req.get("method")
            msg_id = req.get("id")
            
            if method == "tools/list":
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
            elif method == "tools/call":
                params = req.get("params", {})
                tool_name = params.get("name")
                args = params.get("arguments", {})
                res = handle_call_tool(tool_name, args)
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}}
            elif method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "agentic-data-fabric", "version": "1.0.0"}
                    }
                }
            else:
                resp = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Method not found"}}
                
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
