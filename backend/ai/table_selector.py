import json
import logging
from pathlib import Path
from typing import List
from .gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class TableSelector:
    def __init__(self, api_key: str):
        self.gemini_client = GeminiClient(api_key=api_key)
        self.table_descriptions = self._load_table_descriptions()
    
    def _load_table_descriptions(self) -> List[dict]:
        try:
            descriptions_path = Path(__file__).parent / "schema" / "table_descriptions.json"
            with open(descriptions_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading table descriptions: {e}")
            raise
    
    def select_tables(self, user_question: str) -> List[str]:
        try:
            prompt = self._build_selection_prompt(user_question)
            
            logger.info(f"Selecting tables for query: {user_question[:100]}...")
            raw_output = self.gemini_client.generate_sql(prompt)
            
            selected_tables = self._parse_table_selection(raw_output)
            
            valid_tables = self._validate_tables(selected_tables)
            
            logger.info(f"Selected tables: {valid_tables}")
            return valid_tables
            
        except Exception as e:
            logger.error(f"Error selecting tables: {e}")
            logger.warning("Falling back to all tables due to selection error")
            return [table["tableName"] for table in self.table_descriptions]
    
    def _build_selection_prompt(self, user_question: str) -> str:
        tables_text = "\n".join([
            f"- {table['tableName']}: {table['description']}"
            for table in self.table_descriptions
        ])
        
        prompt = f"""You are a database table selection assistant. Your task is to analyze a user's natural language query and identify which database tables are needed to answer it.

AVAILABLE TABLES:
{tables_text}

INSTRUCTIONS:
1. Analyze the user's question carefully
2. Identify which tables contain the data needed to answer the question
3. Return ONLY a JSON array of table names (e.g., ["ASRIT_PATIENT", "ASRIT_CASE"])
4. Include only tables that are directly relevant to the query
5. If the query requires joining data from multiple tables, include all relevant tables
6. Return the JSON array without any additional text or explanation

USER QUESTION: {user_question}

Return the JSON array of table names:"""
        
        return prompt
    
    def _parse_table_selection(self, raw_output: str) -> List[str]:
        if not raw_output:
            return []
        
        cleaned = raw_output.strip()
        
        import re
        json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(1)
        
        json_match = re.search(r'(\[.*?\])', cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(1)
        
        try:
            selected_tables = json.loads(cleaned)
            if isinstance(selected_tables, list):
                return [str(table).upper().strip() for table in selected_tables if table]
            elif isinstance(selected_tables, str):
                return [selected_tables.upper().strip()]
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON, attempting to extract table names from: {raw_output}")
            table_pattern = r'\b(ASRIT|ASRIM)_[A-Z_]+'
            matches = [match.group(0) for match in re.finditer(table_pattern, cleaned.upper())]
            if matches:
                return list(set(matches))
        
        return []
    
    def _validate_tables(self, table_names: List[str]) -> List[str]:
        valid_table_names = {table["tableName"] for table in self.table_descriptions}
        validated = [name for name in table_names if name in valid_table_names]
        
        if len(validated) != len(table_names):
            invalid = set(table_names) - set(validated)
            logger.warning(f"Invalid table names filtered out: {invalid}")
        
        return validated

