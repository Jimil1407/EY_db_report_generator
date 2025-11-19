import json
from pathlib import Path
import os
from typing import List, Union

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


def filter_schema_by_tables(schema_json: Union[List[dict], dict], table_names: List[str]) -> Union[List[dict], dict]:
    """
    Filter schema to only include specified tables.
    
    Args:
        schema_json: Schema data (list of table objects or dict)
        table_names: List of table names to include (case-insensitive)
        
    Returns:
        Filtered schema with only the specified tables
    """
    if not table_names:
        return schema_json
    
    # Normalize table names to uppercase for comparison
    table_names_upper = [name.upper() for name in table_names]
    
    # Handle list of table objects (current schema.json format)
    if isinstance(schema_json, list):
        filtered = [
            table for table in schema_json
            if isinstance(table, dict) and table.get("tableName", "").upper() in table_names_upper
        ]
        return filtered
    
    # Handle dict format (legacy support)
    elif isinstance(schema_json, dict):
        # Check if it's a single table object
        if "tableName" in schema_json and "columns" in schema_json:
            table_name = schema_json.get("tableName", "").upper()
            if table_name in table_names_upper:
                return schema_json
            else:
                return {}
        
        # Handle dict of tables
        filtered = {
            table: columns
            for table, columns in schema_json.items()
            if table.upper() in table_names_upper
        }
        return filtered
    
    return schema_json


def format_schema(schema_json: Union[dict, List[dict]]) -> str:
    lines = []
    
    # Handle list of table objects (current schema.json format)
    if isinstance(schema_json, list):
        for table_obj in schema_json:
            if isinstance(table_obj, dict) and "tableName" in table_obj and "columns" in table_obj:
                table_name = table_obj.get("tableName")
                raw_columns = table_obj.get("columns", [])
                column_names = []
                column_details = []
                for col in raw_columns:
                    if isinstance(col, dict):
                        name = col.get("name")
                        col_type = col.get("type", "unknown")
                        if name:
                            column_names.append(name)
                            column_details.append(f"  - {name} ({col_type})")
                    elif isinstance(col, str):
                        column_names.append(col)
                        column_details.append(f"  - {col}")
                
                # Format with explicit column list
                lines.append(f"TABLE: {table_name}")
                lines.append(f"Available columns (USE ONLY THESE):")
                lines.extend(column_details)
                lines.append(f"\nColumn list: {', '.join(column_names)}")
                lines.append("")  # Empty line between tables
        return "\n".join(lines)
    
    # Support single table object: {"tableName": "T", "columns": [{"name": "COL", "type": "..."} , ...]}
    if isinstance(schema_json, dict) and "tableName" in schema_json and "columns" in schema_json:
        table_name = schema_json.get("tableName")
        raw_columns = schema_json.get("columns", [])
        column_names = []
        column_details = []
        for col in raw_columns:
            if isinstance(col, dict):
                name = col.get("name")
                col_type = col.get("type", "unknown")
                if name:
                    column_names.append(name)
                    column_details.append(f"  - {name} ({col_type})")
            elif isinstance(col, str):
                column_names.append(col)
                column_details.append(f"  - {col}")
        
        # Format with explicit column list
        lines.append(f"TABLE: {table_name}")
        lines.append(f"Available columns (USE ONLY THESE):")
        lines.extend(column_details)
        lines.append(f"\nColumn list: {', '.join(column_names)}")
        return "\n".join(lines)

    # Fallback: treat schema_json as mapping of table -> columns
    if isinstance(schema_json, dict):
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
