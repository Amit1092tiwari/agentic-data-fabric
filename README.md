# 🤖 Enterprise Agentic Data Fabric & Autonomous MCP Governor

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Model Context Protocol](https://img.shields.io/badge/MCP-2024--11--05-8A2BE2.svg)](https://modelcontextprotocol.io/)
[![DuckDB](https://img.shields.io/badge/DuckDB-%3E%3D_0.10.0-FFF000?logo=duckdb)](https://duckdb.org/)
[![Apache Arrow](https://img.shields.io/badge/Apache_Arrow-Columnar_Zero--Copy-red.svg)](https://arrow.apache.org/)
[![CI Validation](https://img.shields.io/badge/CI-Automated_QA_Passing-success.svg)](.github/workflows/ci.yml)

A production-grade **Deterministic Data Fabric** enabling autonomous AI agents (Claude, Gemini, Antigravity, Cursor) to discover, inspect, query, and govern Lakehouse assets via the **Model Context Protocol (MCP)** with an integrated **Self-Healing Compaction Governor**.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    Client["🤖 AI Client (Claude Desktop / Gemini CLI / Antigravity)"] <-->|"Model Context Protocol (Stdio)"| MCPServer["🔌 MCP Server (src/mcp_server)"]
    
    subgraph GuardrailLayer ["Deterministic Guardrails & Query Sandbox"]
        MCPServer <--> Router["Gateway Router"]
        Router --> Guardrail["FabricGuardrail (Blocks DDL/DML, Enforces LIMIT Caps)"]
        Guardrail --> Engine["🦆 Sandboxed DuckDB & PyArrow Engine"]
    end

    subgraph StorageLayer ["Distributed Lakehouse & Storage"]
        Engine <--> Lakehouse["🧊 Apache Iceberg / Delta Lake on S3/MinIO"]
    end

    subgraph SelfHealingGovernor ["Autonomous Self-Healing Loop"]
        Watcher["📊 LakehouseHealthWatcher (Detects Small-File Sprawl)"]
        Lakehouse -.-> Watcher
        Watcher --> Compactor["⚙️ AutonomousCompactor (Bin-Packing with Checksums)"]
        Compactor -->|"Commit Verified Snapshot"| Lakehouse
    end
```

---

## ⚡ Model Context Protocol (MCP) Tools Catalog

| MCP Tool Name | Target Scope | Safety & Determinism Controls |
| :--- | :--- | :--- |
| `lakehouse_inspect_schema` | Table Schema & Metadata | Returns column data types, nullability, row counts, and storage format. |
| `lakehouse_explain_query` | Query Plan Optimization | Parses AST, analyzes sequential scans, and suggests partition pruning. |
| `lakehouse_query_sandboxed` | Read-Only Analytical SQL | Enforces AST validation (blocks mutations), caps row output (max 100), 5s timeout. |
| `governor_audit_pipeline` | Storage & File Health | Telemetry auditor returning small-file fragmentation index and skew. |
| `governor_trigger_compaction` | Autonomous Self-Healing | Executes columnar bin-packing with pre- and post-compaction row checksum validation. |

---

## 🚀 Antigravity MCP Routing Configuration

To route Google Antigravity / Gemini CLI through this server, add this entry to `~/.gemini/config/mcp_config.json`:

```json
{
  "mcpServers": {
    "agentic-data-fabric": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "C:/Users/amitt/Documents/github/agentic-data-fabric"
    }
  }
}
```

---

## 📜 Governance & Licensing
Licensed under the [Apache License 2.0](LICENSE). Maintained under enterprise architectural governance by Amitkumar Tiwari.
