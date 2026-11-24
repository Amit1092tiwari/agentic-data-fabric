"""
Deterministic Columnar Query Engine (DuckDB & PyArrow).
Provides zero-copy analytics, schema contracts, and sandboxed execution.
"""
import duckdb
from typing import Dict, Any
from src.fabric.guardrails import FabricGuardrail

class SandboxedQueryEngine:
    def __init__(self, in_memory: bool = True):
        self.con = duckdb.connect(':memory:' if in_memory else 'lakehouse.duckdb')
        self._init_mock_lakehouse_data()

    def _init_mock_lakehouse_data(self):
        """Initializes baseline lakehouse tables for demonstration and agent testing."""
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id BIGINT PRIMARY KEY,
                customer_id VARCHAR,
                amount DECIMAL(10, 2),
                order_status VARCHAR,
                event_timestamp TIMESTAMP
            );
            
            INSERT INTO orders VALUES
                (1001, 'CUST-01', 249.50, 'COMPLETED', '2026-11-20 08:30:00'),
                (1002, 'CUST-02', 89.00, 'PENDING', '2026-11-20 09:15:00'),
                (1003, 'CUST-01', 450.25, 'COMPLETED', '2026-11-21 11:00:00'),
                (1004, 'CUST-03', 1200.00, 'SHIPPED', '2026-11-22 14:20:00'),
                (1005, 'CUST-04', 15.75, 'COMPLETED', '2026-11-23 16:45:00');
        """)

    def get_schema_metadata(self, table_name: str) -> Dict[str, Any]:
        """Returns schema contract and partition information."""
        try:
            info = self.con.execute(f"DESCRIBE {table_name}").fetchall()
            columns = [{"name": r[0], "type": r[1], "nullable": r[2]} for r in info]
            row_count = self.con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            return {
                "table": table_name,
                "columns": columns,
                "total_rows": row_count,
                "format": "Parquet / Columnar Arrow"
            }
        except Exception as e:
            return {"error": str(e)}

    def explain_plan(self, sql: str) -> Dict[str, Any]:
        """Returns execution plan and scans for partition pruning and un-sargable operators."""
        try:
            sanitized = FabricGuardrail.validate_and_sanitize(sql, requested_limit=10)
            plan = self.con.execute(f"EXPLAIN {sanitized}").fetchall()
            plan_str = "\n".join([r[1] for r in plan])
            has_table_scan = "SEQ_SCAN" in plan_str
            return {
                "sanitized_sql": sanitized,
                "execution_plan": plan_str,
                "has_sequential_scan": has_table_scan,
                "recommendation": "Consider partition filter on event_timestamp" if has_table_scan else "Optimal plan"
            }
        except Exception as e:
            return {"error": str(e)}

    def execute_sandboxed(self, sql: str, limit: int = 50) -> Dict[str, Any]:
        """Safely executes read-only SQL with deterministic row cap."""
        try:
            sanitized = FabricGuardrail.validate_and_sanitize(sql, requested_limit=limit)
            rel = self.con.execute(sanitized)
            columns = [desc[0] for desc in rel.description]
            rows = rel.fetchall()
            data = [dict(zip(columns, row)) for row in rows]
            return {
                "status": "SUCCESS",
                "rows_returned": len(data),
                "columns": columns,
                "data": data
            }
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
