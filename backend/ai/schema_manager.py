import json
from pathlib import Path
import os

_schema_cache = None

def load_schema(schema_path: str = "backend/ai/schema/schema.json"):
    global _schema_cache
    if _schema_cache is None:
        with open(schema_path, "r") as f:
            schema_json = json.load(f)
    return schema_json


def format_schema(schema_json: dict) -> str:
    lines = []
    #print(type(schema_json))
    for table, columns in schema_json.items():
        cols_str = ", ".join(columns)
        lines.append(f"TABLE: {table} ({cols_str})")
    return "\n".join(lines)
