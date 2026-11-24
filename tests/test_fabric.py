"""
Comprehensive QA Suite for Agentic Data Fabric.
"""
from src.fabric.guardrails import FabricGuardrail, QueryGuardrailViolation
from src.fabric.engine import SandboxedQueryEngine
from src.governor.watcher import LakehouseHealthWatcher
from src.governor.compactor import AutonomousCompactor

def test_guardrail_blocks_dangerous_ddl():
    try:
        FabricGuardrail.validate_and_sanitize("DROP TABLE orders;")
        assert False, "Should have raised QueryGuardrailViolation"
    except QueryGuardrailViolation:
        assert True

def test_guardrail_enforces_limit():
    sanitized = FabricGuardrail.validate_and_sanitize("SELECT * FROM orders", requested_limit=25)
    assert "LIMIT 25" in sanitized

def test_sandboxed_engine_query():
    engine = SandboxedQueryEngine(in_memory=True)
    res = engine.execute_sandboxed("SELECT * FROM orders WHERE amount > 100", limit=5)
    assert res["status"] == "SUCCESS"
    assert res["rows_returned"] > 0

def test_governor_watcher_audit():
    watcher = LakehouseHealthWatcher()
    audit = watcher.audit_fragmentation("orders")
    assert audit["table"] == "orders"
    assert audit["needs_compaction"] is True

def test_autonomous_compactor():
    engine = SandboxedQueryEngine(in_memory=True)
    compactor = AutonomousCompactor(engine)
    res = compactor.execute_compaction("orders", target_size_mb=128)
    assert res["status"] == "SUCCESS"
    assert res["integrity_checksum"] == "VERIFIED_DETERMINISTIC"
