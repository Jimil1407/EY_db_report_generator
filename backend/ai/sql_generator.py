from .gemini_client import GeminiClient
from .schema_manager import load_schema, format_schema
from .prompt_builder import build_gemini_prompt
import re

class SQLGenerator:
    def __init__(self, few_shots: list, api_key: str):
        # Load fixed schema once and format for prompt context
        schema_json = load_schema()  # returns JSON dict from file
        self.schema_context = format_schema(schema_json)  # formatted schema string
        self.schema_json = schema_json  # Store for validation
        self.few_shots = few_shots
        self.gemini_client = GeminiClient(api_key=api_key)
        
        # Extract valid column names from schema for validation
        self.valid_columns = set()
        if isinstance(schema_json, dict) and "columns" in schema_json:
            for col in schema_json.get("columns", []):
                if isinstance(col, dict):
                    name = col.get("name")
                    if name:
                        self.valid_columns.add(name.upper())
                elif isinstance(col, str):
                    self.valid_columns.add(col.upper())
        
        # Get table name
        self.table_name = schema_json.get("tableName", "").upper() if isinstance(schema_json, dict) else ""

    def generate_query(self, user_question: str) -> str:
        # Build full combined prompt using the shared prompt builder
        prompt = build_gemini_prompt(
            user_question=user_question,
            few_shots=self.few_shots,
            schema_context=self.schema_context,
        )

        # Call Gemini API to generate SQL
        raw_output = self.gemini_client.generate_sql(prompt)
        
        # Sanitize: strip markdown fences, language tags, and leading labels
        sql = self._clean_sql_output(raw_output)
        
        # Validate SQL completeness
        completeness_error = self._validate_sql_completeness(sql)
        if completeness_error:
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
        
        # Must contain table name ASRIT_PATIENT
        if "ASRIT_PATIENT" not in sql_upper:
            return "SQL query must include FROM ASRIT_PATIENT"
        
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
        cleaned = re.sub(r"^(SQL\\s*QUERY\\s*:|SQL\\s*:)", "", cleaned, flags=re.IGNORECASE).strip()
        # If multiple lines, take the first line that starts with SELECT
        lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
        for ln in lines:
            if ln.upper().startswith("SELECT"):
                return ln.rstrip(";") + ";"
        # Fallback: try to extract the first SELECT ... ; span
        m = re.search(r"(SELECT[\\s\\S]+?;)", cleaned, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
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
