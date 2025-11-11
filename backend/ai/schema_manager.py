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
    # Support two shapes:
    # 1) {"tableName": "T", "columns": [{"name": "COL", "type": "..."} , ...]}
    # 2) {"TABLE_A": ["COL1", "COL2"], "TABLE_B": [{"name": "COL1"}, "COL2", ...]}
    if isinstance(schema_json, dict) and "tableName" in schema_json and "columns" in schema_json:
        table_name = schema_json.get("tableName")
        raw_columns = schema_json.get("columns", [])
        column_names = []
        for col in raw_columns:
            if isinstance(col, dict):
                name = col.get("name")
                if name:
                    column_names.append(name)
            elif isinstance(col, str):
                column_names.append(col)
        cols_str = ", ".join(column_names)
        lines.append(f"TABLE: {table_name} ({cols_str})")
        return "\n".join(lines)

    # Fallback: treat schema_json as mapping of table -> columns
    for table, columns in schema_json.items():
        column_names = []
        if isinstance(columns, list):
            for col in columns:
                if isinstance(col, dict):
                    name = col.get("name")
                    if name:
                        column_names.append(name)
                elif isinstance(col, str):
                    column_names.append(col)
        cols_str = ", ".join(column_names)
        lines.append(f"TABLE: {table} ({cols_str})")
    return "\n".join(lines)
