from .gemini_client import GeminiClient
from .schema_manager import load_schema, format_schema, filter_schema_by_tables
from .prompt_builder import build_gemini_prompt
from typing import List, Optional
import re

class SQLGenerator:
    def __init__(self, few_shots: list, api_key: str, selected_tables: Optional[List[str]] = None):
        """
        Initialize SQLGenerator with schema and optional table filtering.
        
        Args:
            few_shots: List of few-shot examples for prompt
            api_key: Gemini API key
            selected_tables: Optional list of table names to filter schema. If None, uses all tables.
        """
        # Load fixed schema once
        schema_json = load_schema()  # returns list of table objects from file
        
        # Filter schema if selected_tables provided
        if selected_tables:
            schema_json = filter_schema_by_tables(schema_json, selected_tables)
        
        # Format schema for prompt context
        self.schema_context = format_schema(schema_json)  # formatted schema string
        self.schema_json = schema_json  # Store for validation
        self.few_shots = few_shots
        self.gemini_client = GeminiClient(api_key=api_key)
        
        # Extract valid column names and table names from schema for validation
        self.valid_columns = set()
        self.valid_tables = set()
        
        # Handle list of table objects (current schema.json format)
        if isinstance(schema_json, list):
            for table_obj in schema_json:
                if isinstance(table_obj, dict):
                    table_name = table_obj.get("tableName", "")
                    if table_name:
                        self.valid_tables.add(table_name.upper())
                    
                    columns = table_obj.get("columns", [])
                    for col in columns:
                        if isinstance(col, dict):
                            name = col.get("name")
                            if name:
                                self.valid_columns.add(name.upper())
                        elif isinstance(col, str):
                            self.valid_columns.add(col.upper())
        
        # Handle single table object (legacy support)
        elif isinstance(schema_json, dict) and "tableName" in schema_json:
            table_name = schema_json.get("tableName", "")
            if table_name:
                self.valid_tables.add(table_name.upper())
            
            columns = schema_json.get("columns", [])
            for col in columns:
                if isinstance(col, dict):
                    name = col.get("name")
                    if name:
                        self.valid_columns.add(name.upper())
                elif isinstance(col, str):
                    self.valid_columns.add(col.upper())

    def generate_query(self, user_question: str) -> str:
        import logging
        logger = logging.getLogger(__name__)
        
        # Build full combined prompt using the shared prompt builder
        prompt = build_gemini_prompt(
            user_question=user_question,
            few_shots=self.few_shots,
            schema_context=self.schema_context,
        )

        # Call Gemini API to generate SQL
        raw_output = self.gemini_client.generate_sql(prompt)
        logger.debug(f"Raw SQL output from Gemini: {raw_output[:500]}...")  # Log first 500 chars
        
        # Sanitize: strip markdown fences, language tags, and leading labels
        sql = self._clean_sql_output(raw_output)
        logger.debug(f"Cleaned SQL: {sql[:500]}...")  # Log first 500 chars
        
        # Validate SQL completeness
        completeness_error = self._validate_sql_completeness(sql)
        if completeness_error:
            logger.error(f"SQL completeness validation failed. Raw output: {raw_output[:1000]}")
            logger.error(f"Cleaned SQL: {sql[:1000]}")
            raise ValueError(f"Generated SQL is incomplete: {completeness_error}")
        
        # Validate that SQL only uses columns from schema
        validation_error = self._validate_sql_columns(sql)
        if validation_error:
            raise ValueError(f"Generated SQL uses invalid columns: {validation_error}")
        
        # Return SQL for further processing
        return sql
    
    def _validate_sql_completeness(self, sql: str) -> str:
        """
        Validate that the SQL query is complete and has all required components.
        Returns error message if validation fails, None if valid.
        """
        if not sql or not sql.strip():
            return "SQL query is empty"
        
        sql_upper = sql.strip().upper()
        
        # Must start with SELECT
        if not sql_upper.startswith("SELECT"):
            return "SQL query must start with SELECT"
        
        # Must contain FROM clause
        if "FROM" not in sql_upper:
            return "SQL query must include FROM clause with table name"
        
        # Check that at least one valid table is used
        if self.valid_tables:
            found_table = False
            for table_name in self.valid_tables:
                if table_name in sql_upper:
                    found_table = True
                    break
            
            if not found_table:
                return f"SQL query must include one of the valid tables: {', '.join(sorted(self.valid_tables))}"
        
        # Check for incomplete SELECT (e.g., "SELECT *;" without FROM)
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql_upper, re.DOTALL)
        if not select_match:
            # Check if it's just "SELECT *;" or similar without FROM
            if re.match(r'SELECT\s+\*?\s*;?\s*$', sql_upper):
                return "SQL query is incomplete - missing FROM clause"
        
        return None
    
    def _validate_sql_columns(self, sql: str) -> str:
        """
        Validate that the SQL query only uses columns from the schema.
        Returns error message if validation fails, None if valid.
        """
        if not sql or not self.valid_columns:
            return None
        
        sql_upper = sql.upper()
        
        # Extract column names from SELECT clause
        # Pattern: SELECT col1, col2, ... FROM table
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql_upper, re.DOTALL)
        if not select_match:
            return None  # Can't parse, let database handle it
        
        select_clause = select_match.group(1).strip()
        
        # Handle SELECT * case
        if select_clause.strip() == '*':
            return None  # SELECT * is allowed
        
        # Extract individual columns (handle functions, aliases, etc.)
        # Split by comma, but be careful with function calls
        columns = []
        current_col = ""
        paren_depth = 0
        
        for char in select_clause:
            if char == '(':
                paren_depth += 1
                current_col += char
            elif char == ')':
                paren_depth -= 1
                current_col += char
            elif char == ',' and paren_depth == 0:
                col_name = current_col.strip()
                if col_name:
                    # Extract base column name (remove aliases, functions)
                    base_col = self._extract_base_column(col_name)
                    if base_col:
                        columns.append(base_col)
                current_col = ""
            else:
                current_col += char
        
        # Handle last column
        if current_col.strip():
            base_col = self._extract_base_column(current_col.strip())
            if base_col:
                columns.append(base_col)
        
        # Check each column against valid columns
        invalid_columns = []
        for col in columns:
            col_upper = col.upper().strip()
            # Skip common SQL keywords and functions
            if col_upper in ('COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT', 'AS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'):
                continue
            # Check if it's a valid column
            if col_upper not in self.valid_columns and col_upper not in ('*', ''):
                # Check if it's part of a function (e.g., COUNT(column))
                if '(' in col_upper or ')' in col_upper:
                    # Try to extract column from function
                    func_col_match = re.search(r'\(([A-Z_][A-Z0-9_]*)\)', col_upper)
                    if func_col_match:
                        func_col = func_col_match.group(1)
                        if func_col not in self.valid_columns:
                            invalid_columns.append(col)
                else:
                    invalid_columns.append(col)
        
        if invalid_columns:
            return f"Invalid columns found: {', '.join(set(invalid_columns))}. Valid columns are: {', '.join(sorted(self.valid_columns))}"
        
        return None
    
    def _extract_base_column(self, col_expr: str) -> str:
        """
        Extract base column name from expression (handles aliases, functions, etc.)
        """
        col_expr = col_expr.strip()
        
        # Remove alias (e.g., "COLUMN AS alias" or "COLUMN alias")
        alias_match = re.search(r'\s+AS\s+(\w+)', col_expr, re.IGNORECASE)
        if alias_match:
            col_expr = col_expr[:alias_match.start()].strip()
        
        # Check for simple alias without AS
        parts = col_expr.split()
        if len(parts) == 2 and parts[1].isalnum():
            col_expr = parts[0]
        
        # Extract from function calls (e.g., COUNT(COLUMN) -> COLUMN)
        func_match = re.search(r'\(([A-Z_][A-Z0-9_]*)\)', col_expr.upper())
        if func_match:
            return func_match.group(1)
        
        # Return as-is if it looks like a column name
        if re.match(r'^[A-Z_][A-Z0-9_]*$', col_expr.upper()):
            return col_expr.upper()
        
        return None

    def _clean_sql_output(self, text: str) -> str:
        if not text:
            return text
        cleaned = text.strip()
        # Remove fenced code blocks ```sql ... ``` or ``` ...
        fenced_match = re.search(r"```[a-zA-Z]*\s*([\s\S]*?)```", cleaned)
        if fenced_match:
            cleaned = fenced_match.group(1).strip()
        # Remove leading labels like 'SQL:', 'SQL QUERY:', etc.
        cleaned = re.sub(r"^(SQL\s*QUERY\s*:|SQL\s*:)", "", cleaned, flags=re.IGNORECASE).strip()
        
        # Try to extract complete SQL query (handles multi-line queries)
        # Look for SELECT ... ; pattern that may span multiple lines
        sql_match = re.search(r"(SELECT[\s\S]+?;)", cleaned, flags=re.IGNORECASE | re.DOTALL)
        if sql_match:
            sql = sql_match.group(1).strip()
            # Clean up extra whitespace but preserve structure
            sql = re.sub(r'\s+', ' ', sql)  # Replace multiple spaces/newlines with single space
            # Restore newlines after keywords for readability (optional, but helps)
            sql = re.sub(r'\s+(FROM|WHERE|JOIN|ON|ORDER BY|GROUP BY|HAVING|FETCH FIRST)', r'\n\1', sql, flags=re.IGNORECASE)
            return sql
        
        # If no semicolon found, try to find SELECT statement until end of text
        select_match = re.search(r"(SELECT[\s\S]+)", cleaned, flags=re.IGNORECASE | re.DOTALL)
        if select_match:
            sql = select_match.group(1).strip()
            # Add semicolon if missing
            if not sql.rstrip().endswith(';'):
                sql = sql.rstrip() + ";"
            # Clean up extra whitespace
            sql = re.sub(r'\s+', ' ', sql)
            return sql
        
        # Last fallback: return cleaned as-is
        return cleaned


if __name__ == "__main__":
    few_shots = [
        {
            "q": "How many claims are pending?",
            "a": "SELECT COUNT(*) FROM claims WHERE status = 'PENDING';",
        },
        {
            "q": "Show approved claims in last month.",
            "a": (
                "SELECT * FROM claims "
                "WHERE status = 'APPROVED' "
                "AND claim_date >= TRUNC(ADD_MONTHS(SYSDATE, -1), 'MM');"
            ),
        },
    ]

    sql_gen = SQLGenerator(few_shots)
    sample_question = "Give me report for pending approvals for last month"
    sql_gen.generate_query(sample_question)
