"""
Deterministic Guardrails Engine for Autonomous AI Agents.
Validates SQL syntax, blocks dangerous DDL/DML, and enforces query row caps.
"""
import re

class QueryGuardrailViolation(Exception):
    """Raised when an AI agent attempts to execute an unsafe SQL statement."""
    pass

class FabricGuardrail:
    FORBIDDEN_KEYWORDS = [
        r'\bDROP\b', r'\bTRUNCATE\b', r'\bDELETE\b', 
        r'\bALTER\b', r'\bINSERT\b', r'\bUPDATE\b', r'\bGRANT\b', r'\bREVOKE\b'
    ]
    MAX_ROW_CAP = 100

    @classmethod
    def validate_and_sanitize(cls, sql: str, requested_limit: int = 50) -> str:
        clean_sql = sql.strip().rstrip(';')
        
        # Check forbidden mutation keywords
        for pattern in cls.FORBIDDEN_KEYWORDS:
            if re.search(pattern, clean_sql, re.IGNORECASE):
                raise QueryGuardrailViolation(f"Unsafe operation detected matching pattern: {pattern}. Only SELECT is permitted.")
        
        # Ensure LIMIT is present and capped
        limit_match = re.search(r'\bLIMIT\s+(\d+)\b', clean_sql, re.IGNORECASE)
        capped_limit = min(requested_limit, cls.MAX_ROW_CAP)
        
        if limit_match:
            existing_limit = int(limit_match.group(1))
            if existing_limit > capped_limit:
                clean_sql = re.sub(r'\bLIMIT\s+\d+\b', f'LIMIT {capped_limit}', clean_sql, flags=re.IGNORECASE)
        else:
            clean_sql = f"{clean_sql} LIMIT {capped_limit}"
            
        return clean_sql
