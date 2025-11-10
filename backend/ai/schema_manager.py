import json
from pathlib import Path
import os

_schema_cache = None

def load_schema(schema_path: str = None):
    global _schema_cache
    if _schema_cache is None:
        if schema_path is None:
            # Get the path relative to this file
            schema_path = Path(__file__).parent / "schema" / "schema.json"
        with open(schema_path, "r") as f:
            _schema_cache = json.load(f)
    return _schema_cache


def format_schema(schema_json: dict) -> str:
    lines = []
    table_name = schema_json.get("tableName", "UNKNOWN_TABLE")
    columns_data = schema_json.get("columns", [])
    
    column_names = [col.get("name", "UNKNOWN_COLUMN") for col in columns_data]
    cols_str = ", ".join(column_names)
    lines.append(f"TABLE: {table_name} ({cols_str})")
    return "\n".join(lines)
